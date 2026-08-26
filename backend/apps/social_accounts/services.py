from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    SocialAccount,
    SocialAccountStatus,
)


@transaction.atomic
def create_social_account(
    *,
    organization,
    validated_data,
):
    """
    Create a social account for a specific organization.

    Only one active account per platform is allowed
    for each organization.
    """

    platform = validated_data["platform"]

    # ---------------------------------------------------------
    # ACTIVE PLATFORM DUPLICATE CHECK
    # ---------------------------------------------------------

    existing_account = SocialAccount.objects.filter(
        organization=organization,
        platform=platform,
        is_deleted=False,
    ).first()

    if existing_account:
        raise ValidationError(
            {
                "platform": (
                    f"{platform.capitalize()} is already "
                    "connected to this organization."
                )
            }
        )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    try:
        social_account = SocialAccount.objects.create(
            organization=organization,
            platform=platform,
            platform_account_id=validated_data["platform_account_id"],
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
        # Handles concurrent requests where another request
        # connected the same platform at the same time.
        raise ValidationError(
            {
                "platform": (
                    f"{platform.capitalize()} is already "
                    "connected to this organization."
                )
            }
        )

    return social_account


@transaction.atomic
def update_social_account(
    *,
    social_account,
    validated_data,
):
    """
    Update non-sensitive social account metadata.

    OAuth tokens, connection status and validity are
    controlled by the integration layer and should not
    be modified through normal CRUD updates.
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

    social_account.save()

    return social_account


@transaction.atomic
def mark_social_account_connected(
    *,
    social_account,
):
    """
    Mark an account as successfully connected.
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


@transaction.atomic
def mark_social_account_expired(
    *,
    social_account,
):
    """
    Mark an account whose provider token/session
    is no longer valid.
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


@transaction.atomic
def disconnect_social_account(
    *,
    social_account,
):
    """
    Disconnect a social account without deleting its
    historical record.

    This is preferable to hard deletion because the CRM
    may need the connection history later.
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


@transaction.atomic
def delete_social_account(
    *,
    social_account,
):
    """
    Soft-delete a social account.
    """

    social_account.soft_delete()

    return social_account
