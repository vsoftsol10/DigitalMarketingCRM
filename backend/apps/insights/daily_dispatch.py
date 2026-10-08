"""Daily enqueueing for the existing account-duration Insights sync workflow."""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .models import InsightsSyncState
from .selectors import get_connected_accounts_for_daily_insights
from .sync_service import request_insights_sync

logger = logging.getLogger(__name__)

DAILY_INSIGHTS_DURATIONS = {
    SocialPlatform.INSTAGRAM: (7, 30),
    SocialPlatform.FACEBOOK: (7, 28),
}


def dispatch_daily_insights_syncs(*, run_date=None):
    """Create today's account-duration attempts and enqueue their existing stage work."""
    run_date = run_date or timezone.localdate()
    summary = {
        "accounts_discovered": 0,
        "workloads_considered": 0,
        "workloads_enqueued": 0,
        "active_work_skipped": 0,
        "same_day_attempt_skipped": 0,
        "accounts_no_longer_eligible": 0,
    }

    accounts = get_connected_accounts_for_daily_insights().iterator(chunk_size=200)
    for discovered_account in accounts:
        summary["accounts_discovered"] += 1
        durations = DAILY_INSIGHTS_DURATIONS.get(discovered_account.platform, ())

        for duration_days in durations:
            summary["workloads_considered"] += 1
            since = run_date - timedelta(days=duration_days - 1)

            # The account lock serializes this daily reservation with manual
            # requests and concurrent dispatcher invocations.
            with transaction.atomic():
                account = (
                    SocialAccount.objects.select_for_update()
                    .filter(
                        id=discovered_account.id,
                        is_deleted=False,
                        status=SocialAccountStatus.CONNECTED,
                        is_valid=True,
                        platform=discovered_account.platform,
                    )
                    .first()
                )
                if account is None:
                    summary["accounts_no_longer_eligible"] += 1
                    continue

                already_attempted_today = InsightsSyncState.objects.filter(
                    social_account=account,
                    since=since,
                    until=run_date,
                    is_deleted=False,
                    requested_at__date=run_date,
                ).exists()
                if already_attempted_today:
                    summary["same_day_attempt_skipped"] += 1
                    continue

                result = request_insights_sync(
                    social_account_id=str(account.id),
                    since=since,
                    until=run_date,
                )

            if result.get("already_active"):
                summary["active_work_skipped"] += 1
            elif result.get("sync_state_id") and result.get("status") not in {"failed", "not_found"}:
                summary["workloads_enqueued"] += 1

    logger.info("Daily Insights dispatcher completed: %s", summary)
    return summary
