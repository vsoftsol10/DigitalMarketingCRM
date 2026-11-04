from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from cryptography.fernet import Fernet
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.invitations import (
    InvalidInvitation,
    claim_invitation,
    complete_invitation_acceptance,
    create_invitation,
    create_invitation_oauth_attempt,
    create_invitation_oauth_attempt_for_resumption,
    mark_email_invitation_sent,
    platform_resumption_url,
    prepare_email_invitation_delivery,
    resume_invitation_platform,
    consume_invitation_oauth_attempt,
)
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountInvitationAcceptance,
    SocialAccountInvitationAcceptanceAccount,
    SocialAccountInvitationOAuthAttempt,
    SocialAccountInvitationMode,
    SocialAccountInvitationStatus,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialConnectionStatus,
    SocialPlatform,
)

from .invitation_oauth import InvitationMetaOAuthService
from .models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
)
from .services import MetaAccountData


@override_settings(
    META_APP_ID="test-meta-app",
    META_APP_SECRET="test-meta-secret",
    META_BUSINESS_LOGIN_CONFIG_ID="test-meta-config",
    META_INVITATION_OAUTH_REDIRECT_URI=(
        "https://api.example.test/api/integrations/meta/invitation/oauth/callback/"
    ),
    META_OAUTH_REDIRECT_URI="https://api.example.test/api/integrations/meta/oauth/callback/",
    FRONTEND_URL="https://crm.example.test",
)
class InvitationMetaOAuthTests(TestCase):
    def setUp(self):
        self.enterContext(
            self.settings(META_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode())
        )
        self.owner = User.objects.create_user(
            email="invitation-meta-owner@example.test",
            password="test-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORGINVMETA1",
            name="Invitation Meta Test",
            slug="invitation-meta-test",
            industry="Testing",
            created_by=self.owner,
        )
        self.client = APIClient()
        result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        self.invitation = result["invitation"]
        self.invitation_token = result["share_url"].split("#", 1)[1]
        self.acceptance, self.acceptance_token = claim_invitation(
            self.invitation_token,
            [SocialPlatform.FACEBOOK],
        )

    @staticmethod
    def pages(*page_ids):
        return [
            MetaAccountData(
                platform=SocialPlatform.FACEBOOK,
                platform_account_id=page_id,
                account_name=f"Page {page_id}",
                profile_image=f"https://images.example.test/{page_id}.png",
                access_token=f"page-token-{page_id}",
            )
            for page_id in page_ids
        ]

    @staticmethod
    def create_existing_page(organization, page_id):
        connection = SocialConnection.objects.create(
            organization=organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=f"existing-user-{page_id}",
            status=SocialConnectionStatus.ACTIVE,
        )
        account = SocialAccount.objects.create(
            organization=organization,
            connection=connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=f"Existing {page_id}",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token=f"existing-page-token-{page_id}",
            status=MetaCredentialStatus.ACTIVE,
        )
        MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token=f"existing-user-token-{page_id}",
            status=MetaCredentialStatus.ACTIVE,
        )
        return account

    def oauth_session(self, *page_ids):
        attempt, _state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        callback_context = consume_invitation_oauth_attempt(
            _state,
            expected_platform=SocialPlatform.FACEBOOK,
        )
        service = InvitationMetaOAuthService()
        session = service._persist_selection_session(
            callback_context=callback_context,
            provider_user_id="meta-user-1",
            user_access_token="meta-user-token",
            accounts=self.pages(*page_ids),
            token_expires_at=timezone.now() + timedelta(hours=1),
        )
        return attempt, session

    def test_anonymous_oauth_start_uses_invitation_scope_and_existing_meta_config(self):
        response = self.client.post(
            reverse("meta-invitation-oauth-start"),
            {"acceptance_token": self.acceptance_token},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        authorization_url = response.data["data"]["authorization_url"]
        params = parse_qs(urlparse(authorization_url).query)
        self.assertEqual(params["client_id"], ["test-meta-app"])
        self.assertEqual(params["config_id"], ["test-meta-config"])

    def test_platform_resumption_start_reuses_combined_email_acceptance(self):
        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            mode=SocialAccountInvitationMode.EMAIL,
            recipient_email="client@example.test",
            platforms=[SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM],
        )
        invitation = created["invitation"]
        delivery = prepare_email_invitation_delivery(invitation)
        self.assertTrue(mark_email_invitation_sent(invitation, delivery["attempt_id"]))
        invitation.refresh_from_db()
        facebook_url = platform_resumption_url(
            invitation, delivery["token"], SocialPlatform.FACEBOOK
        )
        instagram_url = platform_resumption_url(
            invitation, delivery["token"], SocialPlatform.INSTAGRAM
        )
        facebook_token = parse_qs(urlparse(facebook_url).fragment)["resume"][0]
        instagram_token = parse_qs(urlparse(instagram_url).fragment)["resume"][0]

        response = self.client.post(
            reverse("meta-invitation-oauth-start"),
            {"resumption_token": facebook_token},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        authorization_url = response.data["data"]["authorization_url"]
        params = parse_qs(urlparse(authorization_url).query)
        self.assertEqual(
            set(response.data["data"]["invitation"]["selected_platforms"]),
            {SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM},
        )
        resumed = resume_invitation_platform(
            instagram_token,
            expected_platform=SocialPlatform.INSTAGRAM,
        )
        self.assertEqual(
            SocialAccountInvitationAcceptance.objects.filter(
                invitation=invitation,
                status="active",
                is_deleted=False,
            ).count(),
            1,
        )
        self.assertEqual(
            resumed["acceptance_id"],
            SocialAccountInvitationAcceptance.objects.get(
                invitation=invitation,
                status="active",
                is_deleted=False,
            ).pk,
        )
        self.assertEqual(params["redirect_uri"], [
            "https://api.example.test/api/integrations/meta/invitation/oauth/callback/"
        ])
        self.assertNotIn(delivery["token"], authorization_url)
        attempt = SocialAccountInvitationOAuthAttempt.objects.get(
            acceptance_id=resumed["acceptance_id"],
            platform=SocialPlatform.FACEBOOK,
            state_hash__isnull=False,
        )
        self.assertEqual(attempt.acceptance_id, resumed["acceptance_id"])
        self.assertNotEqual(attempt.state_hash, params["state"][0])

    def test_page_selection_endpoint_accepts_platform_resumption_credential(self):
        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            mode=SocialAccountInvitationMode.EMAIL,
            recipient_email="pages-client@example.test",
            platforms=[SocialPlatform.FACEBOOK],
        )
        invitation = created["invitation"]
        delivery = prepare_email_invitation_delivery(invitation)
        self.assertTrue(mark_email_invitation_sent(invitation, delivery["attempt_id"]))
        invitation.refresh_from_db()
        link = platform_resumption_url(
            invitation, delivery["token"], SocialPlatform.FACEBOOK
        )
        resumption_token = parse_qs(urlparse(link).fragment)["resume"][0]
        _attempt, state, _context = create_invitation_oauth_attempt_for_resumption(
            resumption_token,
            platform=SocialPlatform.FACEBOOK,
        )
        callback_context = consume_invitation_oauth_attempt(
            state,
            expected_platform=SocialPlatform.FACEBOOK,
        )
        selection = InvitationMetaOAuthService()._persist_selection_session(
            callback_context=callback_context,
            provider_user_id="resumed-meta-user",
            user_access_token="resumed-meta-user-token",
            accounts=self.pages("resumed-page-id"),
            token_expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(
            reverse("meta-invitation-oauth-selection"),
            {
                "resumption_token": resumption_token,
                "selection_key": str(selection.selection_key),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["pages"][0]["id"], "resumed-page-id")

    def test_start_rejects_expired_revoked_or_unselected_acceptance(self):
        endpoint = reverse("meta-invitation-oauth-start")
        self.acceptance.expires_at = timezone.now() - timedelta(seconds=1)
        self.acceptance.save(update_fields=["expires_at"])
        expired = self.client.post(
            endpoint, {"acceptance_token": self.acceptance_token}, format="json"
        )
        self.assertEqual(expired.status_code, 400)

        self.acceptance.expires_at = timezone.now() + timedelta(minutes=30)
        self.acceptance.save(update_fields=["expires_at"])
        self.invitation.status = SocialAccountInvitationStatus.REVOKED
        self.invitation.save(update_fields=["status"])
        revoked = self.client.post(
            endpoint, {"acceptance_token": self.acceptance_token}, format="json"
        )
        self.assertEqual(revoked.status_code, 400)

        instagram_invitation = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.INSTAGRAM],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _instagram_acceptance, instagram_token = claim_invitation(
            instagram_invitation["share_url"].split("#", 1)[1],
            [SocialPlatform.INSTAGRAM],
        )
        unselected = self.client.post(
            endpoint, {"acceptance_token": instagram_token}, format="json"
        )
        self.assertEqual(unselected.status_code, 400)

    def test_valid_callback_consumes_state_and_does_not_echo_code_or_state(self):
        attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        selection_key = uuid4()
        with self.patch_selection_session(selection_key):
            response = self.client.get(
                reverse("meta-invitation-oauth-callback"),
                {"state": state, "code": "private-oauth-code"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"selection_key={selection_key}", response["Location"])
        self.assertNotIn("private-oauth-code", response["Location"])
        self.assertNotIn(state, response["Location"])
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.consumed_at)

    def test_callback_provider_failure_redirects_without_echoing_secrets(self):
        from unittest.mock import patch

        from .exceptions import MetaAPIError

        _attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        secret_code = "private-oauth-code-canary"
        with patch.object(
            InvitationMetaOAuthService,
            "create_selection_session",
            side_effect=MetaAPIError(
                f"provider echoed {secret_code} test-meta-secret",
                status_code=400,
                error_payload={"error": {"code": 190, "message": secret_code}},
            ),
        ):
            response = self.client.get(
                reverse("meta-invitation-oauth-callback"),
                {"state": state, "code": secret_code},
            )

        self.assertIn("meta_oauth=error", response["Location"])
        self.assertNotIn(secret_code, response["Location"])
        self.assertNotIn("test-meta-secret", response["Location"])

    def patch_selection_session(self, selection_key):
        from unittest.mock import patch
        from types import SimpleNamespace

        return patch.object(
            InvitationMetaOAuthService,
            "create_selection_session",
            return_value=SimpleNamespace(selection_key=selection_key),
        )

    def test_callback_cancellation_consumes_attempt_without_provider_exchange(self):
        attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        from unittest.mock import patch

        with patch.object(InvitationMetaOAuthService, "create_selection_session") as create:
            response = self.client.get(
                reverse("meta-invitation-oauth-callback"),
                {"state": state, "error": "access_denied"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("meta_oauth=cancelled", response["Location"])
        create.assert_not_called()
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.consumed_at)

    def test_invalid_expired_and_replayed_callback_states_are_rejected(self):
        endpoint = reverse("meta-invitation-oauth-callback")
        invalid = self.client.get(endpoint, {"state": "tampered-state", "code": "x"})
        self.assertEqual(invalid.status_code, 302)

        attempt, expired_state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=["expires_at"])
        expired = self.client.get(
            endpoint, {"state": expired_state, "code": "x"}
        )
        self.assertEqual(expired.status_code, 302)

        attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        with self.patch_selection_session(uuid4()):
            first = self.client.get(endpoint, {"state": state, "code": "x"})
        replay = self.client.get(endpoint, {"state": state, "code": "x"})
        self.assertIn("meta_oauth=selection", first["Location"])
        self.assertIn("meta_oauth=error", replay["Location"])

    def test_callback_state_is_invalid_after_invitation_revocation(self):
        _attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        self.invitation.status = SocialAccountInvitationStatus.REVOKED
        self.invitation.save(update_fields=["status"])

        response = self.client.get(
            reverse("meta-invitation-oauth-callback"),
            {"state": state, "code": "private-oauth-code"},
        )

        self.assertIn("meta_oauth=error", response["Location"])
        self.assertNotIn("private-oauth-code", response["Location"])

    def test_callback_reuses_existing_meta_page_discovery_and_encrypts_selection_data(self):
        from unittest.mock import patch

        attempt, state = create_invitation_oauth_attempt(
            self.acceptance_token,
            SocialPlatform.FACEBOOK,
        )
        callback_context = consume_invitation_oauth_attempt(
            state,
            expected_platform=SocialPlatform.FACEBOOK,
        )
        service = InvitationMetaOAuthService()
        discovery = type(
            "Discovery",
            (),
            {
                "provider_user_id": "meta-user-discovered",
                "accounts": self.pages("page-discovered-a", "page-discovered-b"),
            },
        )()
        with (
            patch.object(
                service.client,
                "exchange_code_for_access_token",
                return_value={
                    "access_token": "meta-user-token",
                    "expires_in": 3600,
                },
            ) as exchange,
            patch(
                "apps.integrations.meta.invitation_oauth.MetaAccountDiscoveryService"
            ) as discovery_service,
        ):
            discovery_service.return_value.discover_accounts.return_value = discovery
            session = service.create_selection_session(
                callback_context,
                "private-oauth-code",
            )

        exchange.assert_called_once_with(
            code="private-oauth-code",
            redirect_uri=(
                "https://api.example.test/api/integrations/meta/invitation/oauth/callback/"
            ),
        )
        self.assertEqual(session.oauth_attempt_id, attempt.pk)
        self.assertEqual(session.acceptance_id, self.acceptance.pk)
        self.assertNotIn("meta-user-token", session.encrypted_access_token)
        self.assertNotIn("page-token-page-discovered-a", session.encrypted_accounts)
        self.assertEqual(
            len(InvitationMetaOAuthService().get_selection_data(
                selection_key=session.selection_key,
                acceptance_token=self.acceptance_token,
            )["pages"]),
            2,
        )

    def test_page_metadata_is_returned_without_tokens_and_foreign_page_is_rejected(self):
        _attempt, session = self.oauth_session("page-a")
        self.oauth_session("page-b")
        endpoint = reverse("meta-invitation-oauth-selection")
        response = self.client.post(
            endpoint,
            {
                "selection_key": str(session.selection_key),
                "acceptance_token": self.acceptance_token,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["pages"][0]["id"], "page-a")
        self.assertNotIn("access_token", str(response.data))
        self.assertNotIn("page-token-page-a", str(response.data))
        self.assertNotIn("meta-user-token", str(response.data))

        rejected = self.client.post(
            reverse("meta-invitation-oauth-selection-add"),
            {
                "selection_key": str(session.selection_key),
                "acceptance_token": self.acceptance_token,
                "page_id": "page-b",
            },
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertFalse(SocialAccount.objects.exists())

    def test_existing_page_is_marked_connected_and_associated_idempotently(self):
        existing_page = self.create_existing_page(self.organization, "existing-page")
        other_organization = Organization.objects.create(
            organization_id="ORGINVMETA2",
            name="Other Invitation Meta Test",
            slug="other-invitation-meta-test",
            industry="Testing",
            created_by=self.owner,
        )
        self.create_existing_page(other_organization, "foreign-page")
        _attempt, session = self.oauth_session("existing-page", "foreign-page", "new-page")

        selection = InvitationMetaOAuthService().get_selection_data(
            selection_key=session.selection_key,
            acceptance_token=self.acceptance_token,
        )
        connected_by_id = {page["id"]: page["connected"] for page in selection["pages"]}
        self.assertTrue(connected_by_id["existing-page"])
        self.assertFalse(connected_by_id["foreign-page"])
        self.assertFalse(connected_by_id["new-page"])

        payload = {
            "selection_key": str(session.selection_key),
            "acceptance_token": self.acceptance_token,
            "page_id": existing_page.platform_account_id,
        }
        first = self.client.post(
            reverse("meta-invitation-oauth-selection-add"),
            payload,
            format="json",
        )
        second = self.client.post(
            reverse("meta-invitation-oauth-selection-add"),
            payload,
            format="json",
        )

        self.assertEqual(first.status_code, 200, first.data)
        self.assertTrue(first.data["data"]["already_connected"])
        self.assertEqual(second.status_code, 200, second.data)
        self.assertTrue(second.data["data"]["already_connected"])
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=self.organization,
                platform=SocialPlatform.FACEBOOK,
                platform_account_id="existing-page",
                is_deleted=False,
            ).count(),
            1,
        )
        self.assertEqual(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=self.acceptance,
                social_account=existing_page,
                is_deleted=False,
            ).count(),
            1,
        )

        completed = complete_invitation_acceptance(self.acceptance_token)
        self.assertEqual(completed.pk, self.invitation.pk)
        self.acceptance.refresh_from_db()
        self.assertEqual(self.acceptance.status, "completed")

    def test_multiple_explicit_page_additions_and_duplicate_retry(self):
        _attempt, session = self.oauth_session("page-a", "page-b")
        endpoint = reverse("meta-invitation-oauth-selection-add")
        base_payload = {
            "selection_key": str(session.selection_key),
            "acceptance_token": self.acceptance_token,
        }

        first = self.client.post(
            endpoint, {**base_payload, "page_id": "page-a"}, format="json"
        )
        second = self.client.post(
            endpoint, {**base_payload, "page_id": "page-b"}, format="json"
        )
        retry = self.client.post(
            endpoint, {**base_payload, "page_id": "page-a"}, format="json"
        )

        self.assertEqual(first.status_code, 200, first.data)
        self.assertFalse(first.data["data"]["already_connected"])
        self.assertEqual(second.status_code, 200, second.data)
        self.assertFalse(second.data["data"]["already_connected"])
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertTrue(retry.data["data"]["already_connected"])
        self.assertEqual(
            SocialAccount.objects.filter(organization=self.organization).count(), 2
        )
        self.assertEqual(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=self.acceptance
            ).count(),
            2,
        )
        session.refresh_from_db()
        self.assertGreater(session.expires_at, timezone.now())

    def test_page_addition_revalidates_invitation_and_acceptance_scope(self):
        _attempt, session = self.oauth_session("page-a")
        self.invitation.status = SocialAccountInvitationStatus.REVOKED
        self.invitation.save(update_fields=["status"])

        response = self.client.post(
            reverse("meta-invitation-oauth-selection-add"),
            {
                "selection_key": str(session.selection_key),
                "acceptance_token": self.acceptance_token,
                "page_id": "page-a",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(SocialAccount.objects.exists())

    def test_page_addition_rejects_invitation_expired_after_discovery(self):
        _attempt, session = self.oauth_session("page-a")
        self.invitation.expires_at = timezone.now() - timedelta(seconds=1)
        self.invitation.save(update_fields=["expires_at"])

        response = self.client.post(
            reverse("meta-invitation-oauth-selection-add"),
            {
                "selection_key": str(session.selection_key),
                "acceptance_token": self.acceptance_token,
                "page_id": "page-a",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(SocialAccount.objects.exists())

    def test_persisted_page_uses_existing_meta_credentials_and_acceptance_audit(self):
        _attempt, session = self.oauth_session("page-a")
        response = self.client.post(
            reverse("meta-invitation-oauth-selection-add"),
            {
                "selection_key": str(session.selection_key),
                "acceptance_token": self.acceptance_token,
                "page_id": "page-a",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        account = SocialAccount.objects.get(
            organization=self.organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="page-a",
        )
        self.assertEqual(account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(
            MetaAccountCredential.objects.filter(
                social_account=account,
                credential_type="page",
            ).exists()
        )
        self.assertTrue(
            MetaAccountCredential.objects.filter(
                social_connection=account.connection,
                credential_type="user",
            ).exists()
        )
        self.assertTrue(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=self.acceptance,
                social_account=account,
            ).exists()
        )

    def test_selection_key_cannot_be_used_with_another_acceptance(self):
        _attempt, session = self.oauth_session("page-a")
        other_result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _other_acceptance, other_token = claim_invitation(
            other_result["share_url"].split("#", 1)[1],
            [SocialPlatform.FACEBOOK],
        )

        with self.assertRaises(InvalidInvitation):
            InvitationMetaOAuthService().get_selection_data(
                selection_key=session.selection_key,
                acceptance_token=other_token,
            )

    def test_selection_key_cannot_cross_organizations(self):
        _attempt, session = self.oauth_session("page-a")
        other_owner = User.objects.create_user(
            email="other-invitation-meta-owner@example.test",
            password="test-password",
        )
        other_organization = Organization.objects.create(
            organization_id="ORGINVMETA2",
            name="Other Invitation Meta Test",
            slug="other-invitation-meta-test",
            industry="Testing",
            created_by=other_owner,
        )
        other_result = create_invitation(
            organization=other_organization,
            inviter=other_owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=SocialAccountInvitationMode.SHARE_LINK,
        )
        _other_acceptance, other_token = claim_invitation(
            other_result["share_url"].split("#", 1)[1],
            [SocialPlatform.FACEBOOK],
        )

        with self.assertRaises(InvalidInvitation):
            InvitationMetaOAuthService().get_selection_data(
                selection_key=session.selection_key,
                acceptance_token=other_token,
            )

    def test_selection_session_is_expired_with_its_oauth_attempt(self):
        attempt, session = self.oauth_session("page-a")
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=["expires_at"])

        with self.assertRaises(InvalidInvitation):
            InvitationMetaOAuthService().get_selection_data(
                selection_key=session.selection_key,
                acceptance_token=self.acceptance_token,
            )
