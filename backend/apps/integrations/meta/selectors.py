from apps.social_accounts.models import (
    SocialAccount,
    SocialConnection,
    SocialConnectionProvider,
)

from .models import (
    MetaAccountCredential,
    MetaCredentialType,
)


def get_meta_connection(
    *,
    organization,
    provider_user_id,
):
    """
    Return the active Meta connection for an organization
    and Meta provider user.
    """

    if not organization or not provider_user_id:
        return None

    return (
        SocialConnection.objects.filter(
            organization=organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=str(
                provider_user_id,
            ),
            is_deleted=False,
        )
        .select_related("organization")
        .first()
    )


def get_social_account(
    *,
    organization,
    platform,
    platform_account_id,
):
    """
    Return an active social account belonging to an organization.
    """

    if not organization or not platform or not platform_account_id:
        return None

    return (
        SocialAccount.objects.filter(
            organization=organization,
            platform=platform,
            platform_account_id=str(
                platform_account_id,
            ),
            is_deleted=False,
        )
        .select_related(
            "organization",
            "connection",
        )
        .first()
    )


def get_meta_account_credential(
    *,
    social_account,
):
    """
    Return the PAGE credential belonging to a SocialAccount.

    The stored access_token is encrypted.
    """

    if not social_account:
        return None

    return (
        MetaAccountCredential.objects.filter(
            social_account=social_account,
            credential_type=MetaCredentialType.PAGE,
            is_deleted=False,
        )
        .select_related(
            "social_account",
        )
        .first()
    )


def get_meta_connection_credential(
    *,
    social_connection,
):
    """
    Return the USER credential belonging to a Meta connection.

    The stored access_token is encrypted.
    """

    if not social_connection:
        return None

    return (
        MetaAccountCredential.objects.filter(
            social_connection=social_connection,
            credential_type=MetaCredentialType.USER,
            is_deleted=False,
        )
        .select_related(
            "social_connection",
        )
        .first()
    )
