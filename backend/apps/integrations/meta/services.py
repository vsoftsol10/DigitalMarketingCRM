# import logging
# from dataclasses import dataclass
# from datetime import timedelta
# from typing import List, Optional, Set

# from django.conf import settings
# from django.db import transaction
# from django.utils import timezone

# from apps.social_accounts.models import (
#     SocialAccount,
#     SocialAccountStatus,
#     SocialConnection,
#     SocialConnectionProvider,
#     SocialConnectionStatus,
#     SocialPlatform,
# )

# from .client import MetaAPIClient
# from .crypto import encrypt_token
# from .exceptions import MetaAPIError
# from .models import (
#     MetaAccountCredential,
#     MetaCredentialStatus,
#     MetaCredentialType,
#     MetaSocialAccountLink,
# )

# logger = logging.getLogger(__name__)


# # ============================================================
# # DATA STRUCTURES
# # ============================================================


# @dataclass
# class MetaAccountData:
#     platform: str
#     platform_account_id: str
#     account_name: str
#     username: str = ""
#     profile_image: str = ""
#     access_token: str = ""
#     credential_type: str = MetaCredentialType.PAGE
#     linked_facebook_page_platform_account_id: str = ""


# @dataclass
# class MetaDiscoveryResult:
#     provider_user_id: str
#     accounts: List[MetaAccountData]


# # ============================================================
# # META ACCOUNT DISCOVERY
# # ============================================================


# class MetaAccountDiscoveryService:
#     """
#     Discover the Facebook Page selected through the Meta
#     Facebook Login for Business flow and its linked
#     Instagram Professional account.

#     Important behavior:

#         Meta authorization
#             ↓
#         Page asset selection
#             ↓
#         /me/accounts
#             ↓
#         selected Page
#             ↓
#         Page access token
#             ↓
#         linked Instagram Professional account
#     """

#     def __init__(
#         self,
#         access_token: str,
#     ):
#         self.access_token = access_token
#         self.client = MetaAPIClient()

#     # ========================================================
#     # SELECTED PAGE IDS
#     # ========================================================

#     def _get_selected_page_ids_from_token(self) -> Set[str]:
#         """
#         Inspect Meta token granular scopes for asset-specific
#         Page target IDs.

#         For Facebook Login for Business, Meta may provide
#         target_ids for granular permissions.

#         We never guess a Page from the list when Meta has
#         explicitly provided asset-specific target IDs.
#         """

#         try:
#             token_data = self.client.diagnose_token(
#                 access_token=self.access_token,
#             )

#         except MetaAPIError:
#             logger.warning(
#                 "Unable to debug Meta token while determining " "selected Page.",
#                 exc_info=True,
#             )

#             return set()

#         granular_scopes = token_data.get("granular_scopes") or []

#         selected_page_ids: Set[str] = set()

#         for item in granular_scopes:
#             if not isinstance(item, dict):
#                 continue

#             scope = item.get("scope")

#             if scope != "pages_show_list":
#                 continue

#             target_ids = item.get("target_ids") or []

#             for target_id in target_ids:
#                 if target_id:
#                     selected_page_ids.add(
#                         str(target_id),
#                     )

#         return selected_page_ids

#     # ========================================================
#     # PAGE FILTERING
#     # ========================================================

#     @staticmethod
#     def _select_page(
#         *,
#         pages: list,
#         selected_page_ids: Set[str],
#     ) -> dict:
#         """
#         Select exactly one Page.

#         Rules:

#         1. If Meta supplied asset-specific target IDs,
#            exactly one matching Page must exist.

#         2. If Meta did not supply target IDs:
#            a single Page is accepted.
#            multiple Pages are rejected.

#         We never silently choose the first Page.
#         """

#         if not pages:
#             raise MetaAPIError(
#                 "Meta did not return any Facebook Pages " "for this authorization.",
#             )

#         if selected_page_ids:
#             matching_pages = [
#                 page
#                 for page in pages
#                 if str(
#                     page.get("id") or "",
#                 )
#                 in selected_page_ids
#             ]

#             if len(matching_pages) == 1:
#                 return matching_pages[0]

#             if len(matching_pages) > 1:
#                 raise MetaAPIError(
#                     "Meta returned multiple selected Facebook "
#                     "Pages. Please authorize only one Page "
#                     "for this connection.",
#                 )

#             raise MetaAPIError(
#                 "The Facebook Page selected in Meta could not "
#                 "be resolved from the returned Page assets.",
#             )

#         if len(pages) == 1:
#             return pages[0]

#         raise MetaAPIError(
#             "Meta returned multiple Facebook Pages, but the "
#             "authorization response did not identify a unique "
#             "selected Page. No accounts were connected.",
#         )

#     # ========================================================
#     # DISCOVER
#     # ========================================================

#     def discover_accounts(self) -> MetaDiscoveryResult:
#         # ----------------------------------------------------
#         # META USER
#         # ----------------------------------------------------

#         current_user = self.client.get_current_user(
#             access_token=self.access_token,
#         )

