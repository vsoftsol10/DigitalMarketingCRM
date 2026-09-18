# reconct change

# from datetime import timedelta
# from urllib.parse import urlencode

# from django.db import transaction
# from django.utils import timezone

# from apps.social_accounts.models import (
#     SocialAccount,
#     SocialAccountStatus,
#     SocialPlatform,
# )

# from .client import InstagramAPIClient
# from .crypto import encrypt_token
# from .exceptions import InstagramIntegrationError
# from .models import (
#     InstagramAccountCredential,
#     InstagramCredentialStatus,
# )
# from .oauth import (
#     create_oauth_nonce,
#     create_oauth_state,
# )


# class InstagramOAuthService:
#     """
#     Handles the server-side Instagram Login OAuth flow.

#     Responsibilities:
#         - Build the Instagram authorization URL.
#         - Validate organization ownership.
#         - Exchange the authorization code.
#         - Exchange the short-lived token for a long-lived token.
#         - Validate the provider token response.
#         - Fetch the Instagram profile.
#         - Create or update the SocialAccount.
#         - Create or update the Instagram credential.

#     Token lifecycle maintenance is intentionally NOT handled
#     here. Automatic token refresh belongs to
#     InstagramTokenLifecycleService.
#     """

#     def __init__(self):
#         self.client = InstagramAPIClient()

#     # ========================================================
#     # AUTHORIZATION URL
#     # ========================================================

#     def build_authorization_url(
#         self,
#         *,
#         organization,
#         user,
#     ):
#         if organization.created_by_id != user.id:
#             raise InstagramIntegrationError(
#                 "You do not have access to this organization."
#             )

#         nonce = create_oauth_nonce()

#         state = create_oauth_state(
#             organization_id=organization.organization_id,
#             user_id=user.pk,
#             nonce=nonce,
#         )

#         params = {
#             "client_id": self.client.client_id,
#             "redirect_uri": self.client.redirect_uri,
#             "response_type": "code",
#             "scope": "instagram_business_basic",
#             "state": state,
#         }

#         return "https://www.instagram.com/oauth/authorize?" f"{urlencode(params)}"

#     # ========================================================
#     # COMPLETE CALLBACK
#     # ========================================================

#     @transaction.atomic
#     def handle_callback(
#         self,
#         *,
#         code,
#         organization,
#         user,
#     ):
#         """
#         Complete Instagram OAuth and persist the resulting
#         long-lived credential.

#         The provider's expires_in value is treated as the
#         authoritative token lifetime.

#         We intentionally do NOT invent a fallback expiry when
#         Instagram does not return a valid expires_in value.
#         """

#         if organization.created_by_id != user.id:
#             raise InstagramIntegrationError(
#                 "You do not have access to this organization."
#             )

#         # ----------------------------------------------------
#         # STEP 1
#         # Authorization code -> short-lived token
#         # ----------------------------------------------------

#         short_token_data = self.client.exchange_code(
#             code=code,
#         )

#         short_lived_token = short_token_data.get(
#             "access_token",
#         )

#         if not short_lived_token:
#             raise InstagramIntegrationError("Instagram did not return an access token.")

#         # ----------------------------------------------------
#         # STEP 2
#         # Short-lived token -> long-lived token
#         # ----------------------------------------------------

#         long_token_data = self.client.exchange_long_lived_token(
#             short_lived_token=short_lived_token,
#         )

#         long_lived_token = long_token_data.get(
#             "access_token",
#         )

#         if not long_lived_token:
#             raise InstagramIntegrationError(
#                 "Instagram did not return a long-lived access token."
#             )

#         # ----------------------------------------------------
#         # Provider expiry is mandatory for our lifecycle.
#         #
#         # Do NOT silently assume 60 days if the provider does
#         # not return expires_in.
#         # ----------------------------------------------------

#         expires_in = long_token_data.get(
#             "expires_in",
#         )

#         try:
#             expires_in = int(expires_in)
#         except (
#             TypeError,
#             ValueError,
#         ) as exc:
#             raise InstagramIntegrationError(
#                 "Instagram did not return a valid token expiry."
#             ) from exc

#         if expires_in <= 0:
#             raise InstagramIntegrationError(
#                 "Instagram returned an invalid token expiry."
#             )

#         token_expires_at = timezone.now() + timedelta(
#             seconds=expires_in,
#         )

#         # ----------------------------------------------------
#         # STEP 3
#         # Fetch Instagram profile
#         # ----------------------------------------------------

#         profile = self.client.get_profile(
#             access_token=long_lived_token,
#         )

#         instagram_user_id = str(
#             profile.get("id") or profile.get("user_id") or ""
#         ).strip()

#         if not instagram_user_id:
#             raise InstagramIntegrationError(
#                 "Instagram profile did not contain a user ID."
#             )

#         username = str(profile.get("username") or "").strip()

#         account_name = str(
#             profile.get("name") or username or "Instagram Account"
#         ).strip()

#         profile_image = str(profile.get("profile_picture_url") or "").strip()

#         # ----------------------------------------------------
#         # STEP 4
#         # Find existing SocialAccount
#         # ----------------------------------------------------

#         social_account = (
#             SocialAccount.objects.select_for_update()
#             .filter(
#                 organization=organization,
#                 platform=SocialPlatform.INSTAGRAM,
#                 platform_account_id=instagram_user_id,
#                 is_deleted=False,
#             )
#             .first()
#         )

#         # ----------------------------------------------------
#         # CREATE
#         # ----------------------------------------------------

#         if not social_account:
#             social_account = SocialAccount.objects.create(
#                 organization=organization,
#                 platform=SocialPlatform.INSTAGRAM,
#                 platform_account_id=instagram_user_id,
#                 account_name=account_name,
#                 username=username,
#                 profile_image=profile_image,
#                 status=SocialAccountStatus.CONNECTED,
#                 is_valid=True,
#                 last_synced_at=timezone.now(),
#             )

#         # ----------------------------------------------------
#         # UPDATE
#         # ----------------------------------------------------

#         else:
#             social_account.account_name = account_name
#             social_account.username = username
#             social_account.profile_image = profile_image
#             social_account.status = SocialAccountStatus.CONNECTED
#             social_account.is_valid = True
#             social_account.last_synced_at = timezone.now()

#             social_account.save(
#                 update_fields=[
#                     "account_name",
#                     "username",
#                     "profile_image",
#                     "status",
#                     "is_valid",
#                     "last_synced_at",
#                     "updated_at",
#                 ],
#             )

#         # ----------------------------------------------------
#         # STEP 5
#         # Encrypt and persist credential
#         # ----------------------------------------------------

#         encrypted_token = encrypt_token(
#             long_lived_token,
#         )

#         credential = (
#             InstagramAccountCredential.objects.select_for_update()
#             .filter(
#                 social_account=social_account,
#                 is_deleted=False,
#             )
#             .first()
#         )

#         if credential:
#             credential.encrypted_access_token = encrypted_token
#             credential.token_expires_at = token_expires_at
#             credential.status = InstagramCredentialStatus.ACTIVE
#             credential.last_verified_at = timezone.now()

#             credential.save(
#                 update_fields=[
#                     "encrypted_access_token",
#                     "token_expires_at",
#                     "status",
#                     "last_verified_at",
#                     "updated_at",
#                 ],
#             )

#         else:
#             InstagramAccountCredential.objects.create(
#                 social_account=social_account,
#                 encrypted_access_token=encrypted_token,
#                 token_expires_at=token_expires_at,
#                 status=InstagramCredentialStatus.ACTIVE,
#                 last_verified_at=timezone.now(),
#             )

#         return social_account


# class InstagramCredentialService:
#     """
#     Handles local lifecycle operations for Instagram credentials.

#     Responsibilities:
#         - Revoke local credential usage on disconnect.
#         - Preserve credential history.
#         - Never automatically restore a manually revoked
#           credential.
#         - Keep the SocialAccount itself intact.
#     """

#     @staticmethod
#     @transaction.atomic
#     def revoke_for_disconnect(
#         *,
#         social_account,
#     ):
#         """
#         Revoke the locally stored Instagram credential when
#         the user disconnects the account.

#         The encrypted token is intentionally retained for
#         historical/audit purposes.

#         Because the credential status becomes REVOKED,
#         automatic token maintenance will not use it.
#         """

#         credential = (
#             InstagramAccountCredential.objects.select_for_update()
#             .filter(
#                 social_account=social_account,
#                 is_deleted=False,
#             )
#             .first()
#         )

#         if credential:
#             credential.status = InstagramCredentialStatus.REVOKED

#             credential.save(
#                 update_fields=[
#                     "status",
#                     "updated_at",
#                 ],
#             )

#         return credential

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
from .constants import INSTAGRAM_OAUTH_SCOPES
from .crypto import encrypt_token
from .exceptions import InstagramIntegrationError
from .models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
)
from .oauth import (
    create_oauth_nonce,
    create_oauth_state,
    OAUTH_ACTION_CONNECT,
    OAUTH_ACTION_RECONNECT,
)


class InstagramOAuthService:
    """
    Handles the server-side Instagram Login OAuth flow.

    Responsibilities:
        - Build the Instagram authorization URL.
        - Validate organization ownership.
        - Exchange the authorization code.
        - Exchange the short-lived token for a long-lived token.
        - Validate the provider token response.
        - Fetch the Instagram profile.
        - Create or update the SocialAccount.
        - Create or update the Instagram credential.

    Token lifecycle maintenance is intentionally NOT handled
    here. Automatic token refresh belongs to
    InstagramTokenLifecycleService.
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
            "scope": ",".join(INSTAGRAM_OAUTH_SCOPES),
            "state": state,
        }

        return "https://www.instagram.com/oauth/authorize?" f"{urlencode(params)}"

        # ========================================================

    # RECONNECT EXISTING INSTAGRAM ACCOUNT
    # ========================================================

    @transaction.atomic
    def reconnect_existing_account(
        self,
        *,
        code,
        organization,
        user,
        social_account_id,
    ):
        """
        Reconnect an existing Instagram SocialAccount.

        The OAuth flow must resolve to the exact Instagram
        account represented by social_account_id.

        A different Instagram account is never allowed to
        silently replace the existing connection.
        """

        if organization.created_by_id != user.id:
            raise InstagramIntegrationError(
                "You do not have access to this organization."
            )

        if not social_account_id:
            raise InstagramIntegrationError(
                "Instagram SocialAccount ID is required for reconnect."
            )

        # ----------------------------------------------------
        # STEP 1
        # Find and lock the existing SocialAccount
        # ----------------------------------------------------

        social_account = (
            SocialAccount.objects.select_for_update()
            .filter(
                id=social_account_id,
                organization=organization,
                platform=SocialPlatform.INSTAGRAM,
                is_deleted=False,
            )
            .first()
        )

        if not social_account:
            raise InstagramIntegrationError(
                "The Instagram account selected for reconnect was not found."
            )

        target_instagram_user_id = str(social_account.platform_account_id or "").strip()

        if not target_instagram_user_id:
            raise InstagramIntegrationError("The Instagram account ID is missing.")

        # ----------------------------------------------------
        # STEP 2
        # Authorization code -> short-lived token
        # ----------------------------------------------------

        short_token_data = self.client.exchange_code(
            code=code,
        )

        short_lived_token = str(short_token_data.get("access_token") or "").strip()

        if not short_lived_token:
            raise InstagramIntegrationError("Instagram did not return an access token.")

        # ----------------------------------------------------
        # STEP 3
        # Short-lived -> long-lived token
        # ----------------------------------------------------

        long_token_data = self.client.exchange_long_lived_token(
            short_lived_token=short_lived_token,
        )

        long_lived_token = str(long_token_data.get("access_token") or "").strip()

        if not long_lived_token:
            raise InstagramIntegrationError(
                "Instagram did not return a long-lived access token."
            )

        # ----------------------------------------------------
        # STEP 4
        # Validate provider expiry
        # ----------------------------------------------------

        expires_in = long_token_data.get("expires_in")

        try:
            expires_in = int(expires_in)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise InstagramIntegrationError(
                "Instagram did not return a valid token expiry."
            ) from exc

        if expires_in <= 0:
            raise InstagramIntegrationError(
                "Instagram returned an invalid token expiry."
            )

        token_expires_at = timezone.now() + timedelta(
            seconds=expires_in,
        )

        # ----------------------------------------------------
        # STEP 5
        # Fetch the Instagram profile using the NEW token
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

        # ----------------------------------------------------
        # CRITICAL SECURITY CHECK
        #
        # OAuth must resolve to the exact account the user
        # selected for reconnect.
        # ----------------------------------------------------

        if instagram_user_id != target_instagram_user_id:
            raise InstagramIntegrationError(
                "The authorized Instagram account does not match "
                "the account selected for reconnect."
            )

        username = str(profile.get("username") or "").strip()

        account_name = str(
            profile.get("name") or username or "Instagram Account"
        ).strip()

        profile_image = str(profile.get("profile_picture_url") or "").strip()

        # ----------------------------------------------------
        # STEP 6
        # Update existing SocialAccount
        # ----------------------------------------------------

        now = timezone.now()

        social_account.account_name = account_name
        social_account.username = username
        social_account.profile_image = profile_image
        social_account.status = SocialAccountStatus.CONNECTED
        social_account.is_valid = True
        social_account.last_synced_at = now

        social_account.save(
            update_fields=[
                "account_name",
                "username",
                "profile_image",
                "status",
                "is_valid",
                "last_synced_at",
                "updated_at",
            ],
        )

        # ----------------------------------------------------
        # STEP 7
        # Replace the existing credential
        # ----------------------------------------------------

        encrypted_token = encrypt_token(
            long_lived_token,
        )

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
            credential.last_verified_at = now

            credential.save(
                update_fields=[
                    "encrypted_access_token",
                    "token_expires_at",
                    "status",
                    "last_verified_at",
                    "updated_at",
                ],
            )

        else:
            InstagramAccountCredential.objects.create(
                social_account=social_account,
                encrypted_access_token=encrypted_token,
                token_expires_at=token_expires_at,
                status=InstagramCredentialStatus.ACTIVE,
                last_verified_at=now,
            )

        return social_account

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
        """
        Complete Instagram OAuth and persist the resulting
        long-lived credential.

        The provider's expires_in value is treated as the
        authoritative token lifetime.

        We intentionally do NOT invent a fallback expiry when
        Instagram does not return a valid expires_in value.
        """

        if organization.created_by_id != user.id:
            raise InstagramIntegrationError(
                "You do not have access to this organization."
            )

        # ----------------------------------------------------
        # STEP 1
        # Authorization code -> short-lived token
        # ----------------------------------------------------

        short_token_data = self.client.exchange_code(
            code=code,
        )

        short_lived_token = short_token_data.get(
            "access_token",
        )

        if not short_lived_token:
            raise InstagramIntegrationError("Instagram did not return an access token.")

        # ----------------------------------------------------
        # STEP 2
        # Short-lived token -> long-lived token
        # ----------------------------------------------------

        long_token_data = self.client.exchange_long_lived_token(
            short_lived_token=short_lived_token,
        )

        long_lived_token = long_token_data.get(
            "access_token",
        )

        if not long_lived_token:
            raise InstagramIntegrationError(
                "Instagram did not return a long-lived access token."
            )

        # ----------------------------------------------------
        # Provider expiry is mandatory for our lifecycle.
        #
        # Do NOT silently assume 60 days if the provider does
        # not return expires_in.
        # ----------------------------------------------------

        expires_in = long_token_data.get(
            "expires_in",
        )

        try:
            expires_in = int(expires_in)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise InstagramIntegrationError(
                "Instagram did not return a valid token expiry."
            ) from exc

        if expires_in <= 0:
            raise InstagramIntegrationError(
                "Instagram returned an invalid token expiry."
            )

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
        # Find existing SocialAccount
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
                ],
            )

        # ----------------------------------------------------
        # STEP 5
        # Encrypt and persist credential
        # ----------------------------------------------------

        encrypted_token = encrypt_token(
            long_lived_token,
        )

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
                ],
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


class InstagramCredentialService:
    """
    Handles local lifecycle operations for Instagram credentials.

    Responsibilities:
        - Revoke local credential usage on disconnect.
        - Preserve credential history.
        - Never automatically restore a manually revoked
          credential.
        - Keep the SocialAccount itself intact.
    """

    @staticmethod
    @transaction.atomic
    def revoke_for_disconnect(
        *,
        social_account,
    ):
        """
        Revoke the locally stored Instagram credential when
        the user disconnects the account.

        The encrypted token is intentionally retained for
        historical/audit purposes.

        Because the credential status becomes REVOKED,
        automatic token maintenance will not use it.
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
                ],
            )

        return credential
