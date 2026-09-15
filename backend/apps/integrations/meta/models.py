import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel
from apps.social_accounts.models import (
    SocialAccount,
    SocialConnection,
    SocialPlatform,
)

# ============================================================
# META CREDENTIAL TYPE
# ============================================================


class MetaCredentialType(models.TextChoices):
    USER = "user", "User"
    PAGE = "page", "Page"


# ============================================================
# META CREDENTIAL STATUS
# ============================================================


class MetaCredentialStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"
    INVALID = "INVALID", "Invalid"
    ERROR = "ERROR", "Error"


# ============================================================
# META ACCOUNT CREDENTIAL
# ============================================================


class MetaAccountCredential(BaseModel):
    """
    Meta-specific credential storage.

    USER credential:
        Meta User Access Token.
        Belongs to SocialConnection.

    PAGE credential:
        Facebook Page Access Token.
        Belongs to Facebook SocialAccount.
    """

    social_connection = models.ForeignKey(
        SocialConnection,
        on_delete=models.CASCADE,
        related_name="meta_credentials",
        null=True,
        blank=True,
    )

    social_account = models.OneToOneField(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="meta_credential",
        null=True,
        blank=True,
    )

    credential_type = models.CharField(
        max_length=20,
        choices=MetaCredentialType.choices,
    )

    access_token = models.TextField()

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=MetaCredentialStatus.choices,
        default=MetaCredentialStatus.ACTIVE,
        db_index=True,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "meta_account_credentials"

        indexes = [
            models.Index(
                fields=["status"],
                name="meta_cred_status_idx",
            ),
            models.Index(
                fields=["token_expires_at"],
                name="meta_cred_expiry_idx",
            ),
            models.Index(
                fields=["social_connection", "credential_type"],
                name="meta_cred_conn_type_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        credential_type=MetaCredentialType.USER,
                        social_connection__isnull=False,
                        social_account__isnull=True,
                    )
                    | models.Q(
                        credential_type=MetaCredentialType.PAGE,
                        social_account__isnull=False,
                        social_connection__isnull=True,
                    )
                ),
                name="meta_credential_valid_owner",
            ),
        ]

    def clean(self):
        super().clean()

        if self.credential_type == MetaCredentialType.USER:
            if not self.social_connection:
                raise ValidationError(
                    "USER credential must belong to a social connection."
                )

            if self.social_account:
                raise ValidationError(
                    "USER credential cannot belong to a social account."
                )

        elif self.credential_type == MetaCredentialType.PAGE:
            if not self.social_account:
                raise ValidationError(
                    "PAGE credential must belong to a social account."
                )

            if self.social_connection:
                raise ValidationError(
                    "PAGE credential cannot belong to a social connection."
                )

    def __str__(self):
        if self.social_account:
            return (
                f"{self.social_account.platform}:"
                f"{self.social_account.platform_account_id}"
            )

        if self.social_connection:
            return "meta-connection:" f"{self.social_connection.provider_user_id}"

        return f"meta-credential:{self.pk}"


# ============================================================
# FACEBOOK PAGE ↔ INSTAGRAM LINK
# ============================================================


class MetaSocialAccountLink(BaseModel):
    """
    Meta-specific relationship between:

        Facebook Page
              ↓
        Instagram Professional Account
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="meta_social_account_links",
    )

    facebook_page = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="meta_instagram_links_as_page",
    )

    instagram_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="meta_page_links_as_instagram",
    )

    class Meta:
        db_table = "meta_social_account_links"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "facebook_page",
                    "instagram_account",
                ],
                condition=models.Q(is_deleted=False),
                name="unique_active_meta_page_instagram_link",
            ),
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "instagram_account",
                ],
                condition=models.Q(is_deleted=False),
                name="unique_active_meta_instagram_account_link",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "facebook_page",
                ],
                name="meta_link_org_page_idx",
            ),
            models.Index(
                fields=[
                    "organization",
                    "instagram_account",
                ],
                name="meta_link_org_ig_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.facebook_page_id == self.instagram_account_id:
            raise ValidationError(
                "Facebook Page and Instagram account must be different."
            )

        if self.facebook_page.platform != SocialPlatform.FACEBOOK:
            raise ValidationError(
                "facebook_page must reference a Facebook social account."
            )

        if self.instagram_account.platform != SocialPlatform.INSTAGRAM:
            raise ValidationError(
                "instagram_account must reference an Instagram social account."
            )

        if self.facebook_page.organization_id != self.organization_id:
            raise ValidationError("Facebook Page must belong to the same organization.")

        if self.instagram_account.organization_id != self.organization_id:
            raise ValidationError(
                "Instagram account must belong to the same organization."
            )

    def __str__(self):
        return (
            f"{self.facebook_page.platform_account_id}"
            " -> "
            f"{self.instagram_account.platform_account_id}"
        )


# ============================================================
# META OAUTH SESSION
# ============================================================


class MetaOAuthSession(BaseModel):
    """
    Short-lived server-side OAuth selection session.

    This replaces Redis.

    Flow:

        OAuth callback
            ↓
        discover Pages + Instagram
            ↓
        encrypt temporary data
            ↓
        save here
            ↓
        frontend selects Page
            ↓
        confirm
            ↓
        persist SocialAccount records
            ↓
        session consumed
    """

    selection_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="meta_oauth_sessions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meta_oauth_sessions",
    )

    provider_user_id = models.CharField(
        max_length=255,
    )

    encrypted_access_token = models.TextField()

    encrypted_accounts = models.TextField()

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField(
        db_index=True,
    )

    consumed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "meta_oauth_sessions"

        indexes = [
            models.Index(
                fields=["organization", "user"],
                name="meta_oauth_org_user_idx",
            ),
            models.Index(
                fields=[
                    "expires_at",
                ],
                name="meta_oauth_session_expiry_idx",
            ),
        ]

    @property
    def is_expired(self):
        from django.utils import timezone

        return self.expires_at <= timezone.now()

    @property
    def is_consumed(self):
        return self.consumed_at is not None

    def __str__(self):
        return f"Meta OAuth session {self.selection_key}"