#         provider_user_id = str(
#             current_user.get("id") or "",
#         ).strip()

#         if not provider_user_id:
#             raise MetaAPIError(
#                 "Meta did not return a provider user ID.",
#             )

#         # ----------------------------------------------------
#         # PAGES
#         # ----------------------------------------------------

#         pages = self.client.get_pages(
#             access_token=self.access_token,
#         )

#         selected_page_ids = self._get_selected_page_ids_from_token()

#         page = self._select_page(
#             pages=pages,
#             selected_page_ids=selected_page_ids,
#         )

#         # ----------------------------------------------------
#         # PAGE DATA
#         # ----------------------------------------------------

#         page_id = str(
#             page.get("id") or "",
#         ).strip()

#         page_name = str(
#             page.get("name") or "",
#         ).strip()

#         page_access_token = str(
#             page.get("access_token") or "",
#         ).strip()

#         if not page_id:
#             raise MetaAPIError(
#                 "Meta returned a Facebook Page without an ID.",
#             )

#         if not page_access_token:
#             raise MetaAPIError(
#                 "Meta returned the Facebook Page without a " "Page access token.",
#             )

#         accounts: List[MetaAccountData] = []

#         # ----------------------------------------------------
#         # FACEBOOK PAGE
#         # ----------------------------------------------------

#         accounts.append(
#             MetaAccountData(
#                 platform=SocialPlatform.FACEBOOK,
#                 platform_account_id=page_id,
#                 account_name=page_name or page_id,
#                 access_token=page_access_token,
#                 credential_type=MetaCredentialType.PAGE,
#             )
#         )

#         # ----------------------------------------------------
#         # LINKED INSTAGRAM
#         # ----------------------------------------------------

#         instagram_business_account = page.get("instagram_business_account") or {}

#         instagram_id = str(
#             instagram_business_account.get("id") or "",
#         ).strip()

#         if instagram_id:
#             instagram_profile = {}

#             try:
#                 instagram_profile = self.client.get_instagram_profile(
#                     instagram_account_id=instagram_id,
#                     access_token=page_access_token,
#                 )

#             except MetaAPIError:
#                 # The Page itself can still be connected even
#                 # if profile metadata retrieval temporarily
#                 # fails. We retain the Instagram ID and use
#                 # safe fallback display values.
#                 logger.warning(
#                     "Unable to fetch Instagram profile " "for Instagram ID %s.",
#                     instagram_id,
#                     exc_info=True,
#                 )

#             instagram_username = str(
#                 instagram_profile.get("username") or "",
#             ).strip()

#             instagram_name = str(
#                 instagram_profile.get("name") or instagram_username or instagram_id,
#             ).strip()

#             instagram_profile_image = str(
#                 instagram_profile.get(
#                     "profile_picture_url",
#                 )
#                 or "",
#             ).strip()

#             accounts.append(
#                 MetaAccountData(
#                     platform=SocialPlatform.INSTAGRAM,
#                     platform_account_id=instagram_id,
#                     account_name=instagram_name,
#                     username=instagram_username,
#                     profile_image=instagram_profile_image,
#                     access_token="",
#                     credential_type=MetaCredentialType.PAGE,
#                     linked_facebook_page_platform_account_id=page_id,
#                 )
#             )

#         return MetaDiscoveryResult(
#             provider_user_id=provider_user_id,
#             accounts=accounts,
#         )


# # ============================================================
# # META SOCIAL ACCOUNT PERSISTENCE
# # ============================================================


# class MetaSocialAccountService:
#     """
#     Persist a Meta OAuth authorization and its selected
#     Facebook Page / linked Instagram account.

#     All database writes happen inside one transaction.
#     """

#     def __init__(
#         self,
#         organization,
#         user,
#     ):
#         self.organization = organization
#         self.user = user

#     # ========================================================
#     # CONNECTION
#     # ========================================================

#     def _get_or_create_connection(
#         self,
#         *,
#         provider_user_id: str,
#     ):
#         connection = (
#             SocialConnection.objects.filter(
#                 organization=self.organization,
#                 provider=SocialConnectionProvider.META,
#                 provider_user_id=str(
#                     provider_user_id,
#                 ),
#             )
#             .order_by("-is_deleted", "-created_at")
#             .first()
#         )

#         now = timezone.now()

#         if connection:
#             update_fields = []

#             if connection.is_deleted:
#                 connection.is_deleted = False
#                 connection.deleted_at = None
#                 update_fields.extend(
#                     [
#                         "is_deleted",
#                         "deleted_at",
#                     ]
#                 )

#             if connection.status != SocialConnectionStatus.ACTIVE:
#                 connection.status = SocialConnectionStatus.ACTIVE
#                 update_fields.append("status")

#             connection.last_synced_at = now
#             update_fields.append("last_synced_at")

#             if update_fields:
#                 update_fields.append("updated_at")
#                 connection.save(
#                     update_fields=update_fields,
#                 )

#             return connection

