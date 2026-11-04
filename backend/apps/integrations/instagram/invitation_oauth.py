"""Invitation-scoped Instagram OAuth staging and explicit confirmation."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.social_accounts.invitations import (
    InvalidInvitation,
    _has_active_provider_credential,
    consume_invitation_oauth_attempt,
    create_invitation_oauth_attempt,
    create_invitation_oauth_attempt_for_resumption,
    get_invitation_acceptance_context,
    get_invitation_acceptance_context_by_id,
    persist_invitation_account,
)
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountInvitationAcceptanceAccount,
    SocialAccountInvitationOAuthAttempt,
    SocialAccountStatus,
    SocialPlatform,
)

from .client import InstagramAPIClient
from .crypto import decrypt_token, encrypt_token
from .exceptions import InstagramIntegrationError
from .models import (
    InvitationInstagramOAuthSession,
    InvitationInstagramOAuthStatus,
)
from .services import InstagramOAuthResult, InstagramOAuthService


INVITATION_INSTAGRAM_STAGING_TTL = timedelta(minutes=10)


class InvitationInstagramOAuthService:
    """Adapter from anonymous invitation OAuth into existing Instagram code."""

    @staticmethod
    def _redirect_uri():
        redirect_uri = str(
            getattr(settings, "INSTAGRAM_INVITATION_OAUTH_REDIRECT_URI", "") or ""
        ).strip()
        if not redirect_uri:
            raise InstagramIntegrationError(
                "Instagram invitation OAuth is not configured."
            )
        return redirect_uri

    def start(self, acceptance_token):
        redirect_uri = self._redirect_uri()
        client = InstagramAPIClient(redirect_uri=redirect_uri)
        _attempt, state = create_invitation_oauth_attempt(
            acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        authorization_url = InstagramOAuthService(
            client=client,
        ).build_authorization_url_for_state(
            state=state,
            redirect_uri=redirect_uri,
        )
        return authorization_url

    def start_from_resumption(self, resumption_token):
        redirect_uri = self._redirect_uri()
        client = InstagramAPIClient(redirect_uri=redirect_uri)
        _attempt, state, context = create_invitation_oauth_attempt_for_resumption(
            resumption_token,
            platform=SocialPlatform.INSTAGRAM,
        )
        authorization_url = InstagramOAuthService(
            client=client,
        ).build_authorization_url_for_state(
            state=state,
            redirect_uri=redirect_uri,
        )
        return {"authorization_url": authorization_url, "context": context}

    def stage_callback(self, callback_context, code):
        if not code:
            raise InstagramIntegrationError("Instagram authorization code is missing.")
        redirect_uri = self._redirect_uri()
        client = InstagramAPIClient(redirect_uri=redirect_uri)
        provider_result = InstagramOAuthService(
            client=client,
        ).exchange_and_fetch_profile(
            code=code,
            redirect_uri=redirect_uri,
        )
        return self._persist_staging_session(callback_context, provider_result)

    @transaction.atomic
    def _persist_staging_session(self, callback_context, provider_result):
        context = get_invitation_acceptance_context_by_id(
            callback_context["acceptance_id"]
        )
        if (
            SocialPlatform.INSTAGRAM not in context["allowed_platforms"]
            or SocialPlatform.INSTAGRAM not in context["selected_platforms"]
        ):
            raise InvalidInvitation("Instagram is not selected for this invitation.")

        attempt = SocialAccountInvitationOAuthAttempt.objects.select_for_update().filter(
            pk=callback_context["attempt_id"],
            acceptance_id=context["acceptance_id"],
            platform=SocialPlatform.INSTAGRAM,
            is_deleted=False,
        ).first()
        now = timezone.now()
        if (
            attempt is None
            or attempt.consumed_at is None
            or attempt.expires_at <= now
        ):
            raise InvalidInvitation("This Instagram OAuth attempt has expired.")

        expires_at = min(
            context["expires_at"],
            attempt.expires_at,
            provider_result.token_expires_at,
            now + INVITATION_INSTAGRAM_STAGING_TTL,
        )
        if expires_at <= now:
            raise InvalidInvitation("This Instagram authorization has expired.")

        return InvitationInstagramOAuthSession.objects.create(
            acceptance_id=context["acceptance_id"],
            oauth_attempt=attempt,
            instagram_user_id=provider_result.instagram_user_id,
            username=provider_result.username,
            account_name=provider_result.account_name,
            profile_image=provider_result.profile_image,
            encrypted_access_token=encrypt_token(provider_result.access_token),
            token_expires_at=provider_result.token_expires_at,
            expires_at=expires_at,
        )

    def get_staging_data(
        self, *, selection_key, acceptance_token=None, resumption_token=None
    ):
        with transaction.atomic():
            context = self._acceptance_context_or_invalidate_stage(
                selection_key,
                acceptance_token,
                resumption_token=resumption_token,
            )
            session = (
                self._get_active_session(
                    selection_key=selection_key,
                    acceptance_id=context["acceptance_id"],
                )
                if context is not None
                else None
            )
            data = self._safe_profile(session) if session is not None else None
        if data is None:
            raise InvalidInvitation("This Instagram preview is invalid or expired.")
        return data

    def confirm(
        self, *, selection_key, acceptance_token=None, resumption_token=None
    ):
        try:
            with transaction.atomic():
                context = self._acceptance_context_or_invalidate_stage(
                    selection_key,
                    acceptance_token,
                    resumption_token=resumption_token,
                )
                if context is None:
                    account = None
                else:
                    session = InvitationInstagramOAuthSession.objects.select_for_update().filter(
                        selection_key=selection_key,
                        acceptance_id=context["acceptance_id"],
                        is_deleted=False,
                    ).first()
                    if session is None:
                        raise InvalidInvitation(
                            "This Instagram preview is invalid or expired."
                        )
                    if session.status == InvitationInstagramOAuthStatus.CONFIRMED:
                        account = self._get_confirmed_account(session, context)
                    else:
                        account = self._confirm_staged_session(
                            selection_key=selection_key,
                            acceptance_token=acceptance_token,
                            resumption_token=resumption_token,
                            context=context,
                        )
        except InvalidInvitation:
            self._cleanup_expired_session(selection_key)
            raise
        if account is None:
            raise InvalidInvitation("This Instagram preview is invalid or expired.")
        return {
            "id": str(account.id),
            "instagram_user_id": account.platform_account_id,
            "username": account.username,
            "account_name": account.account_name,
        }

    def _confirm_staged_session(
        self,
        *,
        selection_key,
        acceptance_token,
        resumption_token,
        context,
    ):
        active_session = self._get_active_session(
            selection_key=selection_key,
            acceptance_id=context["acceptance_id"],
        )
        if active_session is None:
            return None
        provider_result = InstagramOAuthResult(
            instagram_user_id=active_session.instagram_user_id,
            username=active_session.username,
            account_name=active_session.account_name,
            profile_image=active_session.profile_image,
            access_token=decrypt_token(active_session.encrypted_access_token),
            token_expires_at=active_session.token_expires_at,
        )

        def persist(*, organization, allowed_platforms, selected_platforms):
            locked_session = self._get_active_session(
                selection_key=selection_key,
                acceptance_id=context["acceptance_id"],
            )
            if (
                locked_session is None
                or SocialPlatform.INSTAGRAM not in allowed_platforms
                or SocialPlatform.INSTAGRAM not in selected_platforms
                or locked_session.oauth_attempt.platform != SocialPlatform.INSTAGRAM
            ):
                raise InvalidInvitation(
                    "Instagram is not selected for this invitation."
                )

            connected_account = InstagramOAuthService.persist_authorized_profile(
                organization=organization,
                result=provider_result,
                recover_unique_race=True,
                restore_deleted_credential=True,
            )
            locked_session.status = InvitationInstagramOAuthStatus.CONFIRMED
            locked_session.confirmed_at = timezone.now()
            locked_session.encrypted_access_token = ""
            locked_session.save(update_fields=[
                "status", "confirmed_at", "encrypted_access_token", "updated_at",
            ])
            return connected_account

        if resumption_token:
            from apps.social_accounts.invitations import persist_invitation_account_for_acceptance

            return persist_invitation_account_for_acceptance(
                context["acceptance_id"], persist
            )
        return persist_invitation_account(acceptance_token, persist)

    @staticmethod
    def _get_confirmed_account(session, context):
        now = timezone.now()
        if (
            session.confirmed_at is None
            or session.expires_at <= now
            or session.expires_at > context["expires_at"]
            or session.token_expires_at <= now
            or session.oauth_attempt.is_deleted
            or session.oauth_attempt.platform != SocialPlatform.INSTAGRAM
            or session.oauth_attempt.acceptance_id != context["acceptance_id"]
            or session.oauth_attempt.consumed_at is None
            or session.oauth_attempt.expires_at <= now
            or SocialPlatform.INSTAGRAM not in context["allowed_platforms"]
            or SocialPlatform.INSTAGRAM not in context["selected_platforms"]
        ):
            raise InvalidInvitation("This Instagram confirmation is no longer usable.")

        audit_links = list(
            SocialAccountInvitationAcceptanceAccount.objects.select_for_update().filter(
                acceptance_id=context["acceptance_id"],
                is_deleted=False,
                platform=SocialPlatform.INSTAGRAM,
                platform_account_id=session.instagram_user_id,
                social_account__isnull=False,
            ).order_by("pk")[:2]
        )
        if len(audit_links) != 1:
            raise InvalidInvitation("The confirmed Instagram account could not be verified.")

        audit_link = audit_links[0]
        account = SocialAccount.objects.select_for_update().filter(
            pk=audit_link.social_account_id,
            is_deleted=False,
        ).first()
        if (
            account is None
            or audit_link.platform != account.platform
            or audit_link.platform_account_id != account.platform_account_id
            or account.organization_id != context["organization"].pk
            or account.platform != SocialPlatform.INSTAGRAM
            or account.platform_account_id != session.instagram_user_id
            or account.status != SocialAccountStatus.CONNECTED
            or not account.is_valid
            or not _has_active_provider_credential(account)
        ):
            raise InvalidInvitation("The confirmed Instagram account could not be verified.")
        return account

    def decline(
        self, *, selection_key, acceptance_token=None, resumption_token=None
    ):
        with transaction.atomic():
            context = self._acceptance_context_or_invalidate_stage(
                selection_key,
                acceptance_token,
                resumption_token=resumption_token,
            )
            session = (
                self._get_active_session(
                    selection_key=selection_key,
                    acceptance_id=context["acceptance_id"],
                )
                if context is not None
                else None
            )
            if session is not None:
                session.status = InvitationInstagramOAuthStatus.DECLINED
                session.declined_at = timezone.now()
                session.encrypted_access_token = ""
                session.save(update_fields=[
                    "status", "declined_at", "encrypted_access_token", "updated_at",
                ])
        if session is None:
            raise InvalidInvitation("This Instagram preview is invalid or expired.")
        return {"status": session.status}

    def _acceptance_context_or_invalidate_stage(
        self, selection_key, acceptance_token=None, *, resumption_token=None
    ):
        try:
            if resumption_token:
                from apps.social_accounts.invitations import get_invitation_acceptance_context_for_resumption

                return get_invitation_acceptance_context_for_resumption(
                    resumption_token,
                    expected_platform=SocialPlatform.INSTAGRAM,
                )
            return get_invitation_acceptance_context(acceptance_token)
        except InvalidInvitation:
            # A caller with a valid staging key but an expired/revoked claim
            # cannot retain a usable token. A wrong bearer for a still-live
            # acceptance does not invalidate the rightful recipient's session.
            session_ref = InvitationInstagramOAuthSession.objects.filter(
                selection_key=selection_key,
                is_deleted=False,
            ).values("pk", "acceptance_id").first()
            if session_ref is not None:
                try:
                    get_invitation_acceptance_context_by_id(
                        session_ref["acceptance_id"]
                    )
                except InvalidInvitation:
                    session = InvitationInstagramOAuthSession.objects.select_for_update().filter(
                        pk=session_ref["pk"],
                        status=InvitationInstagramOAuthStatus.STAGED,
                        is_deleted=False,
                    ).first()
                    if session is not None:
                        self._invalidate_session(
                            session,
                            InvitationInstagramOAuthStatus.INVALIDATED,
                        )
                        return None
                    raise
                raise
            raise

    @staticmethod
    def _safe_profile(session):
        return {
            "instagram_user_id": session.instagram_user_id,
            "username": session.username,
            "account_name": session.account_name,
            "profile_image": session.profile_image,
            "expires_at": session.expires_at,
            "status": session.status,
        }

    @classmethod
    def _get_active_session(cls, *, selection_key, acceptance_id):
        session = InvitationInstagramOAuthSession.objects.select_for_update().filter(
            selection_key=selection_key,
            acceptance_id=acceptance_id,
            is_deleted=False,
        ).first()
        if session is None:
            raise InvalidInvitation("This Instagram preview is invalid or expired.")
        now = timezone.now()
        if session.status != InvitationInstagramOAuthStatus.STAGED:
            raise InvalidInvitation("This Instagram preview is no longer available.")
        if session.expires_at <= now or session.token_expires_at <= now:
            cls._invalidate_session(session, InvitationInstagramOAuthStatus.EXPIRED)
            return None
        attempt = session.oauth_attempt
        if (
            attempt.is_deleted
            or attempt.platform != SocialPlatform.INSTAGRAM
            or attempt.acceptance_id != acceptance_id
            or attempt.consumed_at is None
        ):
            cls._invalidate_session(session, InvitationInstagramOAuthStatus.INVALIDATED)
            return None
        if attempt.expires_at <= now:
            cls._invalidate_session(session, InvitationInstagramOAuthStatus.EXPIRED)
            return None
        return session

    @staticmethod
    @transaction.atomic
    def _cleanup_expired_session(selection_key):
        session = InvitationInstagramOAuthSession.objects.select_for_update().filter(
            selection_key=selection_key,
            status=InvitationInstagramOAuthStatus.STAGED,
            is_deleted=False,
        ).first()
        if session is None:
            return
        now = timezone.now()
        if (
            session.expires_at <= now
            or session.token_expires_at <= now
            or session.oauth_attempt.expires_at <= now
        ):
            InvitationInstagramOAuthService._invalidate_session(
                session,
                InvitationInstagramOAuthStatus.EXPIRED,
            )

    @staticmethod
    def _invalidate_session(session, status):
        session.status = status
        session.invalidated_at = timezone.now()
        session.encrypted_access_token = ""
        session.save(update_fields=[
            "status", "invalidated_at", "encrypted_access_token", "updated_at",
        ])
