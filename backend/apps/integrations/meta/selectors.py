from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccount,
    SocialConnection,
    SocialConnectionProvider,
)

from .models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaProviderExpiryState,
)


def meta_user_credential_expiry_eligibility_q(now=None):
    """Expiry conditions required before a Meta USER token may be used."""
    now = now or timezone.now()
    legacy_expiry_is_current = Q(token_expires_at__isnull=True) | Q(
        token_expires_at__gt=now
    )
    data_access_is_current = Q(data_access_expires_at__gt=now)
    finite_provider_expiry_is_current = (
        Q(
            provider_expiry_state=MetaProviderExpiryState.FINITE,
            provider_expires_at__gt=now,
        )
        & (Q(provider_is_valid__isnull=True) | Q(provider_is_valid=True))
    )
    no_finite_expiry_is_confirmed = Q(
        provider_expiry_state=MetaProviderExpiryState.NO_FINITE_EXPIRY,
        provider_is_valid=True,
        provider_expires_at__isnull=True,
    )
    return (
        legacy_expiry_is_current
        & data_access_is_current
        & (finite_provider_expiry_is_current | no_finite_expiry_is_confirmed)
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
    Return a usable USER credential, or an inactive lifecycle record.

    Active UNKNOWN/expired credentials are excluded so they cannot be used
    as an indefinite fallback. Inactive lifecycle rows remain selectable for
    reconnect-status display; token consumers must continue to require ACTIVE.
    The stored access_token is encrypted.
    """

    if not social_connection:
        return None

    now = timezone.now()
    return (
        MetaAccountCredential.objects.filter(
            social_connection=social_connection,
            credential_type=MetaCredentialType.USER,
            is_deleted=False,
        )
        .filter(
            (
                Q(status=MetaCredentialStatus.ACTIVE, access_token__gt="")
                & meta_user_credential_expiry_eligibility_q(now)
            )
            | Q(
                status__in=(
                    MetaCredentialStatus.EXPIRED,
                    MetaCredentialStatus.REVOKED,
                    MetaCredentialStatus.INVALID,
                    MetaCredentialStatus.ERROR,
                )
            )
        )
        .order_by(
            Case(
                When(status=MetaCredentialStatus.ACTIVE, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            "-created_at",
            "-id",
        )
        .select_related(
            "social_connection",
        )
        .first()
    )