#         return SocialConnection.objects.create(
#             organization=self.organization,
#             provider=SocialConnectionProvider.META,
#             provider_user_id=str(
#                 provider_user_id,
#             ),
#             status=SocialConnectionStatus.ACTIVE,
#             last_synced_at=now,
#         )

#     # ========================================================
#     # USER CREDENTIAL
#     # ========================================================

#     def _save_user_credential(
#         self,
#         *,
#         connection,
#         user_access_token: str,
#         token_expires_at=None,
#     ):
#         credential = (
#             MetaAccountCredential.objects.filter(
#                 social_connection=connection,
#                 credential_type=MetaCredentialType.USER,
#             )
#             .order_by("-created_at")
#             .first()
#         )

#         encrypted_token = encrypt_token(
#             user_access_token,
#         )

#         defaults = {
#             "social_account": None,
#             "access_token": encrypted_token,
#             "token_expires_at": token_expires_at,
#             "status": MetaCredentialStatus.ACTIVE,
#             "last_verified_at": timezone.now(),
#             "is_deleted": False,
#             "deleted_at": None,
#         }

#         if credential:
#             for field, value in defaults.items():
#                 setattr(
#                     credential,
#                     field,
#                     value,
#                 )

#             credential.save()

#             return credential

#         return MetaAccountCredential.objects.create(
#             social_connection=connection,
#             social_account=None,
#             credential_type=MetaCredentialType.USER,
#             **{
#                 key: value
#                 for key, value in defaults.items()
#                 if key
#                 not in {
#                     "social_account",
#                 }
#             },
#         )

#     # ========================================================
#     # SOCIAL ACCOUNT
#     # ========================================================

#     def _get_or_create_social_account(
#         self,
#         *,
#         account_data: MetaAccountData,
#         connection,
#     ):
#         now = timezone.now()

#         social_account = (
#             SocialAccount.objects.filter(
#                 organization=self.organization,
#                 platform=account_data.platform,
#                 platform_account_id=(account_data.platform_account_id),
#             )
#             .order_by("-is_deleted", "-created_at")
#             .first()
#         )

#         if social_account:
#             social_account.organization = self.organization
#             social_account.connection = connection
#             social_account.account_name = account_data.account_name
#             social_account.username = account_data.username
#             social_account.profile_image = account_data.profile_image
#             social_account.status = SocialAccountStatus.CONNECTED
#             social_account.is_valid = True
#             social_account.last_synced_at = now
#             social_account.is_deleted = False
#             social_account.deleted_at = None

#             social_account.save()

#             return social_account

#         return SocialAccount.objects.create(
#             organization=self.organization,
#             connection=connection,
#             platform=account_data.platform,
#             platform_account_id=(account_data.platform_account_id),
#             account_name=account_data.account_name,
#             username=account_data.username,
#             profile_image=account_data.profile_image,
#             status=SocialAccountStatus.CONNECTED,
#             is_valid=True,
#             last_synced_at=now,
#         )

#     # ========================================================
#     # PAGE CREDENTIAL
#     # ========================================================

#     def _save_page_credential(
#         self,
#         *,
#         social_account,
#         page_access_token: str,
#     ):
#         if not page_access_token:
#             raise MetaAPIError(
#                 "Facebook Page access token is missing.",
#             )

#         credential = (
#             MetaAccountCredential.objects.filter(
#                 social_account=social_account,
#                 credential_type=MetaCredentialType.PAGE,
#             )
#             .order_by("-created_at")
#             .first()
#         )

#         encrypted_token = encrypt_token(
#             page_access_token,
#         )

#         if credential:
#             credential.access_token = encrypted_token
#             credential.social_connection = None
#             credential.token_expires_at = None
#             credential.status = MetaCredentialStatus.ACTIVE
#             credential.last_verified_at = timezone.now()
#             credential.is_deleted = False
#             credential.deleted_at = None
#             credential.save()

#             return credential

#         return MetaAccountCredential.objects.create(
#             social_account=social_account,
#             social_connection=None,
#             credential_type=MetaCredentialType.PAGE,
#             access_token=encrypted_token,
#             token_expires_at=None,
#             status=MetaCredentialStatus.ACTIVE,
#             last_verified_at=timezone.now(),
#         )

#     # ========================================================
#     # PAGE ↔ INSTAGRAM LINK
#     # ========================================================

#     def _save_page_instagram_link(
#         self,
#         *,
#         facebook_page,
#         instagram_account,
#     ):
#         link = (
#             MetaSocialAccountLink.objects.filter(
#                 organization=self.organization,
#                 facebook_page=facebook_page,
#                 instagram_account=instagram_account,
#             )
#             .order_by("-is_deleted", "-created_at")
#             .first()
#         )

#         if link:
#             link.is_deleted = False
#             link.deleted_at = None
#             link.save(
#                 update_fields=[
#                     "is_deleted",
#                     "deleted_at",
#                     "updated_at",
#                 ]
#             )

#             return link

#         return MetaSocialAccountLink.objects.create(
#             organization=self.organization,
#             facebook_page=facebook_page,
#             instagram_account=instagram_account,
#         )

#     # ========================================================
#     # COMPLETE SYNC
#     # ========================================================

#     @transaction.atomic
#     def sync_connection_and_accounts(
#         self,
#         *,
#         provider_user_id: str,
#         user_access_token: str,
#         accounts: List[MetaAccountData],
#         token_expires_at=None,
#     ):
#         if not provider_user_id:
#             raise MetaAPIError(
#                 "Meta provider user ID is required.",
#             )

#         if not user_access_token:
#             raise MetaAPIError(
#                 "Meta access token is required.",
#             )

#         if not accounts:
#             raise MetaAPIError(
#                 "Meta did not return any social accounts.",
#             )

#         connection = self._get_or_create_connection(
#             provider_user_id=provider_user_id,
#         )

#         self._save_user_credential(
#             connection=connection,
#             user_access_token=user_access_token,
#             token_expires_at=token_expires_at,
#         )

#         facebook_accounts = {}
#         instagram_accounts = {}
#         synced_accounts = []

#         # ----------------------------------------------------
#         # CREATE / UPDATE ACCOUNTS
#         # ----------------------------------------------------

#         for account_data in accounts:
#             social_account = self._get_or_create_social_account(
#                 account_data=account_data,
#                 connection=connection,
#             )

#             if account_data.platform == SocialPlatform.FACEBOOK:
#                 facebook_accounts[account_data.platform_account_id] = social_account

#                 self._save_page_credential(
#                     social_account=social_account,
#                     page_access_token=account_data.access_token,
#                 )

#             elif account_data.platform == SocialPlatform.INSTAGRAM:
#                 instagram_accounts[account_data.platform_account_id] = social_account

#             synced_accounts.append(
#                 social_account,
#             )

#         # ----------------------------------------------------
#         # PAGE → INSTAGRAM
#         # ----------------------------------------------------

#         for account_data in accounts:
#             if account_data.platform != SocialPlatform.INSTAGRAM:
#                 continue

#             linked_page_id = account_data.linked_facebook_page_platform_account_id

#             if not linked_page_id:
#                 continue

#             facebook_page = facebook_accounts.get(
#                 linked_page_id,
#             )

#             instagram_account = instagram_accounts.get(
#                 account_data.platform_account_id,
#             )

#             if not facebook_page or not instagram_account:
#                 raise MetaAPIError(
#                     "Meta returned an Instagram account without "
#                     "a valid linked Facebook Page.",
#                 )

#             self._save_page_instagram_link(
#                 facebook_page=facebook_page,
#                 instagram_account=instagram_account,
#             )

#         connection.status = SocialConnectionStatus.ACTIVE
#         connection.last_synced_at = timezone.now()

#         connection.save(
#             update_fields=[
#                 "status",
#                 "last_synced_at",
#                 "updated_at",
#             ]
#         )

#         return (
#             connection,
#             synced_accounts,
#         )


# # ============================================================
# # META OAUTH SERVICE
# # ============================================================


# class MetaOAuthService:
#     """
#     Complete Meta OAuth orchestration.

#     Flow:

#         authorization code
#             ↓
#         access token
#             ↓
#         Meta account discovery
#             ↓
#         atomic persistence
#     """

#     def __init__(self):
#         self.client = MetaAPIClient()

#     # ========================================================
#     # PREPARE OAUTH
#     # ========================================================

#     def prepare_oauth(
#         self,
#         *,
#         code: str,
#         organization,
#         user,
#     ):
#         if not organization:
#             raise MetaAPIError(
#                 "Organization is required.",
#             )

#         if not user:
#             raise MetaAPIError(
#                 "Authenticated user is required.",
#             )

#         if not settings.META_APP_ID:
#             raise MetaAPIError(
#                 "META_APP_ID is not configured.",
#             )

#         if not settings.META_APP_SECRET:
#             raise MetaAPIError(
#                 "META_APP_SECRET is not configured.",
#             )

#         if not settings.META_OAUTH_REDIRECT_URI:
#             raise MetaAPIError(
#                 "META_OAUTH_REDIRECT_URI is not configured.",
#             )

#         # ----------------------------------------------------
#         # AUTHORIZATION CODE → ACCESS TOKEN
#         # ----------------------------------------------------

#         token_response = self.client.exchange_code_for_access_token(
#             code=code,
#         )

#         access_token = str(
#             token_response.get("access_token") or "",
#         ).strip()

#         if not access_token:
#             raise MetaAPIError(
#                 "Meta did not return an access token.",
#             )

#         # Meta may return expires_in for some token types.
#         expires_in = token_response.get(
#             "expires_in",
#         )

#         token_expires_at: Optional[object] = None

#         if expires_in:
#             try:
#                 expires_in_seconds = int(
#                     expires_in,
#                 )

#                 if expires_in_seconds > 0:
#                     token_expires_at = timezone.now() + timedelta(
#                         seconds=expires_in_seconds,
#                     )

#             except (
#                 TypeError,
#                 ValueError,
#             ):
#                 logger.warning(
#                     "Meta returned an invalid expires_in value.",
#                 )

#         # ----------------------------------------------------
#         # DISCOVER SELECTED PAGE + LINKED IG
#         # ----------------------------------------------------

#         discovery = MetaAccountDiscoveryService(
#             access_token=access_token,
#         ).discover_accounts()

#         # ----------------------------------------------------
#         # PERSIST EVERYTHING ATOMICALLY
#         # ----------------------------------------------------

#         social_service = MetaSocialAccountService(
#             organization=organization,
#             user=user,
#         )

#         connection, accounts = social_service.sync_connection_and_accounts(
#             provider_user_id=(discovery.provider_user_id),
#             user_access_token=access_token,
#             accounts=discovery.accounts,
#             token_expires_at=token_expires_at,
#         )

#         return {
#             "connection": connection,
#             "accounts": accounts,
#             "provider_user_id": (discovery.provider_user_id),
#         }


import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional, Set

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialConnectionStatus,
    SocialPlatform,
)

from .client import MetaAPIClient
from .crypto import encrypt_token
from .exceptions import MetaAPIError
from .models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaSocialAccountLink,
)

logger = logging.getLogger(__name__)


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class MetaAccountData:
    platform: str
    platform_account_id: str
    account_name: str
    username: str = ""
    profile_image: str = ""
    access_token: str = ""
    credential_type: str = MetaCredentialType.PAGE
    linked_facebook_page_platform_account_id: str = ""


@dataclass
class MetaDiscoveryResult:
    provider_user_id: str
    accounts: List[MetaAccountData]


# ============================================================
# META ACCOUNT DISCOVERY
# ============================================================


