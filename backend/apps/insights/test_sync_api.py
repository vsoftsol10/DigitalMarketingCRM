from datetime import date, timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .models import (
    InsightsAccountSnapshot,
    InsightsContentSnapshotItem,
    InsightsMediaSnapshot,
    InsightsSnapshotSlot,
    InsightsSyncState,
    InsightsSyncStatus,
    InsightsSyncWork,
    InsightsSyncWorkStage,
    InsightsSyncWorkStatus,
)
from .sync_service import request_insights_sync


class InsightsSyncOrchestrationAPITests(APITestCase):
    since = date(2026, 8, 28)
    until = date(2026, 9, 26)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="insights-sync-owner@example.com",
            first_name="Insights Sync Owner",
            password="password",
        )
        self.other_owner = User.objects.create_user(
            email="insights-sync-other@example.com",
            first_name="Other Insights Owner",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-SYNC-API",
            name="Insights Sync Organization",
            slug="insights-sync-organization",
            industry="Retail",
            created_by=self.owner,
        )
        self.other_organization = Organization.objects.create(
            organization_id="ORG-SYNC-OTHER",
            name="Other Insights Sync Organization",
            slug="other-insights-sync-organization",
            industry="Retail",
            created_by=self.other_owner,
        )
        self.account = self.make_account(self.organization, "provider-account-1")
        self.other_account = self.make_account(self.other_organization, "provider-account-2")
        self.url = reverse(
            "insights-account-sync",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": self.account.id,
            },
        )
        self.payload = {
            "since": self.since.isoformat(),
            "until": self.until.isoformat(),
            "platform": SocialPlatform.INSTAGRAM,
        }
        self.client.force_authenticate(self.owner)

    @staticmethod
    def make_account(organization, provider_id, **overrides):
        values = {
            "organization": organization,
            "platform": SocialPlatform.INSTAGRAM,
            "platform_account_id": provider_id,
            "username": "sync-account",
            "status": SocialAccountStatus.CONNECTED,
            "is_valid": True,
        }
        values.update(overrides)
        return SocialAccount.objects.create(**values)

    def make_state(self, status, **overrides):
        values = {
            "social_account": self.account,
            "since": self.since,
            "until": self.until,
            "api_version": "v26.0",
            "status": status,
            "account_status": status,
            "items_discovered": 5,
            "items_processed": 3,
            "items_total": 5,
            "provider_cursor": "private-provider-cursor",
            "checkpoint": {
                "private": "checkpoint-data",
                "automatic_continuations": 3,
            },
        }
        values.update(overrides)
        return InsightsSyncState.objects.create(**values)

    def assert_safe_response(self, response, state):
        self.assertEqual(response.data["success"], True)
        data = response.data["data"]
        self.assertEqual(data["organization_id"], self.organization.organization_id)
        self.assertEqual(data["social_account_id"], str(self.account.id))
        self.assertEqual(data["platform"], SocialPlatform.INSTAGRAM)
        self.assertEqual(data["since"], self.since.isoformat())
        self.assertEqual(data["until"], self.until.isoformat())
        self.assertEqual(data["sync_state_id"], str(state.id))
        self.assertEqual(data["status"], state.status)
        self.assertEqual(data["account_status"], state.account_status)
        self.assertEqual(
            data["progress"],
            {
                "discovered": state.items_discovered,
                "processed": state.items_processed,
                "total": state.items_total,
            },
        )
        for field in ("requested_at", "started_at", "completed_at", "already_active"):
            self.assertIn(field, data)
        serialized = str(response.data).lower()
        for forbidden in (
            "task_id",
            "access_token",
            "credential",
            "provider_cursor",
            "checkpoint",
            "private-provider-cursor",
            "checkpoint-data",
            "traceback",
        ):
            self.assertNotIn(forbidden, serialized)

    def create_attempt(self, *, since=None, until=None):
        result = request_insights_sync(
            social_account_id=self.account.id,
            since=since or self.since,
            until=until or self.until,
        )
        return InsightsSyncState.objects.get(id=result["sync_state_id"])

    def finish_stage(self, state, stage, status):
        from .sync_service import _finish_claimed_stage, claim_stage_work

        work = InsightsSyncWork.objects.get(sync_state=state, stage=stage)
        work.status = InsightsSyncWorkStatus.DISPATCHED
        work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(work_id=work.id, generation=work.generation)
        self.assertIsNotNone(claim)
        return _finish_claimed_stage(claim, status=status, state_fields={})

    def test_successful_account_and_content_stages_publish_independently(self):
        previous = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
        )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=30,
            published_account_sync_state=previous,
            published_content_sync_state=previous,
        )
        attempt = self.create_attempt()

        self.finish_stage(attempt, InsightsSyncWorkStage.ACCOUNT, InsightsSyncStatus.COMPLETE)
        slot.refresh_from_db()
        self.assertEqual(slot.published_account_sync_state_id, attempt.id)
        self.assertEqual(slot.published_content_sync_state_id, previous.id)
        self.assertEqual(slot.active_sync_state_id, attempt.id)
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.account_completed_at)

        self.finish_stage(attempt, InsightsSyncWorkStage.CONTENT, InsightsSyncStatus.COMPLETE)
        slot.refresh_from_db()
        attempt.refresh_from_db()
        self.assertEqual(slot.published_account_sync_state_id, attempt.id)
        self.assertEqual(slot.published_content_sync_state_id, attempt.id)
        self.assertIsNone(slot.active_sync_state_id)
        self.assertEqual(attempt.status, InsightsSyncStatus.COMPLETE)
        self.assertIsNotNone(attempt.content_completed_at)

    def test_failed_and_partial_stages_do_not_replace_published_pointers(self):
        previous = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
        )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=30,
            published_account_sync_state=previous,
            published_content_sync_state=previous,
        )
        attempt = self.create_attempt()

        self.finish_stage(attempt, InsightsSyncWorkStage.ACCOUNT, InsightsSyncStatus.PARTIAL)
        slot.refresh_from_db()
        self.assertEqual(slot.published_account_sync_state_id, previous.id)
        self.assertEqual(slot.published_content_sync_state_id, previous.id)
        self.assertEqual(slot.active_sync_state_id, attempt.id)

        self.finish_stage(attempt, InsightsSyncWorkStage.CONTENT, InsightsSyncStatus.FAILED)
        slot.refresh_from_db()
        self.assertEqual(slot.published_account_sync_state_id, previous.id)
        self.assertEqual(slot.published_content_sync_state_id, previous.id)
        self.assertIsNone(slot.active_sync_state_id)

    def test_account_success_content_failure_publishes_only_account(self):
        previous = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
        )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=30,
            published_account_sync_state=previous,
            published_content_sync_state=previous,
        )
        attempt = self.create_attempt()
        self.finish_stage(attempt, InsightsSyncWorkStage.ACCOUNT, InsightsSyncStatus.COMPLETE)
        self.finish_stage(attempt, InsightsSyncWorkStage.CONTENT, InsightsSyncStatus.FAILED)
        slot.refresh_from_db()
        self.assertEqual(slot.published_account_sync_state_id, attempt.id)
        self.assertEqual(slot.published_content_sync_state_id, previous.id)
        self.assertIsNone(slot.active_sync_state_id)

    def test_content_success_account_failure_publishes_only_content(self):
        previous = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
        )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=30,
            published_account_sync_state=previous,
            published_content_sync_state=previous,
        )
        attempt = self.create_attempt()
        self.finish_stage(attempt, InsightsSyncWorkStage.CONTENT, InsightsSyncStatus.COMPLETE)
        self.finish_stage(attempt, InsightsSyncWorkStage.ACCOUNT, InsightsSyncStatus.FAILED)
        slot.refresh_from_db()
        self.assertEqual(slot.published_account_sync_state_id, previous.id)
        self.assertEqual(slot.published_content_sync_state_id, attempt.id)
        self.assertIsNone(slot.active_sync_state_id)

    def test_same_duration_active_attempt_blocks_a_second_attempt(self):
        first = self.create_attempt()
        other_since = self.since - timedelta(days=7)
        result = request_insights_sync(
            social_account_id=self.account.id,
            since=other_since,
            until=other_since + timedelta(days=29),
        )
        self.assertEqual(result["sync_state_id"], str(first.id))
        self.assertTrue(result["already_active"])
        self.assertEqual(InsightsSyncState.objects.filter(social_account=self.account).count(), 1)

    def test_account_snapshot_is_linked_to_new_attempt_without_mutating_legacy_snapshot(self):
        legacy = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={"followers": {"value": 10, "availability": "available"}},
            fetched_at=timezone.now() - timedelta(days=1),
        )
        attempt = self.create_attempt()
        from .sync_service import _save_account_snapshot

        completion = timezone.now()
        attempt.account_completed_at = completion
        _save_account_snapshot(
            account=self.account,
            sync_state=attempt,
            since=self.since,
            until=self.until,
            metrics={"followers": {"value": 11, "availability": "available"}},
            follower_growth={},
            profile={},
            api_version=attempt.api_version,
        )
        versioned = InsightsAccountSnapshot.objects.get(sync_state=attempt)
        legacy.refresh_from_db()
        self.assertEqual(versioned.metrics["followers"]["value"], 11)
        self.assertEqual(versioned.fetched_at, completion)
        self.assertEqual(legacy.metrics["followers"]["value"], 10)

    def test_content_metrics_are_stored_per_attempt_while_legacy_media_row_stays_mutable(self):
        from .sync_service import _persist_media_page, _store_media_metrics

        def persist(attempt, reach):
            _persist_media_page(
                state=attempt,
                account=self.account,
                page={"data": [{
                    "id": "versioned-instagram-post",
                    "media_type": "IMAGE",
                    "caption": "Versioned caption",
                    "permalink": "https://instagram.example.test/post/1",
                    "timestamp": "2026-09-15T12:00:00+0000",
                }]},
                since=self.since,
                until=self.until,
            )
            _store_media_metrics(
                account=self.account,
                media_id="versioned-instagram-post",
                metrics={"reach": {"value": reach, "availability": "available"}},
                sync_state=attempt,
            )

        first = self.create_attempt()
        persist(first, 500)
        self.finish_stage(first, InsightsSyncWorkStage.CONTENT, InsightsSyncStatus.COMPLETE)
        self.finish_stage(first, InsightsSyncWorkStage.ACCOUNT, InsightsSyncStatus.COMPLETE)

        second = self.create_attempt()
        persist(second, 700)
        first_item = InsightsContentSnapshotItem.objects.get(
            sync_state=first,
            provider_media_id="versioned-instagram-post",
        )
        second_item = InsightsContentSnapshotItem.objects.get(
            sync_state=second,
            provider_media_id="versioned-instagram-post",
        )
        mutable_media = InsightsMediaSnapshot.objects.get(
            social_account=self.account,
            provider_media_id="versioned-instagram-post",
        )
        self.assertEqual(first_item.metrics["reach"]["value"], 500)
        self.assertEqual(second_item.metrics["reach"]["value"], 700)
        self.assertEqual(mutable_media.metrics["reach"]["value"], 700)

    def test_new_request_queues_existing_sync_service_once_and_returns_safe_state(self):
        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            patch("apps.insights.orchestration.request_insights_sync", wraps=request_insights_sync) as sync_service,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(InsightsSyncState.objects.count(), 1)
        state = InsightsSyncState.objects.get()
        self.assertEqual(state.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(state.account_status, InsightsSyncStatus.QUEUED)
        self.assertEqual(sync_service.call_count, 1)
        dispatch.assert_called_once()
        self.assert_safe_response(response, state)
        self.assertFalse(response.data["data"]["already_active"])

    def test_existing_queued_or_syncing_state_is_reused_without_dispatch(self):
        for existing_status in (InsightsSyncStatus.QUEUED, InsightsSyncStatus.SYNCING):
            with self.subTest(status=existing_status):
                state = self.make_state(existing_status)
                with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch:
                    response = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.data["data"]["already_active"], True)
                self.assert_safe_response(response, state)
                dispatch.assert_not_called()
                state.delete()

    def test_explicit_sync_creates_new_attempt_after_complete_state(self):
        completed_at = timezone.now()
        state = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            completed_at=completed_at,
            items_discovered=5,
            items_processed=5,
            items_total=5,
        )
        with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch:
            response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 202)
        new_state = InsightsSyncState.objects.exclude(id=state.id).get()
        self.assert_safe_response(response, new_state)
        self.assertEqual(response.data["data"]["already_active"], False)
        dispatch.assert_not_called()
        state.refresh_from_db()
        self.assertEqual(state.status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(state.completed_at, completed_at)
        self.assertEqual(state.items_processed, 5)
        self.assertEqual(new_state.status, InsightsSyncStatus.QUEUED)

    def test_complete_force_refresh_creates_new_attempt_and_preserves_published_version(self):
        state = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            completed_at=timezone.now(),
            items_discovered=5,
            items_processed=5,
            items_total=5,
        )
        for stage in (InsightsSyncWorkStage.ACCOUNT, InsightsSyncWorkStage.CONTENT):
            InsightsSyncWork.objects.create(
                sync_state=state,
                stage=stage,
                generation=1,
                status=InsightsSyncWorkStatus.TERMINAL,
            )
        account_snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={"followers": {"value": 17, "availability": "available"}},
            fetched_at=timezone.now(),
        )
        media_snapshot = InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="saved-media",
            api_version="v26.0",
            metrics={"reach": {"value": 12, "availability": "available"}},
            fetched_at=timezone.now(),
        )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=30,
            published_account_sync_state=state,
            published_content_sync_state=state,
        )

        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                self.url,
                {**self.payload, "force_refresh": True},
                format="json",
            )

        state.refresh_from_db()
        account_snapshot.refresh_from_db()
        media_snapshot.refresh_from_db()
        new_state = InsightsSyncState.objects.exclude(id=state.id).get()
        work_rows = list(InsightsSyncWork.objects.filter(sync_state=new_state).order_by("stage"))
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["data"]["sync_state_id"], str(new_state.id))
        self.assertFalse(response.data["data"]["already_active"])
        self.assertEqual(state.status, InsightsSyncStatus.COMPLETE)
        self.assertEqual((state.items_discovered, state.items_processed, state.items_total), (5, 5, 5))
        self.assertEqual(new_state.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(len(work_rows), 2)
        self.assertEqual({row.generation for row in work_rows}, {1})
        self.assertEqual({row.status for row in work_rows}, {InsightsSyncWorkStatus.PENDING})
        self.assertEqual(InsightsSyncWork.objects.filter(sync_state=state).count(), 2)
        self.assertEqual(account_snapshot.metrics["followers"]["value"], 17)
        self.assertEqual(media_snapshot.metrics["reach"]["value"], 12)
        slot.refresh_from_db()
        self.assertEqual(slot.active_sync_state_id, new_state.id)
        self.assertEqual(slot.published_account_sync_state_id, state.id)
        self.assertEqual(slot.published_content_sync_state_id, state.id)
        dispatch.assert_called_once()
        self.assert_safe_response(response, new_state)

    def test_facebook_complete_force_refresh_creates_new_attempt_and_preserves_snapshots(self):
        account = self.make_account(
            self.organization,
            "facebook-provider-page",
            platform=SocialPlatform.FACEBOOK,
        )
        url = reverse(
            "insights-account-sync",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": account.id,
            },
        )
        state = InsightsSyncState.objects.create(
            social_account=account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            items_discovered=84,
            items_processed=84,
            items_total=84,
            checkpoint={"discovered_post_ids": ["provider-post"]},
        )
        for stage in (InsightsSyncWorkStage.ACCOUNT, InsightsSyncWorkStage.CONTENT):
            InsightsSyncWork.objects.create(
                sync_state=state,
                stage=stage,
                generation=4,
                status=InsightsSyncWorkStatus.TERMINAL,
            )
        account_snapshot = InsightsAccountSnapshot.objects.create(
            social_account=account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={"followers": {"value": 84, "availability": "available"}},
            fetched_at=timezone.now(),
        )
        media_snapshot = InsightsMediaSnapshot.objects.create(
            social_account=account,
            provider_media_id="provider-post",
            api_version="v26.0",
            caption="Existing post metadata",
            metrics={"reach": {"value": 12, "availability": "available"}},
            fetched_at=timezone.now(),
        )
        account_snapshot_before = (account_snapshot.metrics.copy(), account_snapshot.fetched_at)
        media_snapshot_before = (
            media_snapshot.caption,
            media_snapshot.metrics.copy(),
            media_snapshot.fetched_at,
        )

        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                url,
                {
                    "since": self.since.isoformat(),
                    "until": self.until.isoformat(),
                    "platform": SocialPlatform.FACEBOOK,
                    "force_refresh": True,
                },
                format="json",
            )

        state.refresh_from_db()
        account_snapshot.refresh_from_db()
        media_snapshot.refresh_from_db()
        new_state = InsightsSyncState.objects.exclude(id=state.id).get()
        work_rows = list(InsightsSyncWork.objects.filter(sync_state=new_state))
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["data"]["sync_state_id"], str(new_state.id))
        self.assertEqual(state.social_account_id, account.id)
        self.assertEqual((state.since, state.until), (self.since, self.until))
        self.assertEqual(state.status, InsightsSyncStatus.COMPLETE)
        self.assertEqual((state.items_discovered, state.items_processed, state.items_total), (84, 84, 84))
        self.assertEqual(new_state.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(len(work_rows), 2)
        self.assertEqual({work.generation for work in work_rows}, {1})
        self.assertEqual({work.status for work in work_rows}, {InsightsSyncWorkStatus.PENDING})
        self.assertEqual(
            (account_snapshot.metrics, account_snapshot.fetched_at),
            account_snapshot_before,
        )
        self.assertEqual(
            (media_snapshot.caption, media_snapshot.metrics, media_snapshot.fetched_at),
            media_snapshot_before,
        )
        self.assertEqual(
            InsightsMediaSnapshot.objects.filter(
                social_account=account,
                provider_media_id="provider-post",
            ).count(),
            1,
        )
        dispatch.assert_called_once()

    def test_facebook_terminal_partial_refresh_creates_new_attempt_without_mutating_old_state(self):
        account = self.make_account(
            self.organization,
            "facebook-terminal-partial-page",
            platform=SocialPlatform.FACEBOOK,
        )
        url = reverse(
            "insights-account-sync",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": account.id,
            },
        )
        state = InsightsSyncState.objects.create(
            social_account=account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.PARTIAL,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.PARTIAL,
            items_discovered=84,
            items_processed=84,
            items_total=84,
            checkpoint={},
            provider_cursor="",
        )
        account_work = InsightsSyncWork.objects.create(
            sync_state=state,
            stage=InsightsSyncWorkStage.ACCOUNT,
            generation=8,
            status=InsightsSyncWorkStatus.TERMINAL,
        )
        content_work = InsightsSyncWork.objects.create(
            sync_state=state,
            stage=InsightsSyncWorkStage.CONTENT,
            generation=8,
            status=InsightsSyncWorkStatus.TERMINAL,
        )
        media_snapshot = InsightsMediaSnapshot.objects.create(
            social_account=account,
            provider_media_id="stable-provider-post",
            api_version="v26.0",
            caption="Persisted post",
            metrics={
                "reach": {"value": 12, "availability": "available"},
                "reactions": {"value": 4, "availability": "available"},
            },
            fetched_at=timezone.now(),
        )
        original_metrics = media_snapshot.metrics.copy()
        original_fetched_at = media_snapshot.fetched_at

        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                url,
                {
                    "since": self.since.isoformat(),
                    "until": self.until.isoformat(),
                    "platform": SocialPlatform.FACEBOOK,
                    "force_refresh": True,
                },
                format="json",
            )

        state.refresh_from_db()
        account_work.refresh_from_db()
        content_work.refresh_from_db()
        new_state = InsightsSyncState.objects.exclude(id=state.id).get()
        self.assertEqual(response.status_code, 202)
        self.assertEqual(new_state.status, InsightsSyncStatus.QUEUED)
        self.assertEqual((new_state.items_discovered, new_state.items_processed, new_state.items_total), (0, 0, None))
        self.assertEqual(state.status, InsightsSyncStatus.PARTIAL)
        self.assertEqual((state.items_discovered, state.items_processed, state.items_total), (84, 84, 84))
        self.assertEqual(account_work.generation, 8)
        self.assertEqual(content_work.generation, 8)
        self.assertEqual(account_work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(content_work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(
            InsightsMediaSnapshot.objects.filter(
                social_account=account,
                provider_media_id="stable-provider-post",
            ).count(),
            1,
        )
        media_snapshot.refresh_from_db()
        self.assertEqual(media_snapshot.metrics, original_metrics)
        self.assertEqual(media_snapshot.fetched_at, original_fetched_at)
        dispatch.assert_called_once()
        self.assertEqual(InsightsSyncState.objects.filter(social_account=account).count(), 2)

    def test_force_refresh_does_not_duplicate_queued_or_syncing_work(self):
        for existing_status in (InsightsSyncStatus.QUEUED, InsightsSyncStatus.SYNCING):
            with self.subTest(status=existing_status):
                state = self.make_state(existing_status)
                for stage in (InsightsSyncWorkStage.ACCOUNT, InsightsSyncWorkStage.CONTENT):
                    InsightsSyncWork.objects.create(
                        sync_state=state,
                        stage=stage,
                        generation=1,
                        status=InsightsSyncWorkStatus.DISPATCHED,
                    )
                with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch:
                    response = self.client.post(
                        self.url,
                        {**self.payload, "force_refresh": True},
                        format="json",
                    )
                self.assertEqual(response.status_code, 202)
                self.assertTrue(response.data["data"]["already_active"])
                self.assertEqual(InsightsSyncState.objects.count(), 1)
                self.assertEqual(InsightsSyncWork.objects.filter(sync_state=state).count(), 2)
                self.assertEqual(
                    set(InsightsSyncWork.objects.filter(sync_state=state).values_list("generation", flat=True)),
                    {1},
                )
                dispatch.assert_not_called()
                state.delete()

    def test_explicit_sync_after_partial_or_failed_creates_fresh_attempt(self):
        partial = self.make_state(InsightsSyncStatus.PARTIAL)
        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                self.url, {**self.payload, "force_refresh": True}, format="json",
            )
        partial.refresh_from_db()
        self.assertEqual(response.status_code, 202)
        partial_retry = InsightsSyncState.objects.exclude(id=partial.id).get()
        self.assertEqual(partial.status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(partial.provider_cursor, "private-provider-cursor")
        self.assertEqual(
            partial.checkpoint,
            {"private": "checkpoint-data", "automatic_continuations": 3},
        )
        self.assertEqual(partial.items_processed, 3)
        self.assertEqual(partial_retry.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(partial_retry.checkpoint, {})
        self.assertEqual(partial_retry.items_processed, 0)
        dispatch.assert_called_once()

        partial_retry.status = InsightsSyncStatus.FAILED
        partial_retry.account_status = InsightsSyncStatus.FAILED
        partial_retry.content_status = InsightsSyncStatus.FAILED
        partial_retry.save(update_fields=("status", "account_status", "content_status", "updated_at"))
        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                self.url, {**self.payload, "force_refresh": True}, format="json",
            )
        partial_retry.refresh_from_db()
        failed_retry = InsightsSyncState.objects.exclude(id__in=(partial.id, partial_retry.id)).get()
        self.assertEqual(response.status_code, 202)
        self.assertEqual(partial_retry.status, InsightsSyncStatus.FAILED)
        self.assertEqual(partial_retry.checkpoint, {})
        self.assertEqual(failed_retry.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(failed_retry.checkpoint, {})
        dispatch.assert_called_once()

    def test_invalid_ranges_are_rejected_without_creating_state(self):
        today = timezone.localdate()
        bad_payloads = (
            {"until": self.until.isoformat(), "platform": SocialPlatform.INSTAGRAM},
            {"since": self.since.isoformat(), "platform": SocialPlatform.INSTAGRAM},
            {"since": self.since.isoformat(), "until": self.until.isoformat()},
            {"since": "not-a-date", "until": self.until.isoformat(), "platform": SocialPlatform.INSTAGRAM},
            {**self.payload, "since": self.until.isoformat(), "until": self.since.isoformat()},
            {**self.payload, "until": (today + timedelta(days=1)).isoformat()},
            {**self.payload, "since": (today - timedelta(days=90)).isoformat(), "until": today.isoformat()},
        )
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertFalse(InsightsSyncState.objects.exists())

    def test_force_refresh_must_be_a_boolean(self):
        response = self.client.post(
            self.url,
            {**self.payload, "force_refresh": "sometimes"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(InsightsSyncState.objects.exists())

    def test_platform_mismatch_is_rejected_and_facebook_sync_is_accepted(self):
        mismatch = self.client.post(
            self.url,
            {**self.payload, "platform": SocialPlatform.FACEBOOK},
            format="json",
        )
        facebook = self.make_account(
            self.organization,
            "facebook-provider-account",
            platform=SocialPlatform.FACEBOOK,
        )
        facebook_url = reverse(
            "insights-account-sync",
            kwargs={"organization_id": self.organization.organization_id, "social_account_id": facebook.id},
        )
        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            accepted = self.client.post(
                facebook_url,
                {**self.payload, "platform": SocialPlatform.FACEBOOK},
                format="json",
            )
        self.assertEqual(mismatch.status_code, 400)
        self.assertEqual(accepted.status_code, 202)
        self.assertEqual(accepted.data["data"]["platform"], SocialPlatform.FACEBOOK)
        state = InsightsSyncState.objects.get(social_account=facebook)
        self.assertEqual(state.api_version, "v26.0")
        self.assertEqual(state.account_status, InsightsSyncStatus.QUEUED)
        self.assertEqual(state.content_status, InsightsSyncStatus.QUEUED)
        self.assertEqual(InsightsSyncWork.objects.filter(sync_state=state).count(), 2)
        dispatch.assert_called_once()

    def test_inaccessible_or_unavailable_accounts_are_not_found(self):
        foreign_url = reverse(
            "insights-account-sync",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": self.other_account.id,
            },
        )
        self.assertEqual(self.client.post(foreign_url, self.payload, format="json").status_code, 404)

        self.client.force_authenticate(self.other_owner)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 404)
        self.client.force_authenticate(self.owner)

        for name, changes in (
            ("deleted", {"is_deleted": True}),
            ("disconnected", {"status": SocialAccountStatus.DISCONNECTED}),
            ("invalid", {"is_valid": False}),
        ):
            account = self.make_account(self.organization, f"provider-{name}", **changes)
            url = reverse(
                "insights-account-sync",
                kwargs={"organization_id": self.organization.organization_id, "social_account_id": account.id},
            )
            self.assertEqual(self.client.post(url, self.payload, format="json").status_code, 404)
        self.assertFalse(InsightsSyncState.objects.exists())

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 401)

    def test_repeated_active_request_protects_against_duplicate_dispatch(self):
        with (
            patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch,
            self.captureOnCommitCallbacks(execute=True),
        ):
            first = self.client.post(self.url, self.payload, format="json")
        second = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(first.data["data"]["sync_state_id"], second.data["data"]["sync_state_id"])
        self.assertTrue(second.data["data"]["already_active"])
        self.assertEqual(InsightsSyncState.objects.count(), 1)
        dispatch.assert_called_once()
