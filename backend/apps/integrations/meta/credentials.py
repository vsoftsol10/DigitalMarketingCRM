from django.utils import timezone

from .crypto import decrypt_token
from .exceptions import MetaIntegrationError
from .models import MetaCredentialStatus
from .selectors import (
    get_meta_account_credential,
)


class MetaCredentialService:
    """
    Manage secure access to Meta credentials.

    Responsibilities:
        - Resolve Meta credentials for Facebook Pages.
        - Validate credential status and expiry.
        - Decrypt credentials only when required.
        - Never expose credentials through API serializers.

    IMPORTANT:
        This service is ONLY responsible for Facebook Page
        credentials.

        Instagram credentials are managed by the dedicated
        Instagram integration and Instagram credential service.
    """

    @staticmethod
    def get_access_token(
        *,
        social_account,
    ):
        """
        Return the decrypted Meta access token for a
        Facebook Page.

        Meta credentials are intentionally NOT resolved for
        Instagram accounts.

        Facebook:
            SocialAccount
                ↓
            Meta PAGE credential
                ↓
            decrypted access token

        Instagram:
            InstagramAccountCredential
                ↓
            handled by Instagram integration
        """

        if not social_account:
            raise MetaIntegrationError(
                "Social account is required.",
            )

        # ====================================================
        # FACEBOOK PAGE ONLY
        # ====================================================

        if social_account.platform != "facebook":
            raise MetaIntegrationError(
                "Meta credential resolution is supported only " "for Facebook Pages.",
            )

        credential = get_meta_account_credential(
            social_account=social_account,
        )

        # ====================================================
        # CREDENTIAL NOT FOUND
        # ====================================================

        if credential is None:
            raise MetaIntegrationError(
                "Meta credential was not found for this Facebook Page.",
            )

        # ====================================================
        # STATUS VALIDATION
        # ====================================================

        if credential.status != MetaCredentialStatus.ACTIVE:
            raise MetaIntegrationError(
                "Meta credential is not active.",
            )

        # ====================================================
        # EXPIRY VALIDATION
        # ====================================================

        if (
            credential.token_expires_at is not None
            and credential.token_expires_at <= timezone.now()
        ):
            raise MetaIntegrationError(
                "Meta credential has expired.",
            )

        # ====================================================
        # DECRYPT TOKEN
        # ====================================================

        try:
            return decrypt_token(
                credential.access_token,
            )

        except Exception as exc:
            raise MetaIntegrationError(
                "Unable to decrypt Meta credential.",
            ) from exc