class MetaAccountDiscoveryService:
    """
    Discover the Facebook Page selected through the Meta
    Facebook Login for Business flow and its linked
    Instagram Professional account.

    Important behavior:

        Meta authorization
            ↓
        Page asset selection
            ↓
        /me/accounts
            ↓
        selected Page
            ↓
        Page access token
            ↓
        linked Instagram Professional account
    """

    def __init__(
        self,
        access_token: str,
    ):
        self.access_token = access_token
        self.client = MetaAPIClient()

    # ========================================================
    # SELECTED PAGE IDS
    # ========================================================

    def _get_selected_page_ids_from_token(self) -> Set[str]:
        """
        Inspect Meta token granular scopes for asset-specific
        Page target IDs.

        For Facebook Login for Business, Meta may provide
        target_ids for granular permissions.

        We never guess a Page from the list when Meta has
        explicitly provided asset-specific target IDs.
        """

        try:
            token_data = self.client.diagnose_token(
                access_token=self.access_token,
            )

        except MetaAPIError:
            logger.warning(
                "Unable to debug Meta token while determining " "selected Page.",
                exc_info=True,
            )

            return set()

        token_data = self.client.diagnose_token(
            access_token=self.access_token,
        )

        granular_scopes = token_data.get("granular_scopes") or []

        logger.warning(
            "META DEBUG TOKEN GRANULAR SCOPES: %s",
            [
                {
                    "scope": item.get("scope"),
                    "target_ids": item.get("target_ids"),
                }
                for item in granular_scopes
                if isinstance(item, dict)
            ],
        )

        selected_page_ids: Set[str] = set()

        for item in granular_scopes:
            if not isinstance(item, dict):
                continue

            scope = item.get("scope")

            if scope != "pages_show_list":
                continue

            target_ids = item.get("target_ids") or []

            for target_id in target_ids:
                if target_id:
                    selected_page_ids.add(
                        str(target_id),
                    )

        return selected_page_ids

    # ========================================================
    # PAGE FILTERING
    # ========================================================

    @staticmethod
    def _select_page(
        *,
        pages: list,
        selected_page_ids: Set[str],
    ) -> dict:
        """
        Select exactly one Page.

        Rules:

        1. If Meta supplied asset-specific target IDs,
           exactly one matching Page must exist.

        2. If Meta did not supply target IDs:
           a single Page is accepted.
           multiple Pages are rejected.

        We never silently choose the first Page.
        """

        if not pages:
            raise MetaAPIError(
                "Meta did not return any Facebook Pages " "for this authorization.",
            )

        if selected_page_ids:
            matching_pages = [
                page
                for page in pages
                if str(
                    page.get("id") or "",
                )
                in selected_page_ids
            ]

            if len(matching_pages) == 1:
                return matching_pages[0]

            if len(matching_pages) > 1:
                raise MetaAPIError(
                    "Meta returned multiple selected Facebook "
                    "Pages. Please authorize only one Page "
                    "for this connection.",
                )

            raise MetaAPIError(
                "The Facebook Page selected in Meta could not "
                "be resolved from the returned Page assets.",
            )

        if len(pages) == 1:
            return pages[0]

        raise MetaAPIError(
            "Meta returned multiple Facebook Pages, but the "
            "authorization response did not identify a unique "
            "selected Page. No accounts were connected.",
        )

    # ========================================================
    # DISCOVER
    # ========================================================

    def discover_accounts(self) -> MetaDiscoveryResult:
        # ----------------------------------------------------
        # META USER
        # ----------------------------------------------------

        current_user = self.client.get_current_user(
            access_token=self.access_token,
        )

        provider_user_id = str(
            current_user.get("id") or "",
        ).strip()

        if not provider_user_id:
            raise MetaAPIError(
                "Meta did not return a provider user ID.",
            )

        # ----------------------------------------------------
        # PAGES
        # ----------------------------------------------------

        pages = self.client.get_pages(
            access_token=self.access_token,
        )

        logger.warning(
            "META DEBUG PAGES RETURNED: %s",
            [
                {
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "has_access_token": bool(page.get("access_token")),
                    "instagram_business_account": (
                        page.get("instagram_business_account")
                    ),
                }
                for page in pages
                if isinstance(page, dict)
            ],
        )

        selected_page_ids = self._get_selected_page_ids_from_token()

        page = self._select_page(
            pages=pages,
            selected_page_ids=selected_page_ids,
        )

        # ----------------------------------------------------
        # PAGE DATA
        # ----------------------------------------------------

        page_id = str(
            page.get("id") or "",
        ).strip()

        page_name = str(
            page.get("name") or "",
        ).strip()

        page_access_token = str(
            page.get("access_token") or "",
        ).strip()

        if not page_id:
            raise MetaAPIError(
                "Meta returned a Facebook Page without an ID.",
            )

        if not page_access_token:
            raise MetaAPIError(
                "Meta returned the Facebook Page without a " "Page access token.",
            )

        accounts: List[MetaAccountData] = []

        # ----------------------------------------------------
        # FACEBOOK PAGE
        # ----------------------------------------------------

        accounts.append(
            MetaAccountData(
                platform=SocialPlatform.FACEBOOK,
                platform_account_id=page_id,
                account_name=page_name or page_id,
                access_token=page_access_token,
                credential_type=MetaCredentialType.PAGE,
            )
        )

        # ----------------------------------------------------
        # LINKED INSTAGRAM
        # ----------------------------------------------------

        instagram_business_account = page.get("instagram_business_account") or {}

        instagram_id = str(
            instagram_business_account.get("id") or "",
        ).strip()

        if instagram_id:
            instagram_profile = {}

            try:
                instagram_profile = self.client.get_instagram_profile(
                    instagram_account_id=instagram_id,
                    access_token=page_access_token,
                )

            except MetaAPIError:
                # The Page itself can still be connected even
                # if profile metadata retrieval temporarily
                # fails. We retain the Instagram ID and use
                # safe fallback display values.
                logger.warning(
                    "Unable to fetch Instagram profile " "for Instagram ID %s.",
                    instagram_id,
                    exc_info=True,
                )

            instagram_username = str(
                instagram_profile.get("username") or "",
            ).strip()

            instagram_name = str(
                instagram_profile.get("name") or instagram_username or instagram_id,
            ).strip()

            instagram_profile_image = str(
                instagram_profile.get(
                    "profile_picture_url",
                )
                or "",
            ).strip()

            accounts.append(
                MetaAccountData(
                    platform=SocialPlatform.INSTAGRAM,
                    platform_account_id=instagram_id,
                    account_name=instagram_name,
                    username=instagram_username,
                    profile_image=instagram_profile_image,
                    access_token="",
                    credential_type=MetaCredentialType.PAGE,
                    linked_facebook_page_platform_account_id=page_id,
                )
            )

        return MetaDiscoveryResult(
            provider_user_id=provider_user_id,
            accounts=accounts,
        )


# ============================================================
# META SOCIAL ACCOUNT PERSISTENCE
# ============================================================


