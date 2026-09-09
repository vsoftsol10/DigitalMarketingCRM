from django.utils import timezone

from .crypto import decrypt_token
from .exceptions import MetaIntegrationError
from .models import (
    MetaCredentialStatus,
    MetaSocialAccountLink,
)
from .selectors import (
    get_meta_account_credential,
)


class MetaCredentialService:
    """
    Manage secure access to Meta credentials.

    Responsibilities:
        - Resolve the correct Meta credential.
        - Resolve Instagram credentials through its linked
          Facebook Page.
        - Validate credential status and expiry.
        - Decrypt credentials only when required.
        - Never expose credentials through API serializers.

    Credential resolution:

        Facebook Page
            -> PAGE credential on Facebook SocialAccount

        Instagram
            -> MetaSocialAccountLink
            -> Facebook Page
            -> PAGE credential on Facebook SocialAccount
    """

    @staticmethod
    def get_access_token(
        *,
        social_account,
    ):
        """
        Return the correct decrypted Meta access token
        for a social account.
        """

        if not social_account:
            raise MetaIntegrationError(
                "Social account is required.",
            )

        # ====================================================
        # 1. FACEBOOK PAGE
        # ====================================================

        if social_account.platform == "facebook":
            credential = get_meta_account_credential(
                social_account=social_account,
            )

        # ====================================================
        # 2. INSTAGRAM
        # ====================================================

        elif social_account.platform == "instagram":
            credential = MetaCredentialService._get_instagram_page_credential(
                instagram_account=social_account,
            )

        # ====================================================
        # 3. UNSUPPORTED PLATFORM
        # ====================================================

        else:
            raise MetaIntegrationError(
                "Meta credential resolution is not supported "
                f"for platform '{social_account.platform}'.",
            )

        # ====================================================
        # 4. CREDENTIAL NOT FOUND
        # ====================================================

        if credential is None:
            raise MetaIntegrationError(
                "Meta credential was not found.",
            )

        # ====================================================
        # 5. STATUS VALIDATION
        # ====================================================

        if credential.status != MetaCredentialStatus.ACTIVE:
            raise MetaIntegrationError(
                "Meta credential is not active.",
            )

        # ====================================================
        # 6. EXPIRY VALIDATION
        # ====================================================

        if (
            credential.token_expires_at is not None
            and credential.token_expires_at <= timezone.now()
        ):
            raise MetaIntegrationError(
                "Meta credential has expired.",
            )

        # ====================================================
        # 7. DECRYPT ONLY WHEN REQUIRED
        # ====================================================

        try:
            return decrypt_token(
                credential.access_token,
            )

        except Exception as exc:
            raise MetaIntegrationError(
                "Unable to decrypt Meta credential.",
            ) from exc

    # ========================================================
    # INSTAGRAM → FACEBOOK PAGE → PAGE CREDENTIAL
    # ========================================================

    @staticmethod
    def _get_instagram_page_credential(
        *,
        instagram_account,
    ):
        """
        Resolve the PAGE credential required for an Instagram
        account through its linked Facebook Page.
        """

        link = (
            MetaSocialAccountLink.objects.select_related(
                "facebook_page",
            )
            .filter(
                instagram_account=instagram_account,
                organization_id=instagram_account.organization_id,
                is_deleted=False,
            )
            .first()
        )

        if link is None:
            raise MetaIntegrationError(
                "Instagram account is not linked to a Facebook Page.",
            )

        facebook_page = link.facebook_page

        if facebook_page.is_deleted:
            raise MetaIntegrationError(
                "Linked Facebook Page is no longer available.",
            )

        credential = get_meta_account_credential(
            social_account=facebook_page,
        )

        if credential is None:
            raise MetaIntegrationError(
                "Linked Facebook Page Meta credential was not found.",
            )

        return credential
