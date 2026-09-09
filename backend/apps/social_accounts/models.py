from django.db import models

from apps.common.models import BaseModel

# ============================================================
# SOCIAL PLATFORM
# ============================================================


class SocialPlatform(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    LINKEDIN = "linkedin", "LinkedIn"
    YOUTUBE = "youtube", "YouTube"


# ============================================================
# SOCIAL ACCOUNT STATUS
# ============================================================


class SocialAccountStatus(models.TextChoices):
    CONNECTED = "connected", "Connected"
    DISCONNECTED = "disconnected", "Disconnected"
    EXPIRED = "expired", "Expired"
    ERROR = "error", "Error"


# ============================================================
# SOCIAL CONNECTION PROVIDER
# ============================================================
#
# A connection represents the OAuth/provider authorization.
#
# One connection can expose multiple social accounts.
#
# Example:
#
# Meta Connection
#     ├── Facebook Page A
#     ├── Instagram A
#     └── Instagram B
#
# ============================================================


class SocialConnectionProvider(models.TextChoices):
    META = "meta", "Meta"


class SocialConnectionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"
    ERROR = "error", "Error"


class SocialConnection(BaseModel):
    """
    Provider-level OAuth connection.

    This model represents the authorization granted to the
    application by a social-platform provider.

    A single connection may be associated with multiple
    SocialAccount records.

    Example:

        Meta connection
            |
            +--- Facebook Page
            +--- Instagram account
            +--- Instagram account

    Provider-specific OAuth credentials are managed by
    provider-specific credential models.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="social_connections",
    )

    provider = models.CharField(
        max_length=20,
        choices=SocialConnectionProvider.choices,
    )

    provider_user_id = models.CharField(
        max_length=255,
        blank=True,
    )

    refresh_token = models.TextField(
        blank=True,
    )

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=SocialConnectionStatus.choices,
        default=SocialConnectionStatus.ACTIVE,
        db_index=True,
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "social_connections"

        ordering = [
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "provider",
                    "provider_user_id",
                ],
                condition=(models.Q(is_deleted=False) & ~models.Q(provider_user_id="")),
                name="unique_org_provider_user_connection",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "provider",
                ],
                name="social_conn_org_provider_idx",
            ),
            models.Index(
                fields=[
                    "status",
                ],
                name="social_conn_status_idx",
            ),
            models.Index(
                fields=[
                    "token_expires_at",
                ],
                name="social_conn_token_expiry_idx",
            ),
        ]

    def __str__(self):
        return f"{self.organization.name} - " f"{self.provider} connection"


# ============================================================
# SOCIAL ACCOUNT
# ============================================================


class SocialAccount(BaseModel):
    """
        External social-media publishing destination belonging
        to an organization.

        A single organization can have multiple accounts on the
        same platform.

        Example:

            Organization A

                Instagram
                ├── @brand
                └── @brand_reels

                Facebook
                ├── Brand Page
                └── Store Page

        Provider-specific OAuth credentials are managed by
        provider-specific credential models. Core SocialAccount
        stores only provider-agnostic account metadata and
        connection state.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )

    # ---------------------------------------------------------
    # Provider connection
    # ---------------------------------------------------------

    connection = models.ForeignKey(
        SocialConnection,
        on_delete=models.PROTECT,
        related_name="social_accounts",
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # Platform
    # ---------------------------------------------------------

    platform = models.CharField(
        max_length=20,
        choices=SocialPlatform.choices,
        db_index=True,
    )

    # ---------------------------------------------------------
    # External provider identity
    # ---------------------------------------------------------

    platform_account_id = models.CharField(
        max_length=255,
    )

    # ---------------------------------------------------------
    # Display metadata
    # ---------------------------------------------------------

    account_name = models.CharField(
        max_length=255,
        blank=True,
    )

    username = models.CharField(
        max_length=255,
        blank=True,
    )

    profile_image = models.URLField(
        blank=True,
    )

    # ---------------------------------------------------------
    # Connection state
    # ---------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=SocialAccountStatus.choices,
        default=SocialAccountStatus.DISCONNECTED,
        db_index=True,
    )

    is_valid = models.BooleanField(
        default=True,
        db_index=True,
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "social_accounts"

        ordering = [
            "platform",
            "account_name",
        ]

        constraints = [
            # -------------------------------------------------
            # IMPORTANT:
            #
            # Multiple accounts on the same platform are
            # allowed.
            #
            # Only the exact same external account may not
            # be duplicated for the same organization.
            # -------------------------------------------------
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "platform",
                    "platform_account_id",
                ],
                condition=models.Q(is_deleted=False),
                name="unique_org_platform_account",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "platform",
                ],
                name="social_org_platform_idx",
            ),
            models.Index(
                fields=[
                    "organization",
                    "status",
                ],
                name="social_org_status_idx",
            ),
            models.Index(
                fields=[
                    "platform",
                    "platform_account_id",
                ],
                name="social_platform_account_idx",
            ),
        ]

    def __str__(self):
        display_name = self.account_name or self.username or self.platform_account_id

        return f"{self.organization.name} - " f"{self.platform} - " f"{display_name}"
