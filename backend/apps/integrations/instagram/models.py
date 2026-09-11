from django.db import models

from apps.common.models import BaseModel
from apps.social_accounts.models import SocialAccount


class InstagramCredentialStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"
    ERROR = "ERROR", "Error"


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