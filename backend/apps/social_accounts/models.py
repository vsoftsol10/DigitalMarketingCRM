from django.db import models

from apps.common.models import BaseModel


class SocialPlatform(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    LINKEDIN = "linkedin", "LinkedIn"
    THREADS = "threads", "Threads"
    X = "x", "X"
    YOUTUBE = "youtube", "YouTube"


class SocialAccountStatus(models.TextChoices):
    CONNECTED = "connected", "Connected"
    DISCONNECTED = "disconnected", "Disconnected"
    EXPIRED = "expired", "Expired"
    ERROR = "error", "Error"


class SocialAccount(BaseModel):
    """
    External social media account connected to an organization.

    OAuth credentials and provider-specific secrets will be handled
    by the integration/service layer. This model keeps the persisted
    connection metadata.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )

    platform = models.CharField(
        max_length=20,
        choices=SocialPlatform.choices,
    )

    platform_account_id = models.CharField(
        max_length=255,
    )

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

    status = models.CharField(
        max_length=20,
        choices=SocialAccountStatus.choices,
        default=SocialAccountStatus.DISCONNECTED,
        db_index=True,
    )

    is_valid = models.BooleanField(
        default=True,
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # OAuth / token metadata
    # ---------------------------------------------------------

    access_token = models.TextField(
        blank=True,
    )

    refresh_token = models.TextField(
        blank=True,
    )

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "social_accounts"
        ordering = ["platform", "account_name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "platform",
                    "platform_account_id",
                ],
                name="unique_social_account_per_org_platform",
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
                fields=["status"],
                name="social_status_idx",
            ),
        ]

    def __str__(self):
        display_name = (
            self.account_name
            or self.username
            or self.platform_account_id
        )

        return (
            f"{self.organization.name} - "
            f"{self.platform} - {display_name}"
        )