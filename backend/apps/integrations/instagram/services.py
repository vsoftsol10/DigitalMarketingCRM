from datetime import timedelta
from urllib.parse import urlencode

from django.db import transaction
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)

from .client import InstagramAPIClient
from .constants import (
    INSTAGRAM_LONG_LIVED_TOKEN_DEFAULT_SECONDS,
)
from .crypto import encrypt_token
from .exceptions import InstagramIntegrationError
from .models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
)
from .oauth import (
    create_oauth_nonce,
    create_oauth_state,
)


class InstagramOAuthService:
    """
    Handles the complete server-side Instagram Login flow.
    """

    def __init__(self):
        self.client = InstagramAPIClient()

    # ========================================================
    # AUTHORIZATION URL
    # ========================================================

    def build_authorization_url(
        self,
        *,
        organization,
        user,
    ):
        if organization.created_by_id != user.id:
            raise InstagramIntegrationError(
                "You do not have access to this organization."
            )

        nonce = create_oauth_nonce()

        state = create_oauth_state(
            organization_id=organization.organization_id,
            user_id=user.pk,
            nonce=nonce,
        )

        params = {
            "client_id": self.client.client_id,
            "redirect_uri": self.client.redirect_uri,
            "response_type": "code",
            "scope": "instagram_business_basic",
            "state": state,
        }

        return "https://www.instagram.com/oauth/authorize?" f"{urlencode(params)}"

    # ========================================================
    # COMPLETE CALLBACK
    # ========================================================

    @transaction.atomic
    def handle_callback(
        self,
        *,
        code,
        organization,
        user,
    ):
        if organization.created_by_id != user.id:
            raise InstagramIntegrationError(
                "You do not have access to this organization."
            )

        # ----------------------------------------------------
        # STEP 1
        # Authorization code → short-lived token
        # ----------------------------------------------------

        short_token_data = self.client.exchange_code(
            code=code,
        )

        short_lived_token = short_token_data.get("access_token")

        if not short_lived_token:
            raise InstagramIntegrationError("Instagram did not return an access token.")

        # ----------------------------------------------------
        # STEP 2
        # Short-lived → long-lived token
        # ----------------------------------------------------

        long_token_data = self.client.exchange_long_lived_token(
            short_lived_token=short_lived_token,
        )

        long_lived_token = long_token_data.get("access_token")

        if not long_lived_token:
            raise InstagramIntegrationError(
                "Instagram did not return a long-lived access token."
            )

        expires_in = long_token_data.get(
            "expires_in",
            INSTAGRAM_LONG_LIVED_TOKEN_DEFAULT_SECONDS,
        )

        try:
            expires_in = int(expires_in)
        except (
            TypeError,
            ValueError,
        ):
            expires_in = INSTAGRAM_LONG_LIVED_TOKEN_DEFAULT_SECONDS

        token_expires_at = timezone.now() + timedelta(
            seconds=expires_in,
        )

        # ----------------------------------------------------
        # STEP 3
        # Fetch Instagram profile
        # ----------------------------------------------------

        profile = self.client.get_profile(
            access_token=long_lived_token,
        )

        instagram_user_id = str(
            profile.get("id") or profile.get("user_id") or ""
        ).strip()

        if not instagram_user_id:
            raise InstagramIntegrationError(
                "Instagram profile did not contain a user ID."
            )

        username = str(profile.get("username") or "").strip()

        account_name = str(
            profile.get("name") or username or "Instagram Account"
        ).strip()

        profile_image = str(profile.get("profile_picture_url") or "").strip()

        # ----------------------------------------------------
        # STEP 4
        # Find existing social account
        # ----------------------------------------------------

        social_account = (
            SocialAccount.objects.select_for_update()
            .filter(
                organization=organization,
                platform=SocialPlatform.INSTAGRAM,
                platform_account_id=instagram_user_id,
                is_deleted=False,
            )
            .first()
        )

        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        if not social_account:
            social_account = SocialAccount.objects.create(
                organization=organization,
                platform=SocialPlatform.INSTAGRAM,
                platform_account_id=instagram_user_id,
                account_name=account_name,
                username=username,
                profile_image=profile_image,
                status=SocialAccountStatus.CONNECTED,
                is_valid=True,
                last_synced_at=timezone.now(),
            )

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        else:
            social_account.account_name = account_name
            social_account.username = username
            social_account.profile_image = profile_image
            social_account.status = SocialAccountStatus.CONNECTED
            social_account.is_valid = True
            social_account.last_synced_at = timezone.now()

            social_account.save(
                update_fields=[
                    "account_name",
                    "username",
                    "profile_image",
                    "status",
                    "is_valid",
                    "last_synced_at",
                    "updated_at",
                ]
            )

        # ----------------------------------------------------
        # STEP 5
        # Credential
        # ----------------------------------------------------

        encrypted_token = encrypt_token(long_lived_token)

        credential = (
            InstagramAccountCredential.objects.select_for_update()
            .filter(
                social_account=social_account,
                is_deleted=False,
            )
            .first()
        )

        if credential:
            credential.encrypted_access_token = encrypted_token
            credential.token_expires_at = token_expires_at
            credential.status = InstagramCredentialStatus.ACTIVE
            credential.last_verified_at = timezone.now()

            credential.save(
                update_fields=[
                    "encrypted_access_token",
                    "token_expires_at",
                    "status",
                    "last_verified_at",
                    "updated_at",
                ]
            )

        else:
            InstagramAccountCredential.objects.create(
                social_account=social_account,
                encrypted_access_token=encrypted_token,
                token_expires_at=token_expires_at,
                status=InstagramCredentialStatus.ACTIVE,
                last_verified_at=timezone.now(),
            )

        return social_account

    # ========================================================
    # REFRESH
    # ========================================================

    @transaction.atomic
    def refresh_credential(
        self,
        *,
        credential,
    ):
        from .crypto import decrypt_token

        access_token = decrypt_token(credential.encrypted_access_token)

        token_data = self.client.refresh_long_lived_token(
            access_token=access_token,
        )

        new_token = token_data.get("access_token")

        if not new_token:
            raise InstagramIntegrationError(
                "Instagram did not return a refreshed access token."
            )

        expires_in = token_data.get(
            "expires_in",
            INSTAGRAM_LONG_LIVED_TOKEN_DEFAULT_SECONDS,
        )

        try:
            expires_in = int(expires_in)
        except (
            TypeError,
            ValueError,
        ):
            expires_in = INSTAGRAM_LONG_LIVED_TOKEN_DEFAULT_SECONDS

        credential.encrypted_access_token = encrypt_token(new_token)

        credential.token_expires_at = timezone.now() + timedelta(
            seconds=expires_in,
        )

        credential.status = InstagramCredentialStatus.ACTIVE

        credential.last_verified_at = timezone.now()

        credential.save(
            update_fields=[
                "encrypted_access_token",
                "token_expires_at",
                "status",
                "last_verified_at",
                "updated_at",
            ]
        )

        return credential


class InstagramCredentialService:
    """
    Handles lifecycle operations for Instagram account credentials.

    Provider credential state is intentionally kept separate from
    SocialAccount state.

    Responsibilities:
        - Revoke local credential usage on disconnect.
        - Preserve credential history.
        - Never delete the SocialAccount.
    """

    @staticmethod
    @transaction.atomic
    def revoke_for_disconnect(
        *,
        social_account,
    ):
        """
        Revoke the locally stored Instagram credential when the
        user disconnects the Instagram account.

        The encrypted token is intentionally retained for audit/
        historical purposes, but it can no longer be resolved for
        API usage because the credential status becomes REVOKED.
        """

        credential = (
            InstagramAccountCredential.objects.select_for_update()
            .filter(
                social_account=social_account,
                is_deleted=False,
            )
            .first()
        )

        if credential:
            credential.status = InstagramCredentialStatus.REVOKED

            credential.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return credential
