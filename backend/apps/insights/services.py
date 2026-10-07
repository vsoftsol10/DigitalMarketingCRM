from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import ResourceNotFoundException
from apps.social_accounts.models import SocialPlatform

from .selectors import (
    get_accessible_organization,
    get_connected_account_for_organization,
    get_connected_accounts_for_organization,
)
from .providers import fetch_provider_insights


def get_organization_for_user(*, user, organization_id):
    organization = get_accessible_organization(
        user=user,
        organization_id=organization_id,
    )
    if organization is None:
        # Hide whether an organization exists if it is not accessible.
        raise ResourceNotFoundException("Organization not found.")
    return organization


def list_organization_accounts(*, user, organization_id, platform=None):
    organization = get_organization_for_user(
        user=user,
        organization_id=organization_id,
    )
    normalized_platform = None
    if platform:
        normalized_platform = platform.strip().lower()
        supported_platforms = {choice.value for choice in SocialPlatform}
        if normalized_platform not in supported_platforms:
            raise ValidationError({"platform": "Unsupported platform filter."})

    return get_connected_accounts_for_organization(
        organization=organization,
        platform=normalized_platform,
    )


def get_selected_account(*, user, organization_id, social_account_id):
    organization = get_organization_for_user(
        user=user,
        organization_id=organization_id,
    )
    account = get_connected_account_for_organization(
        organization=organization,
        social_account_id=social_account_id,
    )
    if account is None:
        # A mismatched, disconnected, deleted, or invalid account is
        # indistinguishable from an unknown account at this boundary.
        raise ResourceNotFoundException("Connected social account not found.")
    return organization, account


def build_insights_response(*, organization, account, since=None, until=None, cursor=None):
    """Fetch and normalize read-only metrics for exactly one selected account."""
    today = timezone.localdate()
    if since is None and until is None:
        until = today
        since = until - timedelta(days=29)
    if since is None or until is None:
        raise ValidationError("Both since and until must be provided together.")
    if since > until:
        raise ValidationError({"since": "since must be on or before until."})
    if until > today:
        raise ValidationError({"until": "until cannot be in the future."})
    if (until - since).days > 89:
        raise ValidationError({"date_range": "Insights date ranges cannot exceed 90 days."})

    provider_data = fetch_provider_insights(
        account=account,
        since=since,
        until=until,
        cursor=cursor,
    )
    return {
        "schema_version": "1.0",
        "filters": {
            "organization_id": organization.organization_id,
            "date_range": {
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
        },
        "account": account,
        "provider_metadata": provider_data["provider_metadata"],
        "metrics": provider_data["metrics"],
        "follower_growth": provider_data["follower_growth"],
        "account_performance": provider_data["account_performance"],
        "content_performance": provider_data["content_performance"],
    }
