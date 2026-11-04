from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from threading import Barrier
from urllib.parse import parse_qs, urlparse
from unittest import skipUnless
from unittest.mock import MagicMock, patch
from uuid import uuid4

from cryptography.fernet import Fernet
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.invitations import (
    InvalidInvitation,
    cancel_invitation_acceptance,
    claim_invitation,
    create_invitation,
    create_invitation_oauth_attempt,
    consume_invitation_oauth_attempt,
    mark_email_invitation_sent,
    platform_resumption_url,
    prepare_email_invitation_delivery,
    resume_invitation_platform,
    revoke_invitation,
)
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountInvitationAcceptanceAccount,
    SocialAccountInvitationMode,
    SocialAccountInvitationOAuthAttempt,
    SocialAccountInvitationStatus,
    SocialAccountStatus,
    SocialPlatform,
)

from .crypto import decrypt_token
from .exceptions import InstagramIntegrationError
from .invitation_oauth import InvitationInstagramOAuthService
from .models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
    InvitationInstagramOAuthSession,
    InvitationInstagramOAuthStatus,
)
from .services import InstagramOAuthResult, InstagramOAuthService


@override_settings(
    INSTAGRAM_APP_ID="instagram-invitation-test-app",
    INSTAGRAM_APP_SECRET="instagram-invitation-test-secret",
    INSTAGRAM_OAUTH_REDIRECT_URI="https://api.example.test/api/integrations/instagram/oauth/callback/",
    INSTAGRAM_INVITATION_OAUTH_REDIRECT_URI=(
        "https://api.example.test/api/integrations/instagram/invitation/oauth/callback/"
    ),
    FRONTEND_URL="https://crm.example.test",
)
class InvitationInstagramOAuthTests(TestCase):
    def setUp(self):
        self.enterContext(
            self.settings(META_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode())
        )
        self.owner = User.objects.create_user(
            email="invitation-instagram-owner@example.test",
            password="test-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORGINVIG01",
            name="Invitation Instagram Test",
            slug="invitation-instagram-test",
            industry="Testing",
            created_by=self.owner,
        )
        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.INSTAGRAM],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        self.invitation = created["invitation"]
        self.invitation_token = created["share_url"].split("#", 1)[1]
        self.acceptance, self.acceptance_token = claim_invitation(
            self.invitation_token,
            [SocialPlatform.INSTAGRAM],
        )
        self.client = APIClient()

    @staticmethod
    def provider_result(
        *,
        user_id="instagram-user-1",
        access_token="synthetic-instagram-token",
    ):
        return InstagramOAuthResult(
            instagram_user_id=user_id,
            username="preview_user",
            account_name="Preview Account",
            profile_image="https://cdn.example.test/profile.jpg",
            access_token=access_token,
            token_expires_at=timezone.now() + timedelta(days=30),
        )

    def staged_session(self, *, user_id="instagram-user-1"):
        attempt, raw_state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        callback_context = consume_invitation_oauth_attempt(
            raw_state,
            expected_platform=SocialPlatform.INSTAGRAM,
        )
        session = InvitationInstagramOAuthService()._persist_staging_session(
            callback_context,
            self.provider_result(user_id=user_id),
        )
        return attempt, session

    def selection_payload(self, session):
        return {
            "acceptance_token": self.acceptance_token,
            "selection_key": str(session.selection_key),
        }

    def test_anonymous_start_uses_invitation_scope_and_existing_instagram_permissions(self):
        response = self.client.post(
            reverse("instagram-invitation-oauth-start"),
            {"acceptance_token": self.acceptance_token},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        authorization_url = response.data["data"]["authorization_url"]
        params = parse_qs(urlparse(authorization_url).query)
        self.assertEqual(params["client_id"], ["instagram-invitation-test-app"])
        self.assertEqual(params["redirect_uri"], [
            "https://api.example.test/api/integrations/instagram/invitation/oauth/callback/"
        ])
        self.assertEqual(params["scope"], [
            "instagram_business_basic,instagram_business_content_publish,"
            "instagram_business_manage_insights"
        ])
        attempt = SocialAccountInvitationOAuthAttempt.objects.get(
            acceptance=self.acceptance,
            platform=SocialPlatform.INSTAGRAM,
        )
        self.assertNotEqual(attempt.state_hash, params["state"][0])
        self.assertNotIn(self.acceptance_token, authorization_url)

    def test_preview_endpoint_restores_email_cta_without_acceptance_token(self):
        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.INSTAGRAM],
            mode=SocialAccountInvitationMode.EMAIL,
            recipient_email="instagram-client@example.test",
        )
        invitation = created["invitation"]
        delivery = prepare_email_invitation_delivery(invitation)
        self.assertTrue(mark_email_invitation_sent(invitation, delivery["attempt_id"]))
        invitation.refresh_from_db()
        link = platform_resumption_url(
            invitation, delivery["token"], SocialPlatform.INSTAGRAM
        )
        resumption_token = parse_qs(urlparse(link).fragment)["resume"][0]
        resumed = resume_invitation_platform(
            resumption_token,
            expected_platform=SocialPlatform.INSTAGRAM,
        )
        start = self.client.post(
            reverse("instagram-invitation-oauth-start"),
            {"resumption_token": resumption_token},
            format="json",
        )
        self.assertEqual(start.status_code, 200, start.data)
        authorization_url = start.data["data"]["authorization_url"]
        state = parse_qs(urlparse(authorization_url).query)["state"][0]
        callback_context = consume_invitation_oauth_attempt(
            state,
            expected_platform=SocialPlatform.INSTAGRAM,
        )
        session = InvitationInstagramOAuthService()._persist_staging_session(
            callback_context,
            self.provider_result(user_id="resumed-instagram-user"),
        )
        self.assertEqual(session.acceptance_id, resumed["acceptance_id"])

        response = self.client.post(
            reverse("instagram-invitation-oauth-preview"),
            {
                "resumption_token": resumption_token,
                "selection_key": str(session.selection_key),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["data"]["instagram_user_id"],
            "resumed-instagram-user",
        )

    def test_oauth_start_rejects_unselected_instagram_scope(self):
        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _facebook_acceptance, token = claim_invitation(
            created["share_url"].split("#", 1)[1],
            [SocialPlatform.FACEBOOK],
        )

        response = self.client.post(
            reverse("instagram-invitation-oauth-start"),
            {"acceptance_token": token},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_valid_callback_stages_profile_without_creating_permanent_records(self):
        _attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        expected = self.provider_result()
        with patch.object(
            InstagramOAuthService,
            "exchange_and_fetch_profile",
            return_value=expected,
        ) as exchange:
            response = self.client.get(
                reverse("instagram-invitation-oauth-callback"),
                {"state": state, "code": "private-instagram-code"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("instagram_invitation_oauth=preview", response["Location"])
        self.assertNotIn("private-instagram-code", response["Location"])
        session = InvitationInstagramOAuthSession.objects.get(
            acceptance=self.acceptance,
        )
        self.assertEqual(session.status, InvitationInstagramOAuthStatus.STAGED)
        self.assertNotEqual(session.encrypted_access_token, expected.access_token)
        self.assertEqual(decrypt_token(session.encrypted_access_token), expected.access_token)
        self.assertFalse(SocialAccount.objects.exists())
        self.assertFalse(InstagramAccountCredential.objects.exists())
        exchange.assert_called_once()

    def test_provider_cancellation_consumes_state_without_staging(self):
        attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        with patch.object(InstagramOAuthService, "exchange_and_fetch_profile") as exchange:
            response = self.client.get(
                reverse("instagram-invitation-oauth-callback"),
                {"state": state, "error": "access_denied"},
            )
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.consumed_at)
        self.assertIn("instagram_invitation_oauth=cancelled", response["Location"])
        exchange.assert_not_called()
        self.assertFalse(InvitationInstagramOAuthSession.objects.exists())

    def test_shared_exchange_profile_adapter_is_provider_only(self):
        service = InstagramOAuthService()
        service.client.exchange_code = MagicMock(return_value={"access_token": "short-token"})
        service.client.exchange_long_lived_token = MagicMock(
            return_value={"access_token": "long-token", "expires_in": 3600}
        )
        service.client.get_profile = MagicMock(
            return_value={
                "id": "instagram-profile-1",
                "username": "profile_user",
                "name": "Profile Name",
                "profile_picture_url": "https://cdn.example.test/profile.jpg",
            }
        )
        invitation_redirect = (
            "https://api.example.test/api/integrations/instagram/invitation/oauth/callback/"
        )

        result = service.exchange_and_fetch_profile(
            code="private-code",
            redirect_uri=invitation_redirect,
        )

        service.client.exchange_code.assert_called_once_with(
            code="private-code",
            redirect_uri=invitation_redirect,
        )
        service.client.exchange_long_lived_token.assert_called_once_with(
            short_lived_token="short-token",
        )
        service.client.get_profile.assert_called_once_with(access_token="long-token")
        self.assertEqual(result.instagram_user_id, "instagram-profile-1")
        self.assertEqual(result.access_token, "long-token")
        self.assertFalse(SocialAccount.objects.exists())
        self.assertFalse(InstagramAccountCredential.objects.exists())

    def test_provider_failure_is_sanitized_and_does_not_stage(self):
        _attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        with patch.object(
            InstagramOAuthService,
            "exchange_and_fetch_profile",
            side_effect=InstagramIntegrationError(
                "provider echoed private-code and access-token-canary"
            ),
        ):
            response = self.client.get(
                reverse("instagram-invitation-oauth-callback"),
                {"state": state, "code": "private-code"},
            )
        self.assertIn("instagram_invitation_oauth=error", response["Location"])
        for secret in ("private-code", "access-token-canary", self.acceptance_token):
            self.assertNotIn(secret, response["Location"])
        self.assertFalse(InvitationInstagramOAuthSession.objects.exists())

    def test_invalid_expired_and_replayed_states_are_rejected(self):
        endpoint = reverse("instagram-invitation-oauth-callback")
        invalid = self.client.get(endpoint, {"state": "tampered", "code": "x"})
        self.assertIn("instagram_invitation_oauth=error", invalid["Location"])

        attempt, expired_state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=["expires_at"])
        expired = self.client.get(endpoint, {"state": expired_state, "code": "x"})
        self.assertIn("instagram_invitation_oauth=error", expired["Location"])

        _attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        with patch.object(
            InstagramOAuthService,
            "exchange_and_fetch_profile",
            return_value=self.provider_result(),
        ):
            first = self.client.get(endpoint, {"state": state, "code": "x"})
        replay = self.client.get(endpoint, {"state": state, "code": "x"})
        self.assertIn("instagram_invitation_oauth=preview", first["Location"])
        self.assertIn("instagram_invitation_oauth=error", replay["Location"])

    def test_preview_contains_safe_profile_metadata_only(self):
        _attempt, session = self.staged_session()
        response = self.client.post(
            reverse("instagram-invitation-oauth-preview"),
            self.selection_payload(session),
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["instagram_user_id"], "instagram-user-1")
        serialized = str(response.data)
        for secret in ("synthetic-instagram-token", session.encrypted_access_token):
            self.assertNotIn(secret, serialized)
        self.assertFalse(SocialAccount.objects.exists())
        self.assertFalse(InstagramAccountCredential.objects.exists())

    def test_confirmation_persists_account_credential_and_audit_link(self):
        _attempt, session = self.staged_session()
        payload = self.selection_payload(session)
        payload["organization_id"] = "CLIENT_CANNOT_CHOOSE_ORG"
        response = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        account = SocialAccount.objects.get(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-user-1",
        )
        self.assertEqual(account.status, SocialAccountStatus.CONNECTED)
        credential = InstagramAccountCredential.objects.get(social_account=account)
        self.assertEqual(credential.status, InstagramCredentialStatus.ACTIVE)
        self.assertEqual(decrypt_token(credential.encrypted_access_token), "synthetic-instagram-token")
        self.assertTrue(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=self.acceptance,
                social_account=account,
            ).exists()
        )
        session.refresh_from_db()
        self.assertEqual(session.status, InvitationInstagramOAuthStatus.CONFIRMED)
        self.assertEqual(session.encrypted_access_token, "")
        self.acceptance.refresh_from_db()
        self.assertEqual(self.acceptance.status, "active")

    def test_confirmation_replay_is_idempotent_and_does_not_increment_usage(self):
        _attempt, session = self.staged_session()
        endpoint = reverse("instagram-invitation-oauth-confirm")
        first = self.client.post(endpoint, self.selection_payload(session), format="json")
        replay = self.client.post(endpoint, self.selection_payload(session), format="json")

        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(first.data["data"], replay.data["data"])
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertEqual(InstagramAccountCredential.objects.count(), 1)
        self.assertEqual(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=self.acceptance
            ).count(),
            1,
        )
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.usage_count, 0)

    def test_confirmation_retry_succeeds_when_first_response_is_lost(self):
        _attempt, session = self.staged_session()
        first_result = InvitationInstagramOAuthService().confirm(
            selection_key=session.selection_key,
            acceptance_token=self.acceptance_token,
        )
        # The service transaction committed, but the first result is treated as
        # lost; retry through the public endpoint must return the same account.
        retry = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            self.selection_payload(session),
            format="json",
        )

        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(retry.data["data"]["id"], first_result["id"])
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertEqual(InstagramAccountCredential.objects.count(), 1)
        self.assertEqual(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=self.acceptance
            ).count(),
            1,
        )

    def test_confirmed_retry_requires_matching_audit_association(self):
        _attempt, session = self.staged_session()
        endpoint = reverse("instagram-invitation-oauth-confirm")
        self.assertEqual(
            self.client.post(endpoint, self.selection_payload(session), format="json").status_code,
            200,
        )
        association = SocialAccountInvitationAcceptanceAccount.objects.get(
            acceptance=self.acceptance
        )
        association.platform_account_id = "different-provider-account"
        association.save(update_fields=["platform_account_id", "updated_at"])

        retry = self.client.post(endpoint, self.selection_payload(session), format="json")

        self.assertEqual(retry.status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 1)

    def test_confirmed_retry_rejects_missing_audit_association(self):
        _attempt, session = self.staged_session()
        endpoint = reverse("instagram-invitation-oauth-confirm")
        self.assertEqual(
            self.client.post(endpoint, self.selection_payload(session), format="json").status_code,
            200,
        )
        SocialAccountInvitationAcceptanceAccount.objects.filter(
            acceptance=self.acceptance
        ).delete()

        retry = self.client.post(endpoint, self.selection_payload(session), format="json")

        self.assertEqual(retry.status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 1)

    def test_confirmed_retry_rejects_account_outside_invited_organization(self):
        _attempt, session = self.staged_session()
        endpoint = reverse("instagram-invitation-oauth-confirm")
        self.assertEqual(
            self.client.post(endpoint, self.selection_payload(session), format="json").status_code,
            200,
        )
        account = SocialAccount.objects.get(platform_account_id="instagram-user-1")
        other_owner = User.objects.create_user(
            email="instagram-confirm-other@example.test",
            password="test-password",
        )
        other_organization = Organization.objects.create(
            organization_id="ORGINVCF01",
            name="Other Confirmation Organization",
            slug="other-confirmation-organization",
            industry="Testing",
            created_by=other_owner,
        )
        account.organization = other_organization
        account.save(update_fields=["organization", "updated_at"])

        retry = self.client.post(endpoint, self.selection_payload(session), format="json")

        self.assertEqual(retry.status_code, 400)

    def test_confirmed_retry_rejects_mismatched_provider_account_id(self):
        _attempt, session = self.staged_session()
        endpoint = reverse("instagram-invitation-oauth-confirm")
        self.assertEqual(
            self.client.post(endpoint, self.selection_payload(session), format="json").status_code,
            200,
        )
        session.instagram_user_id = "different-instagram-user"
        session.save(update_fields=["instagram_user_id", "updated_at"])

        retry = self.client.post(endpoint, self.selection_payload(session), format="json")

        self.assertEqual(retry.status_code, 400)

    def test_confirmed_retry_rejects_expired_or_revoked_acceptance(self):
        endpoint = reverse("instagram-invitation-oauth-confirm")
        _attempt, expired_session = self.staged_session(user_id="instagram-expired-user")
        self.assertEqual(
            self.client.post(
                endpoint, self.selection_payload(expired_session), format="json"
            ).status_code,
            200,
        )
        self.acceptance.expires_at = timezone.now() - timedelta(seconds=1)
        self.acceptance.save(update_fields=["expires_at"])
        expired_retry = self.client.post(
            endpoint, self.selection_payload(expired_session), format="json"
        )
        self.assertEqual(expired_retry.status_code, 400)

        self.invitation.status = SocialAccountInvitationStatus.PENDING
        self.invitation.expires_at = timezone.now() + timedelta(days=1)
        self.invitation.save(update_fields=["status", "expires_at"])
        self.acceptance.expires_at = timezone.now() + timedelta(minutes=20)
        self.acceptance.save(update_fields=["expires_at"])
        _attempt, revoked_session = self.staged_session(
            user_id="instagram-revoked-user"
        )
        self.assertEqual(
            self.client.post(
                endpoint, self.selection_payload(revoked_session), format="json"
            ).status_code,
            200,
        )
        revoke_invitation(self.invitation)
        revoked_retry = self.client.post(
            endpoint, self.selection_payload(revoked_session), format="json"
        )
        self.assertEqual(revoked_retry.status_code, 400)

    def test_duplicate_existing_account_is_reused_and_credential_reactivated(self):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-user-1",
            account_name="Old Name",
            username="old_name",
            status=SocialAccountStatus.DISCONNECTED,
            is_valid=False,
        )
        credential = InstagramAccountCredential.objects.create(
            social_account=account,
            encrypted_access_token="old-ciphertext",
            token_expires_at=timezone.now() - timedelta(days=1),
            status=InstagramCredentialStatus.REVOKED,
        )
        _attempt, session = self.staged_session()

        response = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            self.selection_payload(session),
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(SocialAccount.objects.count(), 1)
        account.refresh_from_db()
        credential.refresh_from_db()
        self.assertEqual(account.status, SocialAccountStatus.CONNECTED)
        self.assertEqual(credential.status, InstagramCredentialStatus.ACTIVE)
        self.assertEqual(decrypt_token(credential.encrypted_access_token), "synthetic-instagram-token")

    def test_decline_clears_staged_token_and_blocks_confirmation(self):
        _attempt, session = self.staged_session()
        declined = self.client.post(
            reverse("instagram-invitation-oauth-decline"),
            self.selection_payload(session),
            format="json",
        )
        confirm = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            self.selection_payload(session),
            format="json",
        )

        self.assertEqual(declined.status_code, 200, declined.data)
        self.assertEqual(confirm.status_code, 400)
        session.refresh_from_db()
        self.assertEqual(session.status, InvitationInstagramOAuthStatus.DECLINED)
        self.assertEqual(session.encrypted_access_token, "")
        self.assertFalse(SocialAccount.objects.exists())

    def test_expired_staging_data_is_cleared_and_cannot_be_confirmed(self):
        _attempt, session = self.staged_session()
        session.expires_at = timezone.now() - timedelta(seconds=1)
        session.save(update_fields=["expires_at"])

        response = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            self.selection_payload(session),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        session.refresh_from_db()
        self.assertEqual(session.status, InvitationInstagramOAuthStatus.EXPIRED)
        self.assertEqual(session.encrypted_access_token, "")
        self.assertFalse(SocialAccount.objects.exists())

    def test_revocation_and_cancellation_invalidate_staged_tokens(self):
        _attempt, revoked_session = self.staged_session()
        revoke_invitation(self.invitation)
        revoked_session.refresh_from_db()
        self.assertEqual(revoked_session.status, InvitationInstagramOAuthStatus.INVALIDATED)
        self.assertEqual(revoked_session.encrypted_access_token, "")

        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.INSTAGRAM],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _acceptance, token = claim_invitation(
            created["share_url"].split("#", 1)[1],
            [SocialPlatform.INSTAGRAM],
        )
        attempt, state = create_invitation_oauth_attempt(token, SocialPlatform.INSTAGRAM)
        context = consume_invitation_oauth_attempt(state, expected_platform="instagram")
        cancelled_session = InvitationInstagramOAuthService()._persist_staging_session(
            context,
            self.provider_result(user_id="instagram-user-cancelled"),
        )
        cancel_invitation_acceptance(token)
        cancelled_session.refresh_from_db()
        self.assertEqual(cancelled_session.status, InvitationInstagramOAuthStatus.INVALIDATED)
        self.assertEqual(cancelled_session.encrypted_access_token, "")

    def test_cross_organization_staging_key_is_rejected(self):
        _attempt, session = self.staged_session()
        other_owner = User.objects.create_user(
            email="invitation-instagram-other@example.test",
            password="test-password",
        )
        other_org = Organization.objects.create(
            organization_id="ORGINVIG02",
            name="Other Instagram Invitation",
            slug="other-instagram-invitation",
            industry="Testing",
            created_by=other_owner,
        )
        created = create_invitation(
            organization=other_org,
            inviter=other_owner,
            platforms=[SocialPlatform.INSTAGRAM],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _other_acceptance, other_token = claim_invitation(
            created["share_url"].split("#", 1)[1],
            [SocialPlatform.INSTAGRAM],
        )

        response = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            {
                "acceptance_token": other_token,
                "selection_key": str(session.selection_key),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(SocialAccount.objects.exists())

    def test_confirmation_failure_rolls_back_account_credential_and_stage_consumption(self):
        _attempt, session = self.staged_session()
        with patch(
            "apps.social_accounts.invitations.SocialAccountInvitationAcceptanceAccount.objects.get_or_create",
            side_effect=RuntimeError("synthetic audit failure"),
        ):
            with self.assertRaises(RuntimeError):
                InvitationInstagramOAuthService().confirm(
                    selection_key=session.selection_key,
                    acceptance_token=self.acceptance_token,
                )

        self.assertFalse(SocialAccount.objects.exists())
        self.assertFalse(InstagramAccountCredential.objects.exists())
        session.refresh_from_db()
        self.assertEqual(session.status, InvitationInstagramOAuthStatus.STAGED)
        self.assertTrue(session.encrypted_access_token)

        retry = self.client.post(
            reverse("instagram-invitation-oauth-confirm"),
            self.selection_payload(session),
            format="json",
        )
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(SocialAccount.objects.count(), 1)


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row-lock semantics")
@override_settings(
    INSTAGRAM_APP_ID="instagram-invitation-test-app",
    INSTAGRAM_APP_SECRET="instagram-invitation-test-secret",
    INSTAGRAM_OAUTH_REDIRECT_URI="https://api.example.test/instagram/callback/",
    INSTAGRAM_INVITATION_OAUTH_REDIRECT_URI="https://api.example.test/instagram/invitation/callback/",
    META_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode(),
)
class InvitationInstagramConcurrentConfirmationTests(TransactionTestCase):
    def test_concurrent_confirmation_persists_one_account(self):
        owner = User.objects.create_user(
            email="instagram-concurrent-owner@example.test",
            password="test-password",
        )
        organization = Organization.objects.create(
            organization_id="ORGINVIG03",
            name="Concurrent Instagram Invitation",
            slug="concurrent-instagram-invitation",
            industry="Testing",
            created_by=owner,
        )
        invitation = create_invitation(
            organization=organization,
            inviter=owner,
            platforms=[SocialPlatform.INSTAGRAM],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _acceptance, acceptance_token = claim_invitation(
            invitation["share_url"].split("#", 1)[1],
            [SocialPlatform.INSTAGRAM],
        )
        attempt, state = create_invitation_oauth_attempt(
            acceptance_token,
            SocialPlatform.INSTAGRAM,
        )
        callback_context = consume_invitation_oauth_attempt(
            state,
            expected_platform=SocialPlatform.INSTAGRAM,
        )
        session = InvitationInstagramOAuthService()._persist_staging_session(
            callback_context,
            InstagramOAuthResult(
                instagram_user_id="instagram-concurrent-user",
                username="concurrent",
                account_name="Concurrent",
                profile_image="https://cdn.example.test/concurrent.jpg",
                access_token="concurrent-token",
                token_expires_at=timezone.now() + timedelta(days=30),
            ),
        )
        barrier = Barrier(2)

        def confirm_once():
            close_old_connections()
            barrier.wait()
            try:
                result = InvitationInstagramOAuthService().confirm(
                    selection_key=session.selection_key,
                    acceptance_token=acceptance_token,
                )
                return ("confirmed", result["instagram_user_id"])
            except InvalidInvitation:
                return ("rejected", None)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _index: confirm_once(), range(2)))

        self.assertEqual(sum(outcome[0] == "confirmed" for outcome in outcomes), 2)
        self.assertEqual(sum(outcome[0] == "rejected" for outcome in outcomes), 0)
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=organization,
                platform=SocialPlatform.INSTAGRAM,
                platform_account_id="instagram-concurrent-user",
            ).count(),
            1,
        )