class MetaSocialAccountService:
    """
    Persist a Meta OAuth authorization and its selected
    Facebook Page / linked Instagram account.

    All database writes happen inside one transaction.
    """

    def __init__(
        self,
        organization,
        user,
    ):
        self.organization = organization
        self.user = user

    # ========================================================
    # CONNECTION
    # ========================================================

    def _get_or_create_connection(
        self,
        *,
        provider_user_id: str,
    ):
        connection = (
            SocialConnection.objects.filter(
                organization=self.organization,
                provider=SocialConnectionProvider.META,
                provider_user_id=str(
                    provider_user_id,
                ),
            )
            .order_by("-is_deleted", "-created_at")
            .first()
        )

        now = timezone.now()

        if connection:
            update_fields = []

            if connection.is_deleted:
                connection.is_deleted = False
                connection.deleted_at = None
                update_fields.extend(
                    [
                        "is_deleted",
                        "deleted_at",
                    ]
                )

            if connection.status != SocialConnectionStatus.ACTIVE:
                connection.status = SocialConnectionStatus.ACTIVE
                update_fields.append("status")

            connection.last_synced_at = now
            update_fields.append("last_synced_at")

            if update_fields:
                update_fields.append("updated_at")
                connection.save(
                    update_fields=update_fields,
                )

            return connection

        return SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=str(
                provider_user_id,
            ),
            status=SocialConnectionStatus.ACTIVE,
            last_synced_at=now,
        )

    # ========================================================
    # USER CREDENTIAL
    # ========================================================

    def _save_user_credential(
        self,
        *,
        connection,
        user_access_token: str,
        token_expires_at=None,
    ):
        credential = (
            MetaAccountCredential.objects.filter(
                social_connection=connection,
                credential_type=MetaCredentialType.USER,
            )
            .order_by("-created_at")
            .first()
        )

        encrypted_token = encrypt_token(
            user_access_token,
        )

        defaults = {
            "social_account": None,
            "access_token": encrypted_token,
            "token_expires_at": token_expires_at,
            "status": MetaCredentialStatus.ACTIVE,
            "last_verified_at": timezone.now(),
            "is_deleted": False,
            "deleted_at": None,
        }

        if credential:
            for field, value in defaults.items():
                setattr(
                    credential,
                    field,
                    value,
                )

            credential.save()

            return credential

        return MetaAccountCredential.objects.create(
            social_connection=connection,
            social_account=None,
            credential_type=MetaCredentialType.USER,
            **{
                key: value
                for key, value in defaults.items()
                if key
                not in {
                    "social_account",
                }
            },
        )

    # ========================================================
    # SOCIAL ACCOUNT
    # ========================================================

    def _get_or_create_social_account(
        self,
        *,
        account_data: MetaAccountData,
        connection,
    ):
        now = timezone.now()

        social_account = (
            SocialAccount.objects.filter(
                organization=self.organization,
                platform=account_data.platform,
                platform_account_id=(account_data.platform_account_id),
            )
            .order_by("-is_deleted", "-created_at")
            .first()
        )

        if social_account:
            social_account.organization = self.organization
            social_account.connection = connection
            social_account.account_name = account_data.account_name
            social_account.username = account_data.username
            social_account.profile_image = account_data.profile_image
            social_account.status = SocialAccountStatus.CONNECTED
            social_account.is_valid = True
            social_account.last_synced_at = now
            social_account.is_deleted = False
            social_account.deleted_at = None

            social_account.save()

            return social_account

        return SocialAccount.objects.create(
            organization=self.organization,
            connection=connection,
            platform=account_data.platform,
            platform_account_id=(account_data.platform_account_id),
            account_name=account_data.account_name,
            username=account_data.username,
            profile_image=account_data.profile_image,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
            last_synced_at=now,
        )

    # ========================================================
    # PAGE CREDENTIAL
    # ========================================================

    def _save_page_credential(
        self,
        *,
        social_account,
        page_access_token: str,
    ):
        if not page_access_token:
            raise MetaAPIError(
                "Facebook Page access token is missing.",
            )

        credential = (
            MetaAccountCredential.objects.filter(
                social_account=social_account,
                credential_type=MetaCredentialType.PAGE,
            )
            .order_by("-created_at")
            .first()
        )

        encrypted_token = encrypt_token(
            page_access_token,
        )

        if credential:
            credential.access_token = encrypted_token
            credential.social_connection = None
            credential.token_expires_at = None
            credential.status = MetaCredentialStatus.ACTIVE
            credential.last_verified_at = timezone.now()
            credential.is_deleted = False
            credential.deleted_at = None
            credential.save()

            return credential

        return MetaAccountCredential.objects.create(
            social_account=social_account,
            social_connection=None,
            credential_type=MetaCredentialType.PAGE,
            access_token=encrypted_token,
            token_expires_at=None,
            status=MetaCredentialStatus.ACTIVE,
            last_verified_at=timezone.now(),
        )

    # ========================================================
    # PAGE ↔ INSTAGRAM LINK
    # ========================================================

    def _save_page_instagram_link(
        self,
        *,
        facebook_page,
        instagram_account,
    ):
        link = (
            MetaSocialAccountLink.objects.filter(
                organization=self.organization,
                facebook_page=facebook_page,
                instagram_account=instagram_account,
            )
            .order_by("-is_deleted", "-created_at")
            .first()
        )

        if link:
            link.is_deleted = False
            link.deleted_at = None
            link.save(
                update_fields=[
                    "is_deleted",
                    "deleted_at",
                    "updated_at",
                ]
            )

            return link

        return MetaSocialAccountLink.objects.create(
            organization=self.organization,
            facebook_page=facebook_page,
            instagram_account=instagram_account,
        )

    # ========================================================
    # COMPLETE SYNC
    # ========================================================

    @transaction.atomic
    def sync_connection_and_accounts(
        self,
        *,
        provider_user_id: str,
        user_access_token: str,
        accounts: List[MetaAccountData],
        token_expires_at=None,
    ):
        if not provider_user_id:
            raise MetaAPIError(
                "Meta provider user ID is required.",
            )

        if not user_access_token:
            raise MetaAPIError(
                "Meta access token is required.",
            )

        if not accounts:
            raise MetaAPIError(
                "Meta did not return any social accounts.",
            )

        connection = self._get_or_create_connection(
            provider_user_id=provider_user_id,
        )

        self._save_user_credential(
            connection=connection,
            user_access_token=user_access_token,
            token_expires_at=token_expires_at,
        )

        facebook_accounts = {}
        instagram_accounts = {}
        synced_accounts = []

        # ----------------------------------------------------
        # CREATE / UPDATE ACCOUNTS
        # ----------------------------------------------------

        for account_data in accounts:
            social_account = self._get_or_create_social_account(
                account_data=account_data,
                connection=connection,
            )

            if account_data.platform == SocialPlatform.FACEBOOK:
                facebook_accounts[account_data.platform_account_id] = social_account

                self._save_page_credential(
                    social_account=social_account,
                    page_access_token=account_data.access_token,
                )

            elif account_data.platform == SocialPlatform.INSTAGRAM:
                instagram_accounts[account_data.platform_account_id] = social_account

            synced_accounts.append(
                social_account,
            )

        # ----------------------------------------------------
        # PAGE → INSTAGRAM
        # ----------------------------------------------------

        for account_data in accounts:
            if account_data.platform != SocialPlatform.INSTAGRAM:
                continue

            linked_page_id = account_data.linked_facebook_page_platform_account_id

            if not linked_page_id:
                continue

            facebook_page = facebook_accounts.get(
                linked_page_id,
            )

            instagram_account = instagram_accounts.get(
                account_data.platform_account_id,
            )

            if not facebook_page or not instagram_account:
                raise MetaAPIError(
                    "Meta returned an Instagram account without "
                    "a valid linked Facebook Page.",
                )

            self._save_page_instagram_link(
                facebook_page=facebook_page,
                instagram_account=instagram_account,
            )

        connection.status = SocialConnectionStatus.ACTIVE
        connection.last_synced_at = timezone.now()

        connection.save(
            update_fields=[
                "status",
                "last_synced_at",
                "updated_at",
            ]
        )

        return (
            connection,
            synced_accounts,
        )


