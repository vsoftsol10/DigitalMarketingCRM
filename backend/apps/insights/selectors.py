from apps.organizations.models import Organization
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)


def get_accessible_organizations(*, user):
    """Organizations this authenticated user owns under current access rules."""
    return Organization.objects.filter(
        created_by=user,
        is_deleted=False,
    ).only(
        "organization_id",
        "name",
        "created_at",
    ).order_by("name", "organization_id")


def get_accessible_organization(*, user, organization_id):
    return get_accessible_organizations(user=user).filter(
        organization_id=organization_id,
    ).first()


def _connected_accounts_queryset():
    return SocialAccount.objects.filter(
        is_deleted=False,
        status=SocialAccountStatus.CONNECTED,
        is_valid=True,
    ).select_related("organization").order_by(
        "platform", "account_name", "username", "id",
    )


def get_connected_accounts_for_organization(*, organization, platform=None):
    queryset = _connected_accounts_queryset().filter(organization=organization)
    if platform:
        queryset = queryset.filter(platform=platform)
    return queryset


def get_connected_accounts_for_daily_insights():
    """Active connected Facebook and Instagram accounts for the daily dispatcher."""
    return _connected_accounts_queryset().filter(
        platform__in=(SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK),
    )


def get_connected_account_for_organization(*, organization, social_account_id):
    return get_connected_accounts_for_organization(
        organization=organization,
    ).filter(id=social_account_id).first()
