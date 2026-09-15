import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import List

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
from .crypto import decrypt_token, encrypt_token
from .exceptions import MetaAPIError
from .models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaOAuthSession,
)

logger = logging.getLogger(__name__)


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class MetaAccountData:
    """
    Temporary representation of a Facebook Page discovered
    through the Meta authorization flow.

    IMPORTANT:
    The Meta Facebook connection flow intentionally handles
    Facebook Pages only.

    Instagram accounts must be connected through the dedicated
    Instagram OAuth flow.
    """

    platform: str
    platform_account_id: str
    account_name: str
    username: str = ""
    profile_image: str = ""
    access_token: str = ""
    credential_type: str = MetaCredentialType.PAGE

    # Kept for backward compatibility with existing encrypted
    # OAuth session payloads. It is NOT used to auto-connect
    # Instagram anymore.
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
    Discover Facebook Pages available to the authenticated
    Meta user.

    IMPORTANT ARCHITECTURE RULE
    ---------------------------
    This service discovers Facebook Pages only.

    A Facebook Page can have a linked Instagram Professional
    account at the Meta platform level. That relationship does
    NOT mean that Instagram is connected to this organization.

    Instagram SocialAccount records are created only through
    the dedicated Instagram OAuth flow.

    Therefore:

        Facebook OAuth
            -> Facebook Pages
            -> Facebook SocialAccount

        Instagram OAuth
            -> Instagram account
            -> Instagram SocialAccount
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.client = MetaAPIClient()

    def discover_accounts(self) -> MetaDiscoveryResult:
        """
        Discover usable Facebook Pages.

        No Instagram account discovery is performed here.
        """

        # ----------------------------------------------------
        # CURRENT META USER
        # ----------------------------------------------------

        current_user = self.client.get_current_user(
            access_token=self.access_token,
        )

        if not isinstance(current_user, dict):
            raise MetaAPIError(
                "Meta returned an invalid current-user response.",
            )

        provider_user_id = str(
            current_user.get("id") or "",
        ).strip()

        if not provider_user_id:
            raise MetaAPIError(
                "Meta did not return a provider user ID.",
            )

        # ----------------------------------------------------
        # FACEBOOK PAGES
        # ----------------------------------------------------

        pages = self.client.get_pages(
            access_token=self.access_token,
        )

        if not pages:
            raise MetaAPIError(
                "Meta did not return any Facebook Pages for " "this authorization.",
            )

        logger.info(
            "Meta returned %s Facebook Page(s) for provider_user_id=%s.",
            len(pages),
            provider_user_id,
        )

        accounts: List[MetaAccountData] = []

        # ----------------------------------------------------
        # PROCESS FACEBOOK PAGES ONLY
        # ----------------------------------------------------

        for page in pages:
            if not isinstance(page, dict):
                logger.warning(
                    "Skipping invalid Meta Page payload.",
                )
                continue

            page_id = str(
                page.get("id") or "",
            ).strip()

            page_name = str(
                page.get("name") or "",
            ).strip()

            page_access_token = str(
                page.get("access_token") or "",
            ).strip()

            # ------------------------------------------------
            # PAGE ID VALIDATION
            # ------------------------------------------------

            if not page_id:
                logger.warning(
                    "Skipping Meta Page without an ID.",
                )
                continue

            # ------------------------------------------------
            # PAGE TOKEN VALIDATION
            # ------------------------------------------------

            if not page_access_token:
                logger.warning(
                    "Skipping Meta Page %s because no Page "
                    "access token was returned.",
                    page_id,
                )
                continue

            # ------------------------------------------------
            # FACEBOOK ACCOUNT
            # ------------------------------------------------

            accounts.append(
                MetaAccountData(
                    platform=SocialPlatform.FACEBOOK,
                    platform_account_id=page_id,
                    account_name=page_name or page_id,
                    access_token=page_access_token,
                    credential_type=MetaCredentialType.PAGE,
                )
            )

        if not accounts:
            raise MetaAPIError(
                "Meta returned no usable Facebook Pages.",
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
    Persist Facebook Pages obtained through Meta OAuth.

    This service intentionally DOES NOT create Instagram
    SocialAccount records.

    Responsibilities:
        1. Create/restore Meta SocialConnection.
        2. Save Meta user credential.
        3. Create/restore Facebook SocialAccount.
        4. Save Facebook Page credential.

    Instagram is outside the responsibility of this service.
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
        """
        Get or create the Meta OAuth connection for this
        organization and Meta provider user.

        Existing soft-deleted connections are restored instead
        of creating a new connection.
        """

        provider_user_id = str(
            provider_user_id or "",
        ).strip()

        if not provider_user_id:
            raise MetaAPIError(
                "Meta provider user ID is required.",
            )

        connection = (
            SocialConnection.objects.select_for_update()
            .filter(
                organization=self.organization,
                provider=SocialConnectionProvider.META,
                provider_user_id=provider_user_id,
            )
            .order_by(
                "-is_deleted",
                "-created_at",
            )
            .first()
        )

        now = timezone.now()

        # ----------------------------------------------------
        # EXISTING CONNECTION
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # NEW CONNECTION
        # ----------------------------------------------------

        return SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=provider_user_id,
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
        """
        Save/update the Meta user-level credential.

        The credential belongs to SocialConnection, not to a
        Facebook Page SocialAccount.
        """

        if not user_access_token:
            raise MetaAPIError(
                "Meta user access token is required.",
            )

        credential = (
            MetaAccountCredential.objects.filter(
                social_connection=connection,
                credential_type=MetaCredentialType.USER,
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        encrypted_token = encrypt_token(
            user_access_token,
        )

        now = timezone.now()

        # ----------------------------------------------------
        # UPDATE EXISTING USER CREDENTIAL
        # ----------------------------------------------------

        if credential:
            credential.social_account = None
            credential.access_token = encrypted_token
            credential.token_expires_at = token_expires_at
            credential.status = MetaCredentialStatus.ACTIVE
            credential.last_verified_at = now
            credential.is_deleted = False
            credential.deleted_at = None

            credential.save()

            return credential

        # ----------------------------------------------------
        # CREATE USER CREDENTIAL
        # ----------------------------------------------------

        return MetaAccountCredential.objects.create(
            social_connection=connection,
            social_account=None,
            credential_type=MetaCredentialType.USER,
            access_token=encrypted_token,
            token_expires_at=token_expires_at,
            status=MetaCredentialStatus.ACTIVE,
            last_verified_at=now,
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
        """
        Create or restore one Facebook SocialAccount.

        Provider identity:

            organization
            +
            platform
            +
            platform_account_id

        represents one logical connected account.

        Existing soft-deleted records are restored instead of
        creating duplicate records.
        """

        # ----------------------------------------------------
        # HARD SAFETY CHECK
        # ----------------------------------------------------

        if account_data.platform != SocialPlatform.FACEBOOK:
            raise MetaAPIError(
                "Meta Facebook connection can persist Facebook " "accounts only.",
            )

        platform_account_id = str(
            account_data.platform_account_id or "",
        ).strip()

        if not platform_account_id:
            raise MetaAPIError(
                "Facebook Page ID is required.",
            )

        now = timezone.now()

        # ----------------------------------------------------
        # EXISTING ACCOUNT
        # ----------------------------------------------------

        social_account = (
            SocialAccount.objects.select_for_update()
            .filter(
                organization=self.organization,
                platform=SocialPlatform.FACEBOOK,
                platform_account_id=platform_account_id,
            )
            .order_by(
                "-is_deleted",
                "-created_at",
            )
            .first()
        )

        if social_account:
            social_account.organization = self.organization
            social_account.connection = connection

            social_account.account_name = (
                account_data.account_name or platform_account_id
            )

            social_account.username = account_data.username or ""

            social_account.profile_image = account_data.profile_image or ""

            social_account.status = SocialAccountStatus.CONNECTED

            social_account.is_valid = True
            social_account.last_synced_at = now

            # Restore a previously disconnected/soft-deleted
            # Facebook account.
            social_account.is_deleted = False
            social_account.deleted_at = None

            social_account.save()

            return social_account

        # ----------------------------------------------------
        # CREATE ACCOUNT
        # ----------------------------------------------------

        return SocialAccount.objects.create(
            organization=self.organization,
            connection=connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=platform_account_id,
            account_name=(account_data.account_name or platform_account_id),
            username=account_data.username or "",
            profile_image=account_data.profile_image or "",
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
        """
        Save/update the Facebook Page access token.

        The credential is owned by the Facebook SocialAccount.
        """

        if social_account.platform != SocialPlatform.FACEBOOK:
            raise MetaAPIError(
                "Page credentials can only belong to Facebook " "SocialAccounts.",
            )

        if not page_access_token:
            raise MetaAPIError(
                "Facebook Page access token is missing.",
            )

        credential = (
            MetaAccountCredential.objects.filter(
                social_account=social_account,
                credential_type=MetaCredentialType.PAGE,
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        encrypted_token = encrypt_token(
            page_access_token,
        )

        now = timezone.now()

        # ----------------------------------------------------
        # UPDATE EXISTING PAGE CREDENTIAL
        # ----------------------------------------------------

        if credential:
            credential.social_connection = None
            credential.access_token = encrypted_token
            credential.token_expires_at = None
            credential.status = MetaCredentialStatus.ACTIVE
            credential.last_verified_at = now
            credential.is_deleted = False
            credential.deleted_at = None

            credential.save()

            return credential

        # ----------------------------------------------------
        # CREATE PAGE CREDENTIAL
        # ----------------------------------------------------

        return MetaAccountCredential.objects.create(
            social_account=social_account,
            social_connection=None,
            credential_type=MetaCredentialType.PAGE,
            access_token=encrypted_token,
            token_expires_at=None,
            status=MetaCredentialStatus.ACTIVE,
            last_verified_at=now,
        )

    # ========================================================
    # SAVE SELECTED FACEBOOK ACCOUNTS
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
        """
        Persist selected Facebook Pages.

        IMPORTANT:
        This method rejects Instagram accounts even if an old
        caller accidentally passes one.

        This gives us a second layer of protection against the
        original Facebook -> Instagram auto-connect bug.
        """

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

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
                "Meta did not return any Facebook Pages.",
            )

        # ----------------------------------------------------
        # FACEBOOK-ONLY SAFETY GUARD
        # ----------------------------------------------------

        invalid_accounts = [
            account
            for account in accounts
            if account.platform != SocialPlatform.FACEBOOK
        ]

        if invalid_accounts:
            logger.error(
                "Attempted to persist non-Facebook account(s) "
                "through Meta Facebook flow.",
            )

            raise MetaAPIError(
                "Only Facebook Pages can be connected through "
                "the Meta Facebook flow.",
            )

        # ----------------------------------------------------
        # META CONNECTION
        # ----------------------------------------------------

        connection = self._get_or_create_connection(
            provider_user_id=provider_user_id,
        )

        # ----------------------------------------------------
        # USER CREDENTIAL
        # ----------------------------------------------------

        self._save_user_credential(
            connection=connection,
            user_access_token=user_access_token,
            token_expires_at=token_expires_at,
        )

        # ----------------------------------------------------
        # FACEBOOK PAGES
        # ----------------------------------------------------

        synced_accounts = []

        for account_data in accounts:
            social_account = self._get_or_create_social_account(
                account_data=account_data,
                connection=connection,
            )

            self._save_page_credential(
                social_account=social_account,
                page_access_token=account_data.access_token,
            )

            synced_accounts.append(
                social_account,
            )

        # ----------------------------------------------------
        # CONNECTION SYNC STATE
        # ----------------------------------------------------

        connection.status = SocialConnectionStatus.ACTIVE
        connection.last_synced_at = timezone.now()

        connection.save(
            update_fields=[
                "status",
                "last_synced_at",
                "updated_at",
            ]
        )

        return connection, synced_accounts


# ============================================================
# META OAUTH SERVICE
# ============================================================


class MetaOAuthService:
    """
    Meta OAuth orchestration for Facebook Page connections.

    Flow:

        OAuth authorization code
                ↓
        Meta user access token
                ↓
        Discover Facebook Pages
                ↓
        One Page
            ↓
        connect immediately

        Multiple Pages
            ↓
        temporary encrypted selection session
            ↓
        user selects Facebook Page
            ↓
        connect selected Facebook Page

    Instagram is intentionally excluded from this flow.
    """

    SESSION_TTL_SECONDS = 600

    def __init__(self):
        self.client = MetaAPIClient()

    # ========================================================
    # TOKEN EXPIRATION
    # ========================================================

    @staticmethod
    def _get_token_expiry(
        token_response,
    ):
        """
        Convert Meta expires_in into a timezone-aware expiry
        datetime.
        """

        expires_in = token_response.get(
            "expires_in",
        )

        if not expires_in:
            return None

        try:
            expires_in_seconds = int(
                expires_in,
            )

        except (
            TypeError,
            ValueError,
        ):
            logger.warning(
                "Meta returned an invalid expires_in value.",
            )

            return None

        if expires_in_seconds <= 0:
            return None

        return timezone.now() + timedelta(
            seconds=expires_in_seconds,
        )

    # ========================================================
    # SERIALIZE SESSION ACCOUNTS
    # ========================================================

    @staticmethod
    def _serialize_accounts(
        accounts: List[MetaAccountData],
    ):
        """
        Serialize Facebook Page discovery data into the
        encrypted temporary OAuth session.

        Access tokens remain server-side and encrypted.

        Only Facebook accounts are allowed.
        """

        serialized = []

        for account in accounts:
            if account.platform != SocialPlatform.FACEBOOK:
                continue

            serialized.append(
                {
                    "platform": account.platform,
                    "platform_account_id": (account.platform_account_id),
                    "account_name": account.account_name,
                    "username": account.username,
                    "profile_image": account.profile_image,
                    "access_token": account.access_token,
                    "credential_type": account.credential_type,
                    # Kept for backward compatibility only.
                    # It is intentionally empty for new sessions.
                    "linked_facebook_page_platform_account_id": "",
                }
            )

        return serialized

    # ========================================================
    # DESERIALIZE SESSION ACCOUNTS
    # ========================================================

    @staticmethod
    def _deserialize_accounts(
        encrypted_accounts: str,
    ) -> List[MetaAccountData]:
        """
        Decrypt and deserialize temporary OAuth session data.

        Legacy sessions may contain Instagram records because
        they were created by the previous implementation.

        Those records are deliberately ignored here.

        This prevents an old session from causing a new
        Instagram SocialAccount to be created.
        """

        try:
            raw = decrypt_token(
                encrypted_accounts,
            )

            data = json.loads(
                raw,
            )

        except Exception as exc:
            logger.exception(
                "Unable to deserialize Meta OAuth session.",
            )

            raise MetaAPIError(
                "Unable to read the temporary Meta authorization session.",
            ) from exc

        if not isinstance(data, list):
            raise MetaAPIError(
                "Temporary Meta authorization data is invalid.",
            )

        accounts: List[MetaAccountData] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            platform = str(
                item.get("platform") or "",
            ).strip()

            # ------------------------------------------------
            # IMPORTANT:
            # Never deserialize Instagram records into the
            # Facebook selection flow.
            # ------------------------------------------------

            if platform != SocialPlatform.FACEBOOK:
                continue

            platform_account_id = str(
                item.get("platform_account_id") or "",
            ).strip()

            if not platform_account_id:
                continue

            accounts.append(
                MetaAccountData(
                    platform=SocialPlatform.FACEBOOK,
                    platform_account_id=platform_account_id,
                    account_name=str(
                        item.get("account_name") or "",
                    ),
                    username=str(
                        item.get("username") or "",
                    ),
                    profile_image=str(
                        item.get("profile_image") or "",
                    ),
                    access_token=str(
                        item.get("access_token") or "",
                    ),
                    credential_type=str(
                        item.get("credential_type") or MetaCredentialType.PAGE,
                    ),
                    # Do not restore legacy relationship data
                    # into the new connection flow.
                    linked_facebook_page_platform_account_id="",
                )
            )

        return accounts

    # ========================================================
    # CREATE SELECTION SESSION
    # ========================================================

    def create_selection_session(
        self,
        *,
        organization,
        user,
        provider_user_id: str,
        user_access_token: str,
        accounts: List[MetaAccountData],
        token_expires_at=None,
    ):
        """
        Create a short-lived encrypted Facebook Page selection
        session.

        No Instagram account is stored in the new session.
        """

        if not accounts:
            raise MetaAPIError(
                "Meta did not return any Facebook Pages.",
            )

        facebook_accounts = [
            account
            for account in accounts
            if account.platform == SocialPlatform.FACEBOOK
        ]

        if not facebook_accounts:
            raise MetaAPIError(
                "Meta did not return any usable Facebook Pages.",
            )

        expires_at = timezone.now() + timedelta(
            seconds=self.SESSION_TTL_SECONDS,
        )

        serialized_accounts = self._serialize_accounts(
            facebook_accounts,
        )

        encrypted_accounts = encrypt_token(
            json.dumps(
                serialized_accounts,
                separators=(
                    ",",
                    ":",
                ),
            )
        )

        session = MetaOAuthSession.objects.create(
            organization=organization,
            user=user,
            provider_user_id=provider_user_id,
            encrypted_access_token=encrypt_token(
                user_access_token,
            ),
            encrypted_accounts=encrypted_accounts,
            token_expires_at=token_expires_at,
            expires_at=expires_at,
        )

        return session

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
        """
        Complete Meta OAuth and connect Facebook Page(s).

        If exactly one Facebook Page is available, it is
        connected immediately.

        If multiple Pages are available, a temporary selection
        session is created.
        """

        # ----------------------------------------------------
        # REQUEST VALIDATION
        # ----------------------------------------------------

        if not organization:
            raise MetaAPIError(
                "Organization is required.",
            )

        if not user:
            raise MetaAPIError(
                "Authenticated user is required.",
            )

        if not code:
            raise MetaAPIError(
                "Meta authorization code is required.",
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
        # CODE → USER ACCESS TOKEN
        # ----------------------------------------------------

        token_response = self.client.exchange_code_for_access_token(
            code=code,
        )

        if not isinstance(token_response, dict):
            raise MetaAPIError(
                "Meta returned an invalid access-token response.",
            )

        access_token = str(
            token_response.get("access_token") or "",
        ).strip()

        if not access_token:
            raise MetaAPIError(
                "Meta did not return an access token.",
            )

        token_expires_at = self._get_token_expiry(
            token_response,
        )

        # ----------------------------------------------------
        # DISCOVER FACEBOOK PAGES ONLY
        # ----------------------------------------------------

        discovery = MetaAccountDiscoveryService(
            access_token=access_token,
        ).discover_accounts()

        facebook_accounts = [
            account
            for account in discovery.accounts
            if account.platform == SocialPlatform.FACEBOOK
        ]

        if not facebook_accounts:
            raise MetaAPIError(
                "Meta did not return any usable Facebook Pages.",
            )

        # ----------------------------------------------------
        # ONE FACEBOOK PAGE → DIRECT CONNECT
        # ----------------------------------------------------

        if len(facebook_accounts) == 1:
            selected_page_id = facebook_accounts[0].platform_account_id

            selected_accounts = [
                account
                for account in facebook_accounts
                if account.platform_account_id == selected_page_id
            ]

            social_service = MetaSocialAccountService(
                organization=organization,
                user=user,
            )

            connection, accounts = social_service.sync_connection_and_accounts(
                provider_user_id=discovery.provider_user_id,
                user_access_token=access_token,
                accounts=selected_accounts,
                token_expires_at=token_expires_at,
            )

            return {
                "status": "connected",
                "connection": connection,
                "accounts": accounts,
                "provider_user_id": discovery.provider_user_id,
            }

        # ----------------------------------------------------
        # MULTIPLE FACEBOOK PAGES → SELECTION SESSION
        # ----------------------------------------------------

        session = self.create_selection_session(
            organization=organization,
            user=user,
            provider_user_id=discovery.provider_user_id,
            user_access_token=access_token,
            accounts=facebook_accounts,
            token_expires_at=token_expires_at,
        )

        return {
            "status": "selection_required",
            "session": session,
            "provider_user_id": discovery.provider_user_id,
            # Only Facebook Pages are returned.
            "accounts": facebook_accounts,
        }

    # ========================================================
    # GET SELECTION DATA
    # ========================================================

    def get_selection_data(
        self,
        *,
        session,
        organization,
        user,
    ):
        """
        Return Facebook Pages available for selection.

        The frontend receives only page metadata.

        OAuth access tokens remain encrypted on the server.
        """

        if not session:
            raise MetaAPIError(
                "Meta authorization session was not found.",
            )

        # ----------------------------------------------------
        # ORGANIZATION OWNERSHIP
        # ----------------------------------------------------

        if session.organization_id != organization.pk:
            raise MetaAPIError(
                "This Meta authorization session does not belong "
                "to the selected organization.",
            )

        # ----------------------------------------------------
        # USER OWNERSHIP
        # ----------------------------------------------------

        if session.user_id != user.id:
            raise MetaAPIError(
                "This Meta authorization session belongs to " "another user.",
            )

        # ----------------------------------------------------
        # SESSION STATE
        # ----------------------------------------------------

        if session.is_consumed:
            raise MetaAPIError(
                "This Meta authorization session has already been used.",
            )

        if session.is_expired:
            raise MetaAPIError(
                "The Meta authorization session has expired. "
                "Please connect Facebook again.",
            )

        # ----------------------------------------------------
        # DESERIALIZE
        # ----------------------------------------------------

        accounts = self._deserialize_accounts(
            session.encrypted_accounts,
        )

        pages = [
            {
                "id": account.platform_account_id,
                "name": account.account_name,
                "profile_image": account.profile_image,
            }
            for account in accounts
            if account.platform == SocialPlatform.FACEBOOK
        ]

        if not pages:
            raise MetaAPIError(
                "No Facebook Pages are available in this " "authorization session.",
            )

        return {
            "selection_key": str(
                session.selection_key,
            ),
            "pages": pages,
            "expires_at": session.expires_at,
        }

    # ========================================================
    # CONFIRM SELECTION
    # ========================================================

    def confirm_selection(
        self,
        *,
        session,
        organization,
        user,
        page_id: str,
    ):
        """
        Persist the Facebook Page selected by the user.

        The selected page is resolved strictly from the encrypted
        OAuth session. The frontend cannot inject an arbitrary
        Page ID.

        Instagram is never created or linked here.
        """

        if not session:
            raise MetaAPIError(
                "Meta authorization session was not found.",
            )

        # ----------------------------------------------------
        # ORGANIZATION OWNERSHIP
        # ----------------------------------------------------

        if session.organization_id != organization.pk:
            raise MetaAPIError(
                "This Meta authorization session does not belong "
                "to the selected organization.",
            )

        # ----------------------------------------------------
        # USER OWNERSHIP
        # ----------------------------------------------------

        if session.user_id != user.id:
            raise MetaAPIError(
                "This Meta authorization session belongs to " "another user.",
            )

        # ----------------------------------------------------
        # SESSION STATE
        # ----------------------------------------------------

        if session.is_consumed:
            raise MetaAPIError(
                "This Meta authorization session has already been used.",
            )

        if session.is_expired:
            raise MetaAPIError(
                "The Meta authorization session has expired. "
                "Please connect Facebook again.",
            )

        # ----------------------------------------------------
        # PAGE ID
        # ----------------------------------------------------

        page_id = str(
            page_id or "",
        ).strip()

        if not page_id:
            raise MetaAPIError(
                "Facebook Page ID is required.",
            )

        # ----------------------------------------------------
        # LOAD SESSION ACCOUNTS
        # ----------------------------------------------------

        accounts = self._deserialize_accounts(
            session.encrypted_accounts,
        )

        # ----------------------------------------------------
        # RESOLVE SELECTED FACEBOOK PAGE
        # ----------------------------------------------------

        selected_page = next(
            (
                account
                for account in accounts
                if (
                    account.platform == SocialPlatform.FACEBOOK
                    and account.platform_account_id == page_id
                )
            ),
            None,
        )

        if not selected_page:
            raise MetaAPIError(
                "The selected Facebook Page is not part of "
                "this Meta authorization session.",
            )

        # ----------------------------------------------------
        # SELECT FACEBOOK PAGE ONLY
        # ----------------------------------------------------

        selected_accounts = [
            account
            for account in accounts
            if (
                account.platform == SocialPlatform.FACEBOOK
                and account.platform_account_id == page_id
            )
        ]

        if not selected_accounts:
            raise MetaAPIError(
                "Unable to resolve the selected Facebook Page.",
            )

        # ----------------------------------------------------
        # DECRYPT USER ACCESS TOKEN
        # ----------------------------------------------------

        try:
            user_access_token = decrypt_token(
                session.encrypted_access_token,
            )
        except Exception as exc:
            logger.exception(
                "Unable to decrypt Meta OAuth session token.",
            )

            raise MetaAPIError(
                "Unable to continue the Meta authorization session.",
            ) from exc

        if not user_access_token:
            raise MetaAPIError(
                "Meta authorization token is unavailable.",
            )

        # ----------------------------------------------------
        # PERSIST FACEBOOK PAGE
        # ----------------------------------------------------

        social_service = MetaSocialAccountService(
            organization=organization,
            user=user,
        )

        connection, synced_accounts = social_service.sync_connection_and_accounts(
            provider_user_id=session.provider_user_id,
            user_access_token=user_access_token,
            accounts=selected_accounts,
            token_expires_at=session.token_expires_at,
        )

        # ----------------------------------------------------
        # CONSUME SESSION
        # ----------------------------------------------------

        session.consumed_at = timezone.now()

        session.save(
            update_fields=[
                "consumed_at",
                "updated_at",
            ]
        )

        return {
            "connection": connection,
            "accounts": synced_accounts,
            "provider_user_id": session.provider_user_id,
        }


class MetaCredentialService:
    """
    Handles lifecycle operations for Meta credentials.

    A Facebook Page credential belongs to the Facebook
    SocialAccount.

    A Meta USER credential belongs to the SocialConnection.

    Disconnecting one Facebook Page must NOT revoke the
    organization-level Meta USER credential.
    """

    @staticmethod
    @transaction.atomic
    def revoke_page_credential_for_disconnect(
        *,
        social_account,
    ):
        """
        Revoke only the Facebook Page credential associated
        with the supplied Facebook SocialAccount.

        The Meta USER credential / SocialConnection is intentionally
        left untouched.
        """

        if social_account.platform != SocialPlatform.FACEBOOK:
            raise MetaAPIError(
                "Meta Page credential revocation requires a Facebook account."
            )

        credential = (
            MetaAccountCredential.objects.select_for_update()
            .filter(
                social_account=social_account,
                credential_type=MetaCredentialType.PAGE,
                is_deleted=False,
            )
            .first()
        )

        if credential:
            credential.status = MetaCredentialStatus.REVOKED

            credential.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return credential
