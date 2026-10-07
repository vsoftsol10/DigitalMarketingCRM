from datetime import date, datetime, timedelta, timezone as datetime_timezone
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
)


class InsightsSnapshotReadAPITests(APITestCase):
    since = date(2026, 8, 28)
    until = date(2026, 9, 26)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="snapshot-api-owner@example.com",
            first_name="Snapshot API Owner",
            password="password",
        )
        self.other_owner = User.objects.create_user(
            email="snapshot-api-other@example.com",
            first_name="Other Owner",
            password="password",
        )
        self.organization = self.make_organization("ORG-SNAPSHOT-API", self.owner)
        self.other_organization = self.make_organization("ORG-SNAPSHOT-OTHER", self.other_owner)
        self.account = self.make_account(self.organization, provider_id="same-provider-id")
        self.other_account = self.make_account(self.other_organization, provider_id="same-provider-id")
        self.account_url = reverse(
            "insights-account-snapshot",
            kwargs={"organization_id": self.organization.organization_id, "social_account_id": self.account.id},
        )
        self.content_url = reverse(
            "insights-account-snapshot-content",
            kwargs={"organization_id": self.organization.organization_id, "social_account_id": self.account.id},
        )
        self.params = {
            "since": self.since.isoformat(),
            "until": self.until.isoformat(),
            "platform": SocialPlatform.INSTAGRAM,
        }
        self.client.force_authenticate(self.owner)

    @staticmethod
    def make_organization(org_id, owner):
        return Organization.objects.create(
            organization_id=org_id,
            name=org_id,
            slug=org_id.lower(),
            industry="Retail",
            created_by=owner,
        )

    @staticmethod
    def make_account(organization, *, provider_id, **overrides):
        values = {
            "organization": organization,
            "platform": SocialPlatform.INSTAGRAM,
            "platform_account_id": provider_id,
            "username": "snapshot-user",
            "status": SocialAccountStatus.CONNECTED,
            "is_valid": True,
        }
        values.update(overrides)
        return SocialAccount.objects.create(**values)

    def make_snapshot(self, *, since=None, until=None, api_version="v26.0", fetched_at=None):
        return InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=since or self.since,
            until=until or self.until,
            api_version=api_version,
            metrics={
                "followers": {"value": 0, "availability": "available", "reason": "", "period": "current"},
                "reach": {"value": None, "availability": "not_supported", "reason": "metric_deprecated"},
            },
            follower_growth={"availability": "unavailable", "reason": "metric_not_supported", "points": []},
            fetched_at=fetched_at or timezone.now(),
        )

    def make_state(self, status, *, since=None, until=None, account_status=None, content_status=None, **overrides):
        return InsightsSyncState.objects.create(
            social_account=self.account,
            since=since or self.since,
            until=until or self.until,
            api_version="v26.0",
            status=status,
            account_status=account_status or InsightsSyncStatus.COMPLETE,
            content_status=content_status or status,
            items_discovered=2,
            items_processed=1 if status in {InsightsSyncStatus.SYNCING, InsightsSyncStatus.PARTIAL} else 0,
            items_total=2,
            provider_cursor="must-not-leak-provider-cursor",
            checkpoint={"token": "must-not-leak-checkpoint"},
            error_code="safe_error_code" if status in {InsightsSyncStatus.PARTIAL, InsightsSyncStatus.FAILED} else "",
            error_reason="safe_reason" if status in {InsightsSyncStatus.PARTIAL, InsightsSyncStatus.FAILED} else "",
            **overrides,
        )

    def make_published_version(
        self,
        *,
        duration_days=30,
        since=None,
        until=None,
        metrics_value=0,
        content=True,
        account=True,
        account_completed_at=None,
        content_completed_at=None,
    ):
        since = since or self.since
        until = until or self.until
        state = self.make_state(
            InsightsSyncStatus.COMPLETE,
            since=since,
            until=until,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            account_completed_at=account_completed_at or timezone.now(),
            content_completed_at=content_completed_at or timezone.now(),
        )
        snapshot = None
        if account:
            snapshot = InsightsAccountSnapshot.objects.create(
                social_account=self.account,
                since=since,
                until=until,
                api_version=state.api_version,
                sync_state=state,
                metrics={
                    "followers": {"value": metrics_value, "availability": "available", "reason": ""},
                },
                follower_growth={"availability": "unavailable", "reason": "metric_not_supported", "points": []},
                fetched_at=timezone.now(),
            )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=duration_days,
            published_account_sync_state=state if account else None,
            published_content_sync_state=state if content else None,
        )
        return state, snapshot, slot

    def make_content_item(self, state, provider_media_id, *, published_at=None, fetched_at=None, value=0):
        return InsightsContentSnapshotItem.objects.create(
            sync_state=state,
            provider_media_id=provider_media_id,
            media_type="IMAGE",
            caption=provider_media_id,
            permalink="",
            published_at=published_at or datetime(2026, 9, 10, tzinfo=datetime_timezone.utc),
            api_version=state.api_version,
            metrics={"likes": {"value": value, "availability": "available", "reason": ""}},
            fetched_at=fetched_at or timezone.now(),
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.account_url, self.params).status_code, 401)
        self.assertEqual(self.client.get(self.content_url, self.params).status_code, 401)

    def test_owner_and_exact_account_scope_are_enforced(self):
        foreign_url = reverse(
            "insights-account-snapshot",
            kwargs={"organization_id": self.organization.organization_id, "social_account_id": self.other_account.id},
        )
        self.assertEqual(self.client.get(foreign_url, self.params).status_code, 404)
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(self.client.get(self.account_url, self.params).status_code, 404)

    def test_disconnected_invalid_and_deleted_accounts_are_not_selectable(self):
        for name, changes in (
            ("disconnected", {"status": SocialAccountStatus.DISCONNECTED}),
            ("invalid", {"is_valid": False}),
            ("deleted", {"is_deleted": True}),
        ):
            account = self.make_account(
                self.organization,
                provider_id=f"provider-{name}",
                **changes,
            )
            url = reverse(
                "insights-account-snapshot",
                kwargs={"organization_id": self.organization.organization_id, "social_account_id": account.id},
            )
            self.assertEqual(self.client.get(url, self.params).status_code, 404)

    def test_required_filters_platform_and_date_validation(self):
        self.assertEqual(self.client.get(self.account_url).status_code, 400)
        mismatch = {**self.params, "platform": SocialPlatform.FACEBOOK}
        self.assertEqual(self.client.get(self.account_url, mismatch).status_code, 400)
        today = timezone.localdate()
        bad_ranges = (
            {"since": today.isoformat(), "until": (today - timedelta(days=1)).isoformat()},
            {"since": today.isoformat(), "until": (today + timedelta(days=1)).isoformat()},
            {"since": (today - timedelta(days=90)).isoformat(), "until": today.isoformat()},
        )
        for date_range in bad_ranges:
            self.assertEqual(
                self.client.get(self.account_url, {**self.params, **date_range}).status_code,
                400,
            )

    def test_exact_account_snapshot_selected_and_values_are_preserved(self):
        old = self.make_snapshot(
            since=self.since - timedelta(days=1),
            until=self.until - timedelta(days=1),
            fetched_at=timezone.now() - timedelta(days=2),
        )
        selected = self.make_snapshot()

        with patch("apps.insights.services.fetch_provider_insights") as provider_call:
            response = self.client.get(self.account_url, self.params)

        self.assertEqual(response.status_code, 200)
        payload = response.data["data"]
        self.assertEqual(payload["freshness"]["account_snapshot"]["fetched_at"], selected.fetched_at.isoformat())
        self.assertNotEqual(payload["freshness"]["account_snapshot"]["fetched_at"], old.fetched_at.isoformat())
        self.assertEqual(payload["account_overview"]["metrics"]["followers"]["value"], 0)
        self.assertEqual(payload["account_overview"]["metrics"]["reach"]["availability"], "not_supported")
        self.assertEqual(payload["account_overview"]["metrics"]["reach"]["reason"], "metric_deprecated")
        self.assertEqual(payload["follower_growth"]["reason"], "metric_not_supported")
        self.assertEqual(payload["freshness"]["account_snapshot"]["source"], "legacy")
        provider_call.assert_not_called()

    def test_facebook_account_snapshot_returns_persisted_aggregations_and_native_reach(self):
        account = self.make_account(
            self.organization,
            provider_id="facebook-page-for-snapshot",
            platform=SocialPlatform.FACEBOOK,
        )
        url = reverse(
            "insights-account-snapshot",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": account.id,
            },
        )
        metrics = {
            "followers": {
                "value": 123,
                "availability": "available",
                "source": "facebook",
                "provider_metric": "followers_count",
                "period": "current",
                "reason": "",
            },
            "engagement": {
                "value": 24,
                "availability": "available",
                "source": "facebook",
                "provider_metric": "page_post_engagements",
                "period": "week",
                "reason": "",
            },
            "views": {
                "value": 40,
                "availability": "available",
                "source": "facebook",
                "provider_metric": "page_media_view",
                "period": "week",
                "reason": "",
            },
            "reach": {
                "value": 9,
                "availability": "available",
                "source": "facebook",
                "provider_metric": "page_total_media_view_unique",
                "measurement": "unique_media_viewers",
                "period": "week",
                "reason": "",
            },
        }
        InsightsAccountSnapshot.objects.create(
            social_account=account,
            since=date(2026, 9, 8),
            until=date(2026, 10, 5),
            api_version="v26.0",
            metrics=metrics,
            follower_growth={"availability": "unavailable", "points": []},
            fetched_at=timezone.now(),
        )
        params = {
            "since": "2026-09-08",
            "until": "2026-10-05",
            "platform": SocialPlatform.FACEBOOK,
        }

        with patch("apps.insights.services.fetch_provider_insights") as provider_call:
            response = self.client.get(url, params)

        self.assertEqual(response.status_code, 200)
        returned = response.data["data"]["account_overview"]["metrics"]
        self.assertEqual(returned, metrics)
        self.assertEqual(returned["engagement"]["period"], "week")
        self.assertNotIn("aggregation", returned["engagement"])
        self.assertEqual(returned["views"]["period"], "week")
        self.assertNotIn("aggregation", returned["views"])
        self.assertEqual(returned["reach"]["period"], "week")
        provider_call.assert_not_called()

    def test_missing_snapshot_does_not_fallback_or_fabricate_metrics(self):
        response = self.client.get(self.account_url, self.params)
        overview = response.data["data"]["account_overview"]
        self.assertFalse(response.data["data"]["freshness"]["account_snapshot"]["exists"])
        self.assertEqual(overview["availability"], "not_ready")
        self.assertIsNone(overview["metrics"])
        self.assertIsNone(response.data["data"]["follower_growth"])
        sync = response.data["data"]["freshness"]["sync"]
        self.assertEqual(sync["status"], "never_synced")
        self.assertEqual(sync["account_status"], "never_synced")
        self.assertEqual(sync["content_status"], "never_synced")
        self.assertFalse(sync["more_content_available"])
        content_response = self.client.get(self.content_url, self.params)
        self.assertEqual(
            content_response.data["data"]["freshness"]["sync"]["content_status"],
            "never_synced",
        )

    def test_published_7d_account_version_is_independent_of_current_dates(self):
        saved_since, saved_until = date(2026, 9, 20), date(2026, 9, 26)
        completion = timezone.now() - timedelta(days=2)
        self.make_published_version(
            duration_days=7,
            since=saved_since,
            until=saved_until,
            metrics_value=707,
            account_completed_at=completion,
        )
        rolling_params = {
            "since": "2026-09-29",
            "until": "2026-10-05",
            "platform": SocialPlatform.INSTAGRAM,
        }

        response = self.client.get(self.account_url, rolling_params)
        data = response.data["data"]
        self.assertEqual(data["account_overview"]["metrics"]["followers"]["value"], 707)
        freshness = data["freshness"]["account_snapshot"]
        self.assertEqual(freshness["since"], saved_since.isoformat())
        self.assertEqual(freshness["until"], saved_until.isoformat())
        self.assertEqual(freshness["updated_at"], completion.isoformat())
        self.assertEqual(freshness["fetched_at"], completion.isoformat())

    def test_facebook_28d_and_instagram_30d_slots_are_selected_by_duration(self):
        facebook = self.make_account(
            self.organization,
            provider_id="facebook-28d",
            platform=SocialPlatform.FACEBOOK,
        )
        fb_url = reverse("insights-account-snapshot", kwargs={
            "organization_id": self.organization.organization_id,
            "social_account_id": facebook.id,
        })
        fb_state = InsightsSyncState.objects.create(
            social_account=facebook,
            since=date(2026, 9, 8),
            until=date(2026, 10, 5),
            api_version="v26.0",
            status=InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            account_completed_at=timezone.now(),
            content_completed_at=timezone.now(),
        )
        InsightsAccountSnapshot.objects.create(
            social_account=facebook,
            since=fb_state.since,
            until=fb_state.until,
            api_version=fb_state.api_version,
            sync_state=fb_state,
            metrics={"followers": {"value": 28, "availability": "available", "reason": ""}},
            fetched_at=timezone.now(),
        )
        InsightsSnapshotSlot.objects.create(
            social_account=facebook,
            duration_days=28,
            published_account_sync_state=fb_state,
        )

        fb_response = self.client.get(fb_url, {
            "since": "2026-09-08", "until": "2026-10-05", "platform": SocialPlatform.FACEBOOK,
        })
        ig_state, _, _ = self.make_published_version(
            duration_days=30,
            since=date(2026, 9, 6),
            until=date(2026, 10, 5),
            metrics_value=30,
            content=False,
        )
        ig_response = self.client.get(self.account_url, {
            "since": "2026-09-06", "until": "2026-10-05", "platform": SocialPlatform.INSTAGRAM,
        })

        self.assertEqual(fb_response.status_code, 200)
        self.assertEqual(fb_response.data["data"]["account_overview"]["metrics"]["followers"]["value"], 28)
        self.assertEqual(fb_response.data["data"]["freshness"]["account_snapshot"]["since"], fb_state.since.isoformat())
        self.assertEqual(ig_response.data["data"]["account_overview"]["metrics"]["followers"]["value"], 30)
        self.assertEqual(ig_response.data["data"]["freshness"]["sync"]["account_status"], "complete")

    def test_no_slot_or_unpublished_stage_returns_never_synced_without_legacy_media(self):
        InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="legacy-media",
            published_at=datetime(2026, 9, 10, tzinfo=datetime_timezone.utc),
            api_version="v26.0",
            metrics={"likes": {"value": 99, "availability": "available", "reason": ""}},
        )
        content = self.client.get(self.content_url, self.params).data["data"]
        self.assertEqual(content["freshness"]["sync"]["content_status"], "never_synced")
        self.assertEqual(content["content_performance"]["availability"], "unavailable")
        self.assertEqual(content["content_performance"]["results"], [])

        InsightsSnapshotSlot.objects.create(social_account=self.account, duration_days=30)
        account = self.client.get(self.account_url, self.params).data["data"]
        self.assertEqual(account["freshness"]["account_snapshot"]["status"], "never_synced")
        self.assertIsNone(account["account_overview"]["metrics"])

    def test_active_attempt_keeps_published_account_and_content_visible(self):
        state_a, _, slot = self.make_published_version(metrics_value=111)
        self.make_content_item(state_a, "published-a", value=111)
        state_b = self.make_state(
            InsightsSyncStatus.QUEUED,
            account_status=InsightsSyncStatus.QUEUED,
            content_status=InsightsSyncStatus.QUEUED,
        )
        slot.active_sync_state = state_b
        slot.save(update_fields=("active_sync_state", "updated_at"))

        account = self.client.get(self.account_url, self.params).data["data"]
        content = self.client.get(self.content_url, self.params).data["data"]
        self.assertEqual(account["account_overview"]["metrics"]["followers"]["value"], 111)
        self.assertEqual(content["content_performance"]["results"][0]["provider_media_id"], "published-a")
        self.assertEqual(content["freshness"]["sync"]["status"], InsightsSyncStatus.QUEUED)
        self.assertEqual(content["freshness"]["sync"]["content_status"], "complete")
        self.assertEqual(content["freshness"]["active_sync"]["sync_state_id"], str(state_b.id))

    def test_failed_attempt_keeps_published_version_and_does_not_mark_it_failed(self):
        state_a, _, slot = self.make_published_version(metrics_value=123)
        state_b = self.make_state(
            InsightsSyncStatus.FAILED,
            account_status=InsightsSyncStatus.FAILED,
            content_status=InsightsSyncStatus.FAILED,
        )
        self.assertNotEqual(state_a.id, state_b.id)
        account = self.client.get(self.account_url, self.params).data["data"]
        self.assertEqual(account["account_overview"]["metrics"]["followers"]["value"], 123)
        self.assertEqual(account["freshness"]["sync"]["status"], InsightsSyncStatus.COMPLETE)
        self.assertEqual(account["freshness"]["sync"]["account_status"], "complete")

    def test_account_and_content_follow_independent_published_attempts(self):
        old_state, _, slot = self.make_published_version(metrics_value=101)
        self.make_content_item(old_state, "content-from-a", value=101)
        new_state = self.make_state(
            InsightsSyncStatus.PARTIAL,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.PARTIAL,
            account_completed_at=timezone.now(),
        )
        InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=new_state.since,
            until=new_state.until,
            api_version=new_state.api_version,
            sync_state=new_state,
            metrics={"followers": {"value": 202, "availability": "available", "reason": ""}},
            fetched_at=timezone.now(),
        )
        slot.published_account_sync_state = new_state
        slot.save(update_fields=("published_account_sync_state", "updated_at"))
        self.make_content_item(new_state, "partial-from-b", value=202)

        account = self.client.get(self.account_url, self.params).data["data"]
        content = self.client.get(self.content_url, self.params).data["data"]
        self.assertEqual(account["account_overview"]["metrics"]["followers"]["value"], 202)
        self.assertEqual(content["content_performance"]["results"][0]["provider_media_id"], "content-from-a")

    def test_content_success_publishes_while_account_failure_keeps_old_account(self):
        old_state, _, slot = self.make_published_version(metrics_value=111)
        self.make_content_item(old_state, "content-a", value=111)
        new_state = self.make_state(
            InsightsSyncStatus.PARTIAL,
            account_status=InsightsSyncStatus.FAILED,
            content_status=InsightsSyncStatus.COMPLETE,
            content_completed_at=timezone.now(),
        )
        self.make_content_item(new_state, "content-b", value=222)
        slot.published_content_sync_state = new_state
        slot.save(update_fields=("published_content_sync_state", "updated_at"))

        account = self.client.get(self.account_url, self.params).data["data"]
        content = self.client.get(self.content_url, self.params).data["data"]
        self.assertEqual(account["account_overview"]["metrics"]["followers"]["value"], 111)
        self.assertEqual(content["content_performance"]["results"][0]["provider_media_id"], "content-b")

    def test_versioned_content_isolated_paginated_and_timestamp_uses_completion(self):
        completion = timezone.now() - timedelta(days=1)
        fetched_at = timezone.now()
        state_a, _, _ = self.make_published_version(
            metrics_value=1,
            account=False,
            content=True,
            since=date(2026, 8, 28),
            until=date(2026, 9, 26),
            content_completed_at=completion,
        )
        state_b = self.make_state(
            InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            content_completed_at=timezone.now(),
        )
        slot = InsightsSnapshotSlot.objects.get(social_account=self.account, duration_days=30)
        # An unpublished attempt's rows must not leak into the published view.
        for media_id in ("same-a", "same-z", "same-m"):
            self.make_content_item(state_a, media_id, published_at=datetime(2026, 9, 10, tzinfo=datetime_timezone.utc), fetched_at=fetched_at)
        self.make_content_item(state_b, "unpublished-b", value=2)

        current_30d = {"since": "2026-09-06", "until": "2026-10-05", "platform": SocialPlatform.INSTAGRAM}
        first = self.client.get(self.content_url, {**current_30d, "page_size": 2}).data["data"]
        second = self.client.get(self.content_url, {**current_30d, "page": 2, "page_size": 2}).data["data"]
        first_ids = [item["provider_media_id"] for item in first["content_performance"]["results"]]
        second_ids = [item["provider_media_id"] for item in second["content_performance"]["results"]]
        self.assertEqual(first_ids, ["same-z", "same-m"])
        self.assertEqual(second_ids, ["same-a"])
        self.assertEqual(first["content_performance"]["pagination"]["total_items"], 3)
        self.assertEqual(first["freshness"]["content"]["newest_fetched_at"], completion.isoformat())
        self.assertEqual(first["freshness"]["content"]["since"], state_a.since.isoformat())
        self.assertEqual(first["freshness"]["content"]["until"], state_a.until.isoformat())
        self.assertEqual(first["content_performance"]["results"][0]["metrics"]["likes"]["value"], 0)
        self.assertNotIn("unpublished-b", str(first))

    def test_duration_isolation_and_platform_duration_validation(self):
        state_30, _, _ = self.make_published_version(duration_days=30, metrics_value=30)
        state_7 = self.make_state(
            InsightsSyncStatus.COMPLETE,
            since=date(2026, 9, 20),
            until=date(2026, 9, 26),
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            account_completed_at=timezone.now(),
        )
        InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=state_7.since,
            until=state_7.until,
            api_version=state_7.api_version,
            sync_state=state_7,
            metrics={"followers": {"value": 7, "availability": "available", "reason": ""}},
            fetched_at=timezone.now(),
        )
        InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=7,
            published_account_sync_state=state_7,
        )
        current_7d = {"since": "2026-09-29", "until": "2026-10-05", "platform": SocialPlatform.INSTAGRAM}
        current_30d = {"since": "2026-09-06", "until": "2026-10-05", "platform": SocialPlatform.INSTAGRAM}
        self.assertEqual(self.client.get(self.account_url, current_7d).data["data"]["account_overview"]["metrics"]["followers"]["value"], 7)
        self.assertEqual(self.client.get(self.account_url, current_30d).data["data"]["account_overview"]["metrics"]["followers"]["value"], 30)
        invalid = {"since": "2026-09-08", "until": "2026-10-05", "platform": SocialPlatform.INSTAGRAM}
        self.assertEqual(self.client.get(self.account_url, invalid).status_code, 400)
        self.assertNotEqual(state_30.id, state_7.id)

    def test_account_completion_time_and_legacy_content_rules(self):
        completion = timezone.now() - timedelta(days=3)
        state, snapshot, _ = self.make_published_version(
            metrics_value=456,
            account_completed_at=completion,
        )
        snapshot.fetched_at = timezone.now()
        snapshot.save(update_fields=("fetched_at", "updated_at"))
        account = self.client.get(self.account_url, self.params).data["data"]
        self.assertEqual(account["freshness"]["account_snapshot"]["updated_at"], completion.isoformat())
        self.assertEqual(account["freshness"]["account_snapshot"]["fetched_at"], completion.isoformat())

        legacy_only = self.make_account(self.organization, provider_id="legacy-content-only")
        legacy_url = reverse("insights-account-snapshot-content", kwargs={
            "organization_id": self.organization.organization_id,
            "social_account_id": legacy_only.id,
        })
        InsightsMediaSnapshot.objects.create(
            social_account=legacy_only,
            provider_media_id="legacy-never-published",
            api_version="v26.0",
            metrics={"likes": {"value": 1, "availability": "available", "reason": ""}},
        )
        response = self.client.get(legacy_url, self.params).data["data"]
        self.assertEqual(response["content_performance"]["availability"], "unavailable")
        self.assertEqual(response["content_performance"]["results"], [])
        self.assertEqual(response["freshness"]["sync"]["content_status"], "never_synced")

    def test_invalid_platform_duration_and_cross_account_scope_are_rejected(self):
        mismatch = {**self.params, "platform": SocialPlatform.FACEBOOK}
        self.assertEqual(self.client.get(self.account_url, mismatch).status_code, 400)
        unsupported = {"since": "2026-09-06", "until": "2026-10-05", "platform": SocialPlatform.FACEBOOK}
        fb = self.make_account(
            self.organization,
            provider_id="facebook-unsupported-test",
            platform=SocialPlatform.FACEBOOK,
        )
        fb_url = reverse("insights-account-snapshot", kwargs={
            "organization_id": self.organization.organization_id,
            "social_account_id": fb.id,
        })
        self.assertEqual(self.client.get(fb_url, unsupported).status_code, 400)
        foreign_url = reverse("insights-account-snapshot", kwargs={
            "organization_id": self.organization.organization_id,
            "social_account_id": self.other_account.id,
        })
        self.assertEqual(self.client.get(foreign_url, self.params).status_code, 404)
