import uuid

from django.db import models

from apps.common.models import BaseModel
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountInvitationAcceptance,
)


class InstagramCredentialStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"
    ERROR = "ERROR", "Error"


class InvitationInstagramOAuthStatus(models.TextChoices):
    STAGED = "staged", "Staged"
    CONFIRMED = "confirmed", "Confirmed"
    DECLINED = "declined", "Declined"
    INVALIDATED = "invalidated", "Invalidated"
    EXPIRED = "expired", "Expired"


class InvitationInstagramOAuthSession(BaseModel):
    """Encrypted, short-lived Instagram preview bound to an invitation claim."""

    selection_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    acceptance = models.ForeignKey(
        SocialAccountInvitationAcceptance,
        on_delete=models.CASCADE,
        related_name="instagram_oauth_sessions",
    )
    oauth_attempt = models.OneToOneField(
        "social_accounts.SocialAccountInvitationOAuthAttempt",
        on_delete=models.CASCADE,
        related_name="instagram_staging_session",
    )
    instagram_user_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    profile_image = models.URLField(max_length=2048, blank=True)
    encrypted_access_token = models.TextField()
    token_expires_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=InvitationInstagramOAuthStatus.choices,
        default=InvitationInstagramOAuthStatus.STAGED,
        db_index=True,
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "invitation_instagram_oauth_sessions"
        indexes = [
            models.Index(
                fields=["acceptance", "status", "expires_at"],
                name="inv_ig_oauth_acc_state_exp_idx",
            ),
        ]

    @property
    def is_expired(self):
        from django.utils import timezone

        return self.expires_at <= timezone.now()


class InstagramAccountCredential(BaseModel):
    """
    Credential created through Instagram API with
    Instagram Login / Business Login for Instagram.
    """

    social_account = models.OneToOneField(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="instagram_credential",
    )

    encrypted_access_token = models.TextField()

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=InstagramCredentialStatus.choices,
        default=InstagramCredentialStatus.ACTIVE,
        db_index=True,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "instagram_account_credentials"

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "token_expires_at",
                ],
                name="ig_cred_status_exp_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Instagram credential - "
            f"{self.social_account_id}"
        )
