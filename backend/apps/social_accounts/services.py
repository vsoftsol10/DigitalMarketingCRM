from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from .models import (
    SocialAccount,
    SocialAccountStatus,
)

# ============================================================
# CREATE SOCIAL ACCOUNT
# ============================================================


@transaction.atomic
def create_social_account(
    *,
    organization,
    validated_data,
):
    """
    Create a social account for an organization.

    Multiple accounts on the same platform are allowed.

    Example:

        Organization
            ├── Instagram Account 1
            ├── Instagram Account 2
            └── Facebook Page 1

    The same external provider account cannot be connected
    more than once to the same organization.

    Provider-specific OAuth handling is intentionally kept
    outside this service.
    """

    platform = validated_data["platform"]

    platform_account_id = validated_data["platform_account_id"]

    # =========================================================
    # DUPLICATE EXACT ACCOUNT CHECK
    # =========================================================
    #
    # Same platform is allowed multiple times.
    #
    # Only this combination must be unique:
    #
    # organization
    # + platform
    # + platform_account_id
    #
    # =========================================================

    existing_account = SocialAccount.objects.filter(
        organization=organization,
        platform=platform,
        platform_account_id=platform_account_id,
        is_deleted=False,
    ).first()

    if existing_account:
        raise ValidationError(
            {
                "platform_account_id": (
                    "This social account is already " "connected to this organization."
                )
            }
        )

    # =========================================================
    # CREATE ACCOUNT
    # =========================================================

    try:
        social_account = SocialAccount.objects.create(
            organization=organization,
            platform=platform,
            platform_account_id=platform_account_id,
            account_name=validated_data.get(
                "account_name",
                "",
            ),
            username=validated_data.get(
                "username",
                "",
            ),
            profile_image=validated_data.get(
                "profile_image",
                "",
            ),
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
            last_synced_at=timezone.now(),
        )

    except IntegrityError:
        # -----------------------------------------------------
        # Handles concurrent requests attempting to create the
        # same external account.
        # -----------------------------------------------------

        raise ValidationError(
            {
                "platform_account_id": (
                    "This social account is already " "connected to this organization."
                )
            }
        )

    return social_account


# ============================================================
# UPDATE SOCIAL ACCOUNT
# ============================================================


@transaction.atomic
def update_social_account(
    *,
    social_account,
    validated_data,
):
    """
    Update non-sensitive display metadata.

    OAuth credentials, provider identity, connection state,
    validity and synchronization fields are not editable through
    the normal social-account CRUD API.
    """

    allowed_fields = {
        "account_name",
        "username",
        "profile_image",
    }

    for field, value in validated_data.items():
        if field in allowed_fields:
            setattr(
                social_account,
                field,
                value,
            )

    social_account.save(
        update_fields=[
            "account_name",
            "username",
            "profile_image",
            "updated_at",
        ]
    )

    return social_account


# ============================================================
# MARK ACCOUNT AS CONNECTED
# ============================================================


@transaction.atomic
def mark_social_account_connected(
    *,
    social_account,
):
    """
    Mark a social account as successfully connected.

    This will be used by the integration layer after a provider
    authorization/account sync succeeds.
    """

    social_account.status = SocialAccountStatus.CONNECTED

    social_account.is_valid = True

    social_account.last_synced_at = timezone.now()

    social_account.save(
        update_fields=[
            "status",
            "is_valid",
            "last_synced_at",
            "updated_at",
        ]
    )

    return social_account


# ============================================================
# MARK ACCOUNT AS DISCONNECTED
# ============================================================


@transaction.atomic
def disconnect_social_account(
    *,
    social_account,
):
    """
    Disconnect a social account without deleting its historical
    record.

    Historical references can therefore remain intact.
    """

    social_account.status = SocialAccountStatus.DISCONNECTED

    social_account.is_valid = False

    social_account.save(
        update_fields=[
            "status",
            "is_valid",
            "updated_at",
        ]
    )

    return social_account


# ============================================================
# MARK ACCOUNT AS EXPIRED
# ============================================================


@transaction.atomic
def mark_social_account_expired(
    *,
    social_account,
):
    """
    Mark a social account as expired when the provider
    authorization/token is no longer usable.
    """

    social_account.status = SocialAccountStatus.EXPIRED

    social_account.is_valid = False

    social_account.save(
        update_fields=[
            "status",
            "is_valid",
            "updated_at",
        ]
    )

    return social_account


# ============================================================
# MARK ACCOUNT AS ERROR
# ============================================================


@transaction.atomic
def mark_social_account_error(
    *,
    social_account,
):
    """
    Mark a social account as being in an integration error state.

    This is useful when provider synchronization or publishing
    fails in a way that makes the account temporarily unusable.
    """

    social_account.status = SocialAccountStatus.ERROR

    social_account.is_valid = False

    social_account.save(
        update_fields=[
            "status",
            "is_valid",
            "updated_at",
        ]
    )

    return social_account


# ============================================================
# REFRESH SOCIAL ACCOUNT SYNC STATE
# ============================================================


@transaction.atomic
def mark_social_account_synced(
    *,
    social_account,
):
    """
    Update the last successful synchronization timestamp.

    Provider-specific synchronization logic should happen in the
    integration layer; this function only updates the persisted
    account state.
    """

    social_account.last_synced_at = timezone.now()

    social_account.save(
        update_fields=[
            "last_synced_at",
            "updated_at",
        ]
    )

    return social_account


# ============================================================
# SOFT DELETE SOCIAL ACCOUNT
# ============================================================


@transaction.atomic
def delete_social_account(
    *,
    social_account,
):
    """
    Soft-delete a social account.

    Historical records remain in the database and can still be
    referenced by historical reporting/audit workflows.
    """

    social_account.soft_delete()

    return social_account
