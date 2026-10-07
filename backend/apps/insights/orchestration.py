"""HTTP-facing idempotency gate for persisted Insights synchronization."""

from django.db import transaction

from apps.common.exceptions import ResourceNotFoundException
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .models import InsightsSyncState
from .sync_service import request_insights_sync


def request_account_insights_sync(*, account, since, until, force_refresh=False):
    """Create an attempt for an explicit refresh, reusing only active work."""
    with transaction.atomic():
        locked_account = (
            SocialAccount.objects.select_for_update()
            .filter(
                id=account.id,
                organization_id=account.organization_id,
                is_deleted=False,
                status=SocialAccountStatus.CONNECTED,
                is_valid=True,
                platform__in=(SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK),
            )
            .first()
        )
        if locked_account is None:
            raise ResourceNotFoundException("Connected social account not found.")

        result = request_insights_sync(
            social_account_id=str(locked_account.id),
            since=since,
            until=until,
        )
        state_id = result.get("sync_state_id")
        if not state_id:
            raise ResourceNotFoundException("Connected social account not found.")
        state = InsightsSyncState.objects.get(id=state_id, is_deleted=False)
        return state, bool(result.get("already_active"))
