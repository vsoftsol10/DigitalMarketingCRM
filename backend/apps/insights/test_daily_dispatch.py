from datetime import date, datetime, timedelta
from uuid import uuid4
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .daily_dispatch import dispatch_daily_insights_syncs
from .models import InsightsSnapshotSlot, InsightsSyncState, InsightsSyncStatus


class DailyInsightsDispatcherTests(TestCase):
    run_date = date(2026, 10, 7)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="daily-insights-owner@example.com",
            first_name="Daily Insights Owner",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-DAILY-1",
            name="Daily Insights Organization",
            slug="daily-insights-organization",
            industry="Retail",
            created_by=self.owner,
        )

    def make_account(self, platform, suffix, **overrides):
        values = {
            "organization": self.organization,
            "platform": platform,
            "platform_account_id": f"daily-{suffix}",
            "username": f"daily-{suffix}",
            "status": SocialAccountStatus.CONNECTED,
            "is_valid": True,
        }
        values.update(overrides)
        return SocialAccount.objects.create(**values)

    @staticmethod
    def queued_result(**_kwargs):
        return {"status": InsightsSyncStatus.QUEUED, "sync_state_id": str(uuid4()), "already_active": False}

    def test_platform_mapping_and_eligibility_create_two_workloads_per_supported_account(self):
        instagram = self.make_account(SocialPlatform.INSTAGRAM, "ig")
        facebook = self.make_account(SocialPlatform.FACEBOOK, "fb")
        self.make_account(SocialPlatform.INSTAGRAM, "disconnected", status=SocialAccountStatus.DISCONNECTED)
        self.make_account(SocialPlatform.FACEBOOK, "invalid", is_valid=False)
        self.make_account(SocialPlatform.INSTAGRAM, "deleted", is_deleted=True)
        self.make_account(SocialPlatform.LINKEDIN, "unsupported")

        with patch("apps.insights.daily_dispatch.request_insights_sync", side_effect=self.queued_result) as request:
            summary = dispatch_daily_insights_syncs(run_date=self.run_date)

        self.assertEqual(summary["accounts_discovered"], 2)
        self.assertEqual(summary["workloads_considered"], 4)
        self.assertEqual(summary["workloads_enqueued"], 4)
        expected = {
            (str(instagram.id), 7, date(2026, 10, 1), self.run_date),
            (str(instagram.id), 30, date(2026, 9, 8), self.run_date),
            (str(facebook.id), 7, date(2026, 10, 1), self.run_date),
            (str(facebook.id), 28, date(2026, 9, 10), self.run_date),
        }
        actual = {
            (call.kwargs["social_account_id"], (call.kwargs["until"] - call.kwargs["since"]).days + 1,
             call.kwargs["since"], call.kwargs["until"])
            for call in request.call_args_list
        }
        self.assertEqual(actual, expected)

    def test_same_day_attempt_is_not_enqueued_again(self):
        account = self.make_account(SocialPlatform.INSTAGRAM, "already-synced")
        since = self.run_date - timedelta(days=6)
        state = InsightsSyncState.objects.create(
            social_account=account,
            since=since,
            until=self.run_date,
            api_version="v26.0",
            status=InsightsSyncStatus.COMPLETE,
            requested_at=timezone.now(),
        )
        InsightsSyncState.objects.filter(pk=state.pk).update(
            requested_at=timezone.make_aware(datetime(2026, 10, 7, 9, 0)),
        )

        with patch("apps.insights.daily_dispatch.request_insights_sync", side_effect=self.queued_result) as request:
            summary = dispatch_daily_insights_syncs(run_date=self.run_date)

        self.assertEqual(summary["same_day_attempt_skipped"], 1)
        self.assertEqual(summary["workloads_enqueued"], 1)
        self.assertEqual(request.call_count, 1)
        self.assertEqual((request.call_args.kwargs["until"] - request.call_args.kwargs["since"]).days + 1, 30)

    def test_existing_active_duration_is_reused_without_a_duplicate_attempt(self):
        account = self.make_account(SocialPlatform.INSTAGRAM, "active")
        yesterday = self.run_date - timedelta(days=1)
        active_state = InsightsSyncState.objects.create(
            social_account=account,
            since=yesterday - timedelta(days=6),
            until=yesterday,
            api_version="v26.0",
            status=InsightsSyncStatus.SYNCING,
        )
        InsightsSnapshotSlot.objects.create(
            social_account=account,
            duration_days=7,
            active_sync_state=active_state,
        )

        with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch_tasks:
            summary = dispatch_daily_insights_syncs(run_date=self.run_date)

        self.assertEqual(summary["active_work_skipped"], 1)
        self.assertEqual(summary["workloads_enqueued"], 1)
        self.assertEqual(InsightsSyncState.objects.filter(social_account=account).count(), 2)
        dispatch_tasks.assert_not_called()

    def test_scheduler_only_uses_existing_enqueue_path(self):
        account = self.make_account(SocialPlatform.FACEBOOK, "enqueue-only")
        with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch_tasks:
            with self.captureOnCommitCallbacks(execute=True):
                summary = dispatch_daily_insights_syncs(run_date=self.run_date)

        self.assertEqual(summary["workloads_enqueued"], 2)
        self.assertEqual(dispatch_tasks.call_count, 2)
        self.assertEqual(InsightsSyncState.objects.filter(social_account=account).count(), 2)

    def test_beat_runs_at_eight_in_project_timezone(self):
        entry = settings.CELERY_BEAT_SCHEDULE["daily-insights-dispatcher"]
        self.assertEqual(entry["task"], "apps.insights.tasks.daily_insights_dispatcher_task")
        self.assertEqual(entry["schedule"].hour, {8})
        self.assertEqual(entry["schedule"].minute, {0})
        self.assertEqual(settings.CELERY_TIMEZONE, settings.TIME_ZONE)
