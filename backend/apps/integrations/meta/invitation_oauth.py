"""Facebook OAuth and explicit Page selection for invitation recipients."""

import json
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.social_accounts.invitations import (
    InvalidInvitation,
    consume_invitation_oauth_attempt,
    create_invitation_oauth_attempt,
    create_invitation_oauth_attempt_for_resumption,
    get_invitation_acceptance_context_by_id,
    get_invitation_acceptance_context,
    persist_invitation_account,
)
from apps.social_accounts.models import (
    SocialAccountInvitationOAuthAttempt,
    SocialPlatform,
)

from .client import MetaAPIClient, MetaAPIError
from .constants import META_OAUTH_AUTHORIZE_URL
from .crypto import decrypt_token, encrypt_token
from apps.social_accounts.models import (
    SocialConnectionProvider,
    SocialConnectionStatus,
    SocialAccountInvitationOAuthAttempt,
    SocialPlatform,
)

from .models import InvitationMetaOAuthSession
from .services import (
    MetaAccountDiscoveryService,
    MetaOAuthService,
    MetaSocialAccountService,
)


INVITATION_SELECTION_TTL = timedelta(minutes=10)


class InvitationMetaOAuthService:
    """Adapter from anonymous invitation OAuth into existing Meta services."""

    def __init__(self):
        self.client = MetaAPIClient()

    @staticmethod
    def _redirect_uri():
        value = str(
            getattr(settings, "META_INVITATION_OAUTH_REDIRECT_URI", "") or ""
        ).strip()
        if not value:
            raise MetaAPIError("Facebook invitation OAuth is not configured.")
        return value

    def start(self, acceptance_token):
        redirect_uri = self._redirect_uri()
        app_id = str(getattr(settings, "META_APP_ID", "") or "").strip()
        app_secret = str(getattr(settings, "META_APP_SECRET", "") or "").strip()
        config_id = str(
            getattr(settings, "META_BUSINESS_LOGIN_CONFIG_ID", "") or ""
        ).strip()
        if not app_id or not app_secret or not config_id:
            raise MetaAPIError("Facebook invitation OAuth is not configured.")

        _, state = create_invitation_oauth_attempt(
            acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        params = {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "config_id": config_id,
        }
        return f"{META_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    def start_from_resumption(self, resumption_token):
        redirect_uri = self._redirect_uri()
        app_id = str(getattr(settings, "META_APP_ID", "") or "").strip()
        app_secret = str(getattr(settings, "META_APP_SECRET", "") or "").strip()
        config_id = str(
            getattr(settings, "META_BUSINESS_LOGIN_CONFIG_ID", "") or ""
        ).strip()
        if not app_id or not app_secret or not config_id:
            raise MetaAPIError("Facebook invitation OAuth is not configured.")

        _attempt, state, context = create_invitation_oauth_attempt_for_resumption(
            resumption_token,
            platform=SocialPlatform.FACEBOOK,
        )
        params = {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "config_id": config_id,
        }
        return {
            "authorization_url": f"{META_OAUTH_AUTHORIZE_URL}?{urlencode(params)}",
            "context": context,
        }

    def create_selection_session(self, callback_context, code):
        redirect_uri = self._redirect_uri()
        if not code:
            raise MetaAPIError("Meta authorization code is missing.")

        token_response = self.client.exchange_code_for_access_token(
            code=code,
            redirect_uri=redirect_uri,
        )
        if not isinstance(token_response, dict):
            raise MetaAPIError("Meta returned an invalid access-token response.")
        user_access_token = str(token_response.get("access_token") or "").strip()
        if not user_access_token:
            raise MetaAPIError("Meta did not return an access token.")

        token_expires_at = MetaOAuthService._get_token_expiry(token_response)
        discovery = MetaAccountDiscoveryService(
            access_token=user_access_token,
            sensitive_values=(code, getattr(settings, "META_APP_SECRET", "")),
        ).discover_accounts()
        facebook_pages = [
            account
            for account in discovery.accounts
            if account.platform == SocialPlatform.FACEBOOK
        ]

        return self._persist_selection_session(
            callback_context=callback_context,
            provider_user_id=discovery.provider_user_id,
            user_access_token=user_access_token,
            accounts=facebook_pages,
            token_expires_at=token_expires_at,
        )

    @transaction.atomic
    def _persist_selection_session(
        self,
        *,
        callback_context,
        provider_user_id,
        user_access_token,
        accounts,
        token_expires_at,
    ):
        acceptance_context = get_invitation_acceptance_context_by_id(
            callback_context["acceptance_id"]
        )
        if SocialPlatform.FACEBOOK not in acceptance_context["selected_platforms"]:
            raise InvalidInvitation("Facebook is not selected for this invitation session.")

        attempt = SocialAccountInvitationOAuthAttempt.objects.select_for_update().filter(
            pk=callback_context["attempt_id"],
            acceptance_id=acceptance_context["acceptance_id"],
            platform=SocialPlatform.FACEBOOK,
            is_deleted=False,
        ).first()
        now = timezone.now()
        if (
            attempt is None
            or attempt.consumed_at is None
            or attempt.expires_at <= now
        ):
            raise InvalidInvitation("This Facebook OAuth attempt has expired.")

        expiry_limits = [
            acceptance_context["expires_at"],
            attempt.expires_at,
            now + INVITATION_SELECTION_TTL,
        ]
        if token_expires_at is not None:
            expiry_limits.append(token_expires_at)
        expires_at = min(expiry_limits)
        if expires_at <= now:
            raise InvalidInvitation("This Facebook authorization has expired.")
        serialized_accounts = MetaOAuthService._serialize_accounts(accounts)
        return InvitationMetaOAuthSession.objects.create(
            acceptance_id=acceptance_context["acceptance_id"],
            oauth_attempt=attempt,
            provider_user_id=provider_user_id,
            encrypted_access_token=encrypt_token(user_access_token),
            encrypted_accounts=encrypt_token(
                json.dumps(serialized_accounts, separators=(",", ":"))
            ),
            token_expires_at=token_expires_at,
            expires_at=expires_at,
        )

    @transaction.atomic
    def get_selection_data(
        self, *, selection_key, acceptance_token=None, resumption_token=None
    ):
        if resumption_token:
            from apps.social_accounts.invitations import get_invitation_acceptance_context_for_resumption

            context = get_invitation_acceptance_context_for_resumption(
                resumption_token,
                expected_platform=SocialPlatform.FACEBOOK,
            )
        else:
            context = get_invitation_acceptance_context(acceptance_token)
        session = self._get_active_session(
            selection_key=selection_key,
            acceptance_id=context["acceptance_id"],
        )
        accounts = MetaOAuthService._deserialize_accounts(session.encrypted_accounts)
        connected_page_ids = MetaOAuthService._get_connected_page_ids(
            organization=context["organization"],
            page_ids=[
                account.platform_account_id
                for account in accounts
                if account.platform == SocialPlatform.FACEBOOK
            ],
        )
        return {
            "pages": [
                {
                    "id": account.platform_account_id,
                    "name": account.account_name,
                    "profile_image": account.profile_image,
                    "connected": account.platform_account_id in connected_page_ids,
                }
                for account in accounts
                if account.platform == SocialPlatform.FACEBOOK
            ],
            "expires_at": session.expires_at,
        }

    @transaction.atomic
    def add_page(
        self, *, selection_key, page_id, acceptance_token=None, resumption_token=None
    ):
        if resumption_token:
            from apps.social_accounts.invitations import get_invitation_acceptance_context_for_resumption

            context = get_invitation_acceptance_context_for_resumption(
                resumption_token,
                expected_platform=SocialPlatform.FACEBOOK,
            )
        else:
            context = get_invitation_acceptance_context(acceptance_token)
        session = self._get_active_session(
            selection_key=selection_key,
            acceptance_id=context["acceptance_id"],
        )
        accounts = MetaOAuthService._deserialize_accounts(session.encrypted_accounts)
        page_id = str(page_id or "").strip()
        selected_page = next(
            (
                account
                for account in accounts
                if account.platform == SocialPlatform.FACEBOOK
                and account.platform_account_id == page_id
            ),
            None,
        )
        if selected_page is None:
            raise InvalidInvitation("The selected Page is not part of this invitation session.")

        user_access_token = decrypt_token(session.encrypted_access_token)
        existing_page_ids = MetaOAuthService._get_connected_page_ids(
            organization=context["organization"],
            page_ids=[page_id],
        )
        already_connected = page_id in existing_page_ids

        def persist(*, organization, selected_platforms, **_scope):
            locked_session = InvitationMetaOAuthSession.objects.select_for_update().filter(
                pk=session.pk,
                acceptance_id=context["acceptance_id"],
                is_deleted=False,
            ).first()
            now = timezone.now()
            if (
                locked_session is None
                or locked_session.expires_at <= now
                or locked_session.oauth_attempt.expires_at <= now
                or locked_session.oauth_attempt.consumed_at is None
                or SocialPlatform.FACEBOOK not in selected_platforms
            ):
                raise InvalidInvitation("This Facebook Page selection has expired.")

            social_service = MetaSocialAccountService(
                organization=organization,
                user=None,
            )
            _connection, connected_accounts = social_service.sync_connection_and_accounts(
                provider_user_id=locked_session.provider_user_id,
                user_access_token=user_access_token,
                accounts=[selected_page],
                token_expires_at=locked_session.token_expires_at,
            )
            if not connected_accounts:
                raise MetaAPIError("Facebook Page persistence returned no account.")
            return connected_accounts[0]

        if resumption_token:
            from apps.social_accounts.invitations import persist_invitation_account_for_acceptance

            account = persist_invitation_account_for_acceptance(
                context["acceptance_id"], persist
            )
        else:
            account = persist_invitation_account(acceptance_token, persist)
        return {
            "id": account.platform_account_id,
            "name": account.account_name,
            "already_connected": already_connected,
        }

    @staticmethod
    def _get_active_session(*, selection_key, acceptance_id):
        session = InvitationMetaOAuthSession.objects.filter(
            selection_key=selection_key,
            acceptance_id=acceptance_id,
            is_deleted=False,
            oauth_attempt__is_deleted=False,
        ).first()
        if session is None:
            raise InvalidInvitation("This Facebook Page selection has expired.")
        if session.is_expired:
            InvitationMetaOAuthSession.objects.filter(
                pk=session.pk,
                is_deleted=False,
            ).update(
                encrypted_access_token="",
                encrypted_accounts="",
                updated_at=timezone.now(),
            )
            raise InvalidInvitation("This Facebook Page selection has expired.")
        if (
            session.oauth_attempt.platform != SocialPlatform.FACEBOOK
            or session.oauth_attempt.consumed_at is None
            or session.oauth_attempt.expires_at <= timezone.now()
        ):
            raise InvalidInvitation("This Facebook Page selection is invalid.")
        return session