# ============================================================
# META OAUTH SERVICE
# ============================================================


class MetaOAuthService:
    """
    Complete Meta OAuth orchestration.

    Flow:

        authorization code
            ↓
        access token
            ↓
        Meta account discovery
            ↓
        atomic persistence
    """

    def __init__(self):
        self.client = MetaAPIClient()

    # ========================================================
    # PREPARE OAUTH
    # ========================================================

    def prepare_oauth(
        self,
        *,
        code: str,
        organization,
        user,
    ):
        if not organization:
            raise MetaAPIError(
                "Organization is required.",
            )

        if not user:
            raise MetaAPIError(
                "Authenticated user is required.",
            )

        if not settings.META_APP_ID:
            raise MetaAPIError(
                "META_APP_ID is not configured.",
            )

        if not settings.META_APP_SECRET:
            raise MetaAPIError(
                "META_APP_SECRET is not configured.",
            )

        if not settings.META_OAUTH_REDIRECT_URI:
            raise MetaAPIError(
                "META_OAUTH_REDIRECT_URI is not configured.",
            )

        # ----------------------------------------------------
        # AUTHORIZATION CODE → ACCESS TOKEN
        # ----------------------------------------------------

        token_response = self.client.exchange_code_for_access_token(
            code=code,
        )

        access_token = str(
            token_response.get("access_token") or "",
        ).strip()

        if not access_token:
            raise MetaAPIError(
                "Meta did not return an access token.",
            )

        # Meta may return expires_in for some token types.
        expires_in = token_response.get(
            "expires_in",
        )

        token_expires_at: Optional[object] = None

        if expires_in:
            try:
                expires_in_seconds = int(
                    expires_in,
                )

                if expires_in_seconds > 0:
                    token_expires_at = timezone.now() + timedelta(
                        seconds=expires_in_seconds,
                    )

            except (
                TypeError,
                ValueError,
            ):
                logger.warning(
                    "Meta returned an invalid expires_in value.",
                )

        # ----------------------------------------------------
        # DISCOVER SELECTED PAGE + LINKED IG
        # ----------------------------------------------------

        discovery = MetaAccountDiscoveryService(
            access_token=access_token,
        ).discover_accounts()

        # ----------------------------------------------------
        # PERSIST EVERYTHING ATOMICALLY
        # ----------------------------------------------------

        social_service = MetaSocialAccountService(
            organization=organization,
            user=user,
        )

        connection, accounts = social_service.sync_connection_and_accounts(
            provider_user_id=(discovery.provider_user_id),
            user_access_token=access_token,
            accounts=discovery.accounts,
            token_expires_at=token_expires_at,
        )

        return {
            "connection": connection,
            "accounts": accounts,
            "provider_user_id": (discovery.provider_user_id),
        }
