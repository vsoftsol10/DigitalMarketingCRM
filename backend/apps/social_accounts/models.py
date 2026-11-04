from django.conf import settings
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


class SocialAccountInvitationMode(models.TextChoices):
    EMAIL = "email", "Email invitation"
    SHARE_LINK = "share_link", "Share link"


class SocialAccountInvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"
    EXHAUSTED = "exhausted", "Usage limit reached"


class SocialAccountInvitationDeliveryStatus(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not required"
    PENDING_CONFIGURATION = "pending_configuration", "Pending email configuration"
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class SocialAccountInvitationAcceptanceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class SocialAccountInvitationOAuthPlatform(models.TextChoices):
    FACEBOOK = "facebook", "Facebook"
    INSTAGRAM = "instagram", "Instagram"


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
        max_length=2048,
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


class SocialAccountInvitation(BaseModel):
    """A scoped bearer capability to connect social accounts to one organization.

    Share-link invitations are intentionally transferable: possession of the
    link grants the ability to claim a use until the invitation expires, is
    revoked, or reaches its usage limit. Email invitations record a delivery
    address, but that address is not treated as verified identity.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="social_account_invitations",
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_social_account_invitations",
    )
    mode = models.CharField(
        max_length=20,
        choices=SocialAccountInvitationMode.choices,
    )
    recipient_email = models.EmailField(blank=True, default="")
    token_hash = models.CharField(max_length=64, unique=True)
    pending_token_hash = models.CharField(max_length=64, blank=True, default="")
    pending_delivery_token_encrypted = models.TextField(blank=True, default="")
    allowed_platforms = models.JSONField(default=list)
    status = models.CharField(
        max_length=20,
        choices=SocialAccountInvitationStatus.choices,
        default=SocialAccountInvitationStatus.PENDING,
        db_index=True,
    )
    expires_at = models.DateTimeField(db_index=True)
    usage_limit = models.PositiveIntegerField(default=1)
    usage_count = models.PositiveIntegerField(default=0)
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Email delivery is a separate lifecycle. No email is sent by the
    # invitation foundation until an approved invitation template exists.
    delivery_status = models.CharField(
        max_length=32,
        choices=SocialAccountInvitationDeliveryStatus.choices,
        default=SocialAccountInvitationDeliveryStatus.NOT_REQUIRED,
    )
    delivery_attempts = models.PositiveIntegerField(default=0)
    provider_message_id = models.CharField(max_length=500, blank=True)
    delivery_error_code = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "social_account_invitations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organization", "status", "created_at"],
                name="soc_inv_org_status_created_idx",
            ),
            models.Index(
                fields=["status", "expires_at"],
                name="soc_inv_status_expiry_idx",
            ),
            models.Index(
                fields=["recipient_email", "created_at"],
                name="soc_inv_email_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(usage_limit__gte=1),
                name="soc_inv_usage_limit_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(usage_count__lte=models.F("usage_limit")),
                name="soc_inv_usage_within_limit",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        mode=SocialAccountInvitationMode.EMAIL,
                        recipient_email__gt="",
                    )
                    | models.Q(
                        mode=SocialAccountInvitationMode.SHARE_LINK,
                        recipient_email="",
                    )
                ),
                name="soc_inv_mode_email_consistent",
            ),
        ]


class SocialAccountInvitationAcceptance(BaseModel):
    """A short-lived, separately revocable claim of invitation capacity."""

    invitation = models.ForeignKey(
        SocialAccountInvitation,
        on_delete=models.CASCADE,
        related_name="acceptances",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    selected_platforms = models.JSONField(default=list)
    status = models.CharField(
        max_length=16,
        choices=SocialAccountInvitationAcceptanceStatus.choices,
        default=SocialAccountInvitationAcceptanceStatus.ACTIVE,
        db_index=True,
    )
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "social_account_invitation_acceptances"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["invitation", "status", "expires_at"],
                name="soc_inv_acc_inv_state_exp_idx",
            ),
        ]


class SocialAccountInvitationOAuthAttempt(BaseModel):
    """One-time OAuth state bound to an active invitation acceptance."""

    acceptance = models.ForeignKey(
        SocialAccountInvitationAcceptance,
        on_delete=models.CASCADE,
        related_name="oauth_attempts",
    )
    platform = models.CharField(
        max_length=20,
        choices=SocialAccountInvitationOAuthPlatform.choices,
    )
    state_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "social_account_invitation_oauth_attempts"
        indexes = [
            models.Index(
                fields=["acceptance", "platform", "expires_at"],
                name="soc_inv_oauth_acc_plat_exp_idx",
            ),
        ]

    @property
    def is_expired(self):
        from django.utils import timezone

        return self.expires_at <= timezone.now()

    @property
    def is_consumed(self):
        return self.consumed_at is not None


class SocialAccountInvitationAcceptanceAccount(BaseModel):
    """Audit link for an account persisted through an invitation session."""

    acceptance = models.ForeignKey(
        SocialAccountInvitationAcceptance,
        on_delete=models.CASCADE,
        related_name="connected_accounts",
    )
    # Keep the acceptance audit if an account is later hard-deleted. Normal
    # account disconnects are soft deletes and remain visible through the FK.
    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitation_acceptance_links",
    )
    platform = models.CharField(max_length=20, choices=SocialPlatform.choices)
    platform_account_id = models.CharField(max_length=255)

    class Meta:
        db_table = "social_account_invitation_acceptance_accounts"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["acceptance", "social_account"],
                condition=models.Q(social_account__isnull=False),
                name="soc_inv_acc_account_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["platform", "platform_account_id"],
                name="soc_inv_acc_account_ext_idx",
            ),
        ]
