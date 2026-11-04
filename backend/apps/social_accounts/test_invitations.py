from concurrent.futures import ThreadPoolExecutor
import hashlib
from importlib import import_module
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.integrations.instagram.models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
    InvitationInstagramOAuthSession,
    InvitationInstagramOAuthStatus,
)
from apps.integrations.meta.models import (
    InvitationMetaOAuthSession,
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
)

from .invitations import (
    InvitationError,
    IncompleteInvitation,
    InvalidInvitation,
    claim_invitation,
    cancel_invitation_acceptance,
    cleanup_expired_invitation_oauth_secrets,
    complete_invitation_acceptance,
    complete_invitation_acceptance_for_resumption,
    consume_invitation_oauth_attempt,
    create_invitation_oauth_attempt,
    create_invitation_oauth_attempt_for_resumption,
    create_invitation,
    get_invitation_acceptance_context,
    get_invitation_acceptance_context_for_resumption,
    mark_email_invitation_failed,
    mark_email_invitation_sent,
    prepare_email_invitation_delivery,
    platform_resumption_url,
    persist_invitation_account,
    resend_email_invitation_delivery,
    revoke_invitation,
    resume_invitation_platform,
    retry_email_invitation_delivery,
    validate_invitation,
)
from .models import (
    SocialAccount,
    SocialAccountInvitation,
    SocialAccountInvitationAcceptance,
    SocialAccountInvitationAcceptanceAccount,
    SocialAccountInvitationAcceptanceStatus as AcceptanceStatus,
    SocialAccountInvitationDeliveryStatus as DeliveryStatus,
    SocialAccountInvitationMode as InvitationMode,
    SocialAccountInvitationOAuthAttempt,
    SocialAccountInvitationOAuthPlatform as InvitationOAuthPlatform,
    SocialAccountInvitationStatus as InvitationStatus,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialConnectionStatus,
    SocialPlatform,
)


TEST_INVITATION_ENCRYPTION_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def create_connected_account(organization, account_id, platform, *, with_credentials=True):
    connection = None
    if with_credentials and platform == SocialPlatform.FACEBOOK:
        connection = SocialConnection.objects.create(
            organization=organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=f"user-{account_id}",
            status=SocialConnectionStatus.ACTIVE,
        )
    account = SocialAccount.objects.create(
        organization=organization,
        connection=connection,
        platform=platform,
        platform_account_id=account_id,
        account_name=account_id,
        status=SocialAccountStatus.CONNECTED,
        is_valid=True,
    )
    if platform == SocialPlatform.FACEBOOK:
        MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token="encrypted-page-token-placeholder",
            status=MetaCredentialStatus.ACTIVE,
        )
        MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token="encrypted-user-token-placeholder",
            status=MetaCredentialStatus.ACTIVE,
        )
    elif with_credentials and platform == SocialPlatform.INSTAGRAM:
        InstagramAccountCredential.objects.create(
            social_account=account,
            encrypted_access_token="encrypted-instagram-token-placeholder",
            status=InstagramCredentialStatus.ACTIVE,
        )
    return account


class SocialAccountInvitationAPITests(TestCase):
    def setUp(self):
        self.enterContext(self.settings(
            FRONTEND_URL="https://crm.example.test",
            META_CREDENTIAL_ENCRYPTION_KEY=TEST_INVITATION_ENCRYPTION_KEY,
        ))
        self.owner = User.objects.create_user(
            email="owner@example.com", password="test-password", first_name="Owner"
        )
        self.other = User.objects.create_user(
            email="other@example.com", password="test-password", first_name="Other"
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INV-1",
            name="Invitation Test Org",
            slug="invitation-test-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.client = APIClient()
        self.url = reverse(
            "organization-social-account-invitation-share-create",
            kwargs={"organization_id": self.organization.organization_id},
        )

    @override_settings(FRONTEND_URL="https://crm.example.test")
    def test_owner_can_create_facebook_instagram_or_combined_share_link(self):
        self.client.force_authenticate(self.owner)
        for platforms in (["facebook"], ["instagram"], ["facebook", "instagram"]):
            response = self.client.post(self.url, {"platforms": platforms}, format="json")
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data["data"]["platforms"], sorted(platforms))
            self.assertTrue(response.data["data"]["share_url"].startswith(
                "https://crm.example.test/social-invitations/accept#"
            ))
            invitation = SocialAccountInvitation.objects.get(pk=response.data["data"]["id"])
            self.assertNotIn(response.data["data"]["share_url"].split("#", 1)[1], invitation.token_hash)
            self.assertEqual(invitation.recipient_email, "")

    def test_non_owner_cannot_create_for_another_organization(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.url, {"platforms": ["facebook"]}, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(SocialAccountInvitation.objects.count(), 0)

    def test_management_list_reports_expiry_without_mutating_lifecycle_state(self):
        expired = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )["invitation"]
        expired.expires_at = timezone.now() - timedelta(seconds=1)
        expired.save(update_fields=["expires_at"])
        expired_updated_at = expired.updated_at

        valid = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )["invitation"]
        revoked = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )["invitation"]
        revoked.status = InvitationStatus.REVOKED
        revoked.save(update_fields=["status"])
        completed = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )["invitation"]
        completed.status = InvitationStatus.ACCEPTED
        completed.save(update_fields=["status"])
        exhausted = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )["invitation"]
        exhausted.status = InvitationStatus.EXHAUSTED
        exhausted.save(update_fields=["status"])

        self.client.force_authenticate(self.owner)
        list_url = reverse(
            "organization-social-account-invitation-list",
            kwargs={"organization_id": self.organization.organization_id},
        )
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, 200, response.data)
        statuses = {
            row["id"]: row["status"] for row in response.data["data"]
        }
        self.assertEqual(statuses[str(expired.id)], InvitationStatus.EXPIRED)
        self.assertEqual(statuses[str(valid.id)], InvitationStatus.PENDING)
        self.assertEqual(statuses[str(revoked.id)], InvitationStatus.REVOKED)
        self.assertEqual(statuses[str(completed.id)], InvitationStatus.ACCEPTED)
        self.assertEqual(statuses[str(exhausted.id)], InvitationStatus.EXHAUSTED)

        expired.refresh_from_db()
        self.assertEqual(expired.status, InvitationStatus.PENDING)
        self.assertEqual(expired.updated_at, expired_updated_at)

    def test_management_list_marks_completed_share_use_without_consuming_reusable_link(self):
        result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
            usage_limit=2,
        )
        invitation = result["invitation"]
        share_token = result["share_url"].split("#", 1)[1]
        _acceptance, acceptance_token = claim_invitation(share_token, ["facebook"])

        self.client.force_authenticate(self.owner)
        list_url = reverse(
            "organization-social-account-invitation-list",
            kwargs={"organization_id": self.organization.organization_id},
        )
        before = self.client.get(list_url)
        before_row = next(row for row in before.data["data"] if row["id"] == str(invitation.id))
        self.assertEqual(before_row["status"], InvitationStatus.PENDING)
        self.assertFalse(before_row["has_completed_acceptance"])

        persist_invitation_account(
            acceptance_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "share-status-page", SocialPlatform.FACEBOOK
            ),
        )
        complete_invitation_acceptance(acceptance_token)

        after = self.client.get(list_url)
        after_row = next(row for row in after.data["data"] if row["id"] == str(invitation.id))
        self.assertEqual(after_row["status"], InvitationStatus.PENDING)
        self.assertTrue(after_row["has_completed_acceptance"])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.PENDING)
        self.assertEqual(invitation.usage_count, 1)

        # A completed use does not invalidate a reusable share link while it
        # still has capacity for another acceptance.
        _second_acceptance, _second_token = claim_invitation(share_token, ["facebook"])

    def test_unsupported_platform_is_rejected(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {"platforms": ["linkedin"]}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_request_body_cannot_override_organization_context(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.url,
            {"platforms": ["facebook"], "organization_id": "ORG-OTHER"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SocialAccountInvitation.objects.get(pk=response.data["data"]["id"]).organization,
                         self.organization)

    def _create_acceptance_session(self, platforms=None, usage_limit=2):
        invitation_result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=platforms or ["facebook"],
            mode=InvitationMode.SHARE_LINK,
            usage_limit=usage_limit,
        )
        invitation_token = invitation_result["share_url"].split("#", 1)[1]
        acceptance, acceptance_token = claim_invitation(
            invitation_token,
            platforms or ["facebook"],
        )
        return invitation_result["invitation"], acceptance, acceptance_token

    def test_public_completion_requires_acceptance_token_not_acceptance_id(self):
        _invitation, acceptance, _acceptance_token = self._create_acceptance_session()
        url = reverse("social-account-invitation-complete")

        response = self.client.post(
            url,
            {"acceptance_id": str(acceptance.id)},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        acceptance.refresh_from_db()
        self.assertEqual(acceptance.status, AcceptanceStatus.ACTIVE)

    def test_public_completion_rejects_invalid_expired_revoked_and_cancelled_sessions(self):
        completion_url = reverse("social-account-invitation-complete")
        invalid = self.client.post(
            completion_url,
            {"acceptance_token": "x" * 48},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.data["code"], "invalid_invitation")

        expired_invitation, expired_acceptance, expired_token = self._create_acceptance_session()
        expired_acceptance.expires_at = timezone.now() - timedelta(seconds=1)
        expired_acceptance.save(update_fields=["expires_at"])
        expired = self.client.post(
            completion_url,
            {"acceptance_token": expired_token},
            format="json",
        )
        self.assertEqual(expired.status_code, 400)
        self.assertEqual(expired.data["code"], "invalid_invitation")

        expired_invitation, _expired_claim, expired_invitation_token = self._create_acceptance_session()
        expired_invitation.expires_at = timezone.now() - timedelta(seconds=1)
        expired_invitation.save(update_fields=["expires_at"])
        expired_parent = self.client.post(
            completion_url,
            {"acceptance_token": expired_invitation_token},
            format="json",
        )
        self.assertEqual(expired_parent.status_code, 400)
        self.assertEqual(expired_parent.data["code"], "invalid_invitation")

        revoked_invitation, _revoked_acceptance, revoked_token = self._create_acceptance_session()
        revoked_invitation.status = InvitationStatus.REVOKED
        revoked_invitation.save(update_fields=["status"])
        revoked = self.client.post(
            completion_url,
            {"acceptance_token": revoked_token},
            format="json",
        )
        self.assertEqual(revoked.status_code, 400)
        self.assertEqual(revoked.data["code"], "invalid_invitation")

        _cancelled_invitation, cancelled_acceptance, cancelled_token = self._create_acceptance_session()
        cancel_invitation_acceptance(cancelled_token)
        cancelled = self.client.post(
            completion_url,
            {"acceptance_token": cancelled_token},
            format="json",
        )
        self.assertEqual(cancelled.status_code, 400)
        self.assertEqual(cancelled.data["code"], "invalid_invitation")
        cancelled_acceptance.refresh_from_db()
        self.assertEqual(cancelled_acceptance.status, AcceptanceStatus.CANCELLED)
        self.assertEqual(expired_invitation.status, InvitationStatus.PENDING)

    def test_public_completion_reports_incomplete_without_trusting_account_ids(self):
        invitation, acceptance, acceptance_token = self._create_acceptance_session()
        account = create_connected_account(
            self.organization,
            "unassociated-page",
            SocialPlatform.FACEBOOK,
        )

        response = self.client.post(
            reverse("social-account-invitation-complete"),
            {
                "acceptance_token": acceptance_token,
                "social_account_id": str(account.id),
                "platform_account_id": account.platform_account_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "incomplete_accounts")
        self.assertEqual(response.data["data"]["status"], "incomplete")

        SocialAccountInvitationAcceptanceAccount.objects.create(
            acceptance=acceptance,
            social_account=account,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="different-page-id",
        )
        mismatched_audit = self.client.post(
            reverse("social-account-invitation-complete"),
            {"acceptance_token": acceptance_token},
            format="json",
        )
        self.assertEqual(mismatched_audit.status_code, 409)
        self.assertEqual(mismatched_audit.data["code"], "incomplete_accounts")
        invitation.refresh_from_db()
        self.assertEqual(invitation.usage_count, 0)

    def test_public_completion_succeeds_and_retries_without_double_counting(self):
        invitation, _acceptance, acceptance_token = self._create_acceptance_session(
            usage_limit=1,
        )
        persist_invitation_account(
            acceptance_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "completion-page", SocialPlatform.FACEBOOK
            ),
        )
        completion_url = reverse("social-account-invitation-complete")

        first = self.client.post(
            completion_url,
            {"acceptance_token": acceptance_token},
            format="json",
        )
        retry = self.client.post(
            completion_url,
            {"acceptance_token": acceptance_token},
            format="json",
        )

        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data["data"]["status"], "completed")
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(retry.data["data"]["usage_count"], 1)
        invitation.refresh_from_db()
        self.assertEqual(invitation.usage_count, 1)
        self.assertEqual(invitation.status, InvitationStatus.EXHAUSTED)

    def test_email_invitation_normalizes_address_and_does_not_expose_token(self):
        self.client.force_authenticate(self.owner)
        url = reverse(
            "organization-social-account-invitation-email-create",
            kwargs={"organization_id": self.organization.organization_id},
        )
        response = self.client.post(url, {
            "email": "  Client@Example.COM ", "platforms": ["instagram"]
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["data"]["delivery_status"], DeliveryStatus.PENDING_CONFIGURATION)
        self.assertNotIn("token", response.data["data"])
        invitation = SocialAccountInvitation.objects.get(pk=response.data["data"]["id"])
        self.assertEqual(invitation.recipient_email, "client@example.com")
        self.assertEqual(len(invitation.token_hash), 64)
        self.assertFalse(validate_invitation("not-a-real-token")["valid"])
        self.assertNotIn("delivery_token", response.data["data"])
        self.assertNotIn("share_url", response.data["data"])

    def test_management_list_never_exposes_active_or_pending_token_material(self):
        invitation = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.EMAIL,
            recipient_email="client@example.com",
        )["invitation"]
        delivery = prepare_email_invitation_delivery(invitation)
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse(
            "organization-social-account-invitation-list",
            kwargs={"organization_id": self.organization.organization_id},
        ))
        self.assertEqual(response.status_code, 200)
        row = response.data["data"][0]
        self.assertNotIn("token_hash", row)
        self.assertNotIn("pending_token_hash", row)
        self.assertNotIn("pending_delivery_token_encrypted", row)
        self.assertNotIn(delivery["token"], str(response.data))

    def test_non_owner_cannot_start_email_delivery(self):
        invitation = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.EMAIL,
            recipient_email="client@example.com",
        )["invitation"]
        self.client.force_authenticate(self.other)
        response = self.client.post(
            reverse(
                "organization-social-account-invitation-email-send",
                kwargs={
                    "organization_id": self.organization.organization_id,
                    "invitation_id": invitation.pk,
                },
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        invitation.refresh_from_db()
        self.assertEqual(invitation.delivery_attempts, 0)

    def test_email_and_share_invitations_use_backend_72_hour_expiry(self):
        self.client.force_authenticate(self.owner)
        email_response = self.client.post(
            reverse(
                "organization-social-account-invitation-email-create",
                kwargs={"organization_id": self.organization.organization_id},
            ),
            {"email": "client@example.com", "platforms": ["facebook"]},
            format="json",
        )
        share_response = self.client.post(
            self.url,
            {"platforms": ["instagram"], "expires_in_days": 30},
            format="json",
        )
        self.assertEqual(email_response.status_code, 201)
        self.assertEqual(share_response.status_code, 201)
        for response in (email_response, share_response):
            invitation = SocialAccountInvitation.objects.get(
                pk=response.data["data"]["id"]
            )
            self.assertAlmostEqual(
                (invitation.expires_at - timezone.now()).total_seconds(),
                72 * 60 * 60,
                delta=5,
            )

    @patch("apps.social_accounts.invitation_delivery.send_brevo_email")
    def test_initial_email_send_uses_brevo_and_never_returns_raw_invitation_token(
        self, send_email
    ):
        from urllib.parse import parse_qs, urlsplit

        send_email.return_value = {"messageId": "brevo-message-123"}
        self.client.force_authenticate(self.owner)
        created = self.client.post(
            reverse(
                "organization-social-account-invitation-email-create",
                kwargs={"organization_id": self.organization.organization_id},
            ),
            {"email": "client@example.com", "platforms": ["facebook", "instagram"]},
            format="json",
        )
        invitation_id = created.data["data"]["id"]
        sent = self.client.post(
            reverse(
                "organization-social-account-invitation-email-send",
                kwargs={
                    "organization_id": self.organization.organization_id,
                    "invitation_id": invitation_id,
                },
            ),
            {},
            format="json",
        )
        self.assertEqual(sent.status_code, 200, sent.data)
        self.assertEqual(sent.data["data"]["delivery_status"], DeliveryStatus.SENT)
        self.assertNotIn("token", sent.data["data"])
        self.assertNotIn("share_url", sent.data["data"])
        params = send_email.call_args.kwargs["params"]
        self.assertEqual(params["OrganizationName"], self.organization.name)
        self.assertEqual(params["Platforms"], "Facebook, Instagram")
        self.assertTrue(params["FacebookEnabled"])
        self.assertTrue(params["InstagramEnabled"])
        self.assertIn("connect=facebook", params["FacebookInvitationUrl"])
        self.assertIn("#resume=", params["FacebookInvitationUrl"])
        self.assertIn("connect=instagram", params["InstagramInvitationUrl"])
        self.assertIn("#resume=", params["InstagramInvitationUrl"])
        self.assertEqual(
            parse_qs(urlsplit(params["FacebookInvitationUrl"]).query),
            {"connect": [SocialPlatform.FACEBOOK]},
        )
        self.assertEqual(
            parse_qs(urlsplit(params["InstagramInvitationUrl"]).query),
            {"connect": [SocialPlatform.INSTAGRAM]},
        )
        self.assertEqual(params["ExpiryHours"], "72")
        self.assertTrue(params["InvitationUrl"].startswith(
            "https://crm.example.test/social-invitations/accept#"
        ))
        token = params["InvitationUrl"].split("#", 1)[1]
        self.assertTrue(validate_invitation(token)["usable"])
        self.assertNotIn(token, str(sent.data))

    @patch("apps.social_accounts.invitation_delivery.send_brevo_email")
    def test_email_delivery_failure_can_be_retried_without_exposing_tokens(self, send_email):
        from apps.notifications.services import BrevoEmailError

        send_email.side_effect = BrevoEmailError(
            "provider rejected request",
            definitive=True,
            error_code="provider_rejected",
        )
        self.client.force_authenticate(self.owner)
        created = self.client.post(
            reverse(
                "organization-social-account-invitation-email-create",
                kwargs={"organization_id": self.organization.organization_id},
            ),
            {"email": "client@example.com", "platforms": ["instagram"]},
            format="json",
        )
        invitation_id = created.data["data"]["id"]
        kwargs = {
            "organization_id": self.organization.organization_id,
            "invitation_id": invitation_id,
        }
        failed = self.client.post(
            reverse("organization-social-account-invitation-email-send", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(failed.status_code, 502)
        self.assertEqual(failed.data["data"]["delivery_attempt_status"], "failed")
        invitation = SocialAccountInvitation.objects.get(pk=invitation_id)
        self.assertEqual(invitation.delivery_error_code, "provider_rejected")

        send_email.side_effect = None
        send_email.return_value = {"messageId": "brevo-retry-123"}
        retried = self.client.post(
            reverse("organization-social-account-invitation-email-retry", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(retried.status_code, 200, retried.data)
        invitation.refresh_from_db()
        self.assertEqual(invitation.delivery_status, DeliveryStatus.SENT)
        self.assertEqual(invitation.delivery_error_code, "")

    @patch("apps.social_accounts.invitation_delivery.send_brevo_email")
    def test_ambiguous_email_provider_result_stays_pending_and_cannot_be_retried(
        self, send_email
    ):
        from apps.notifications.services import BrevoEmailError

        send_email.side_effect = BrevoEmailError("ambiguous provider response")
        self.client.force_authenticate(self.owner)
        created = self.client.post(
            reverse(
                "organization-social-account-invitation-email-create",
                kwargs={"organization_id": self.organization.organization_id},
            ),
            {"email": "client@example.com", "platforms": ["facebook"]},
            format="json",
        )
        invitation_id = created.data["data"]["id"]
        kwargs = {
            "organization_id": self.organization.organization_id,
            "invitation_id": invitation_id,
        }
        pending = self.client.post(
            reverse("organization-social-account-invitation-email-send", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(pending.status_code, 202)
        invitation = SocialAccountInvitation.objects.get(pk=invitation_id)
        self.assertEqual(invitation.delivery_status, DeliveryStatus.PENDING)
        self.assertTrue(invitation.pending_token_hash)
        self.assertFalse(pending.data["data"]["retry_available"])
        retry = self.client.post(
            reverse("organization-social-account-invitation-email-retry", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(retry.status_code, 202)
        self.assertEqual(send_email.call_count, 2)
        self.assertEqual(
            send_email.call_args_list[0].kwargs["params"]["InvitationUrl"],
            send_email.call_args_list[1].kwargs["params"]["InvitationUrl"],
        )
        invitation.refresh_from_db()
        self.assertEqual(invitation.delivery_attempts, 1)

    @patch("apps.social_accounts.invitation_delivery.send_brevo_email")
    def test_failed_resend_preserves_old_link_until_retried_delivery_succeeds(
        self, send_email
    ):
        from apps.notifications.services import BrevoEmailError

        self.client.force_authenticate(self.owner)
        send_email.return_value = {"messageId": "brevo-initial-123"}
        created = self.client.post(
            reverse(
                "organization-social-account-invitation-email-create",
                kwargs={"organization_id": self.organization.organization_id},
            ),
            {"email": "client@example.com", "platforms": ["facebook"]},
            format="json",
        )
        invitation_id = created.data["data"]["id"]
        kwargs = {
            "organization_id": self.organization.organization_id,
            "invitation_id": invitation_id,
        }
        initial = self.client.post(
            reverse("organization-social-account-invitation-email-send", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(initial.status_code, 200, initial.data)
        old_token = send_email.call_args.kwargs["params"]["InvitationUrl"].split("#", 1)[1]
        self.assertTrue(validate_invitation(old_token)["usable"])

        send_email.side_effect = BrevoEmailError(
            "provider rejection", definitive=True, error_code="provider_rejected"
        )
        failed_resend = self.client.post(
            reverse("organization-social-account-invitation-email-resend", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(failed_resend.status_code, 502)
        self.assertTrue(validate_invitation(old_token)["usable"])

        send_email.side_effect = None
        send_email.return_value = {"messageId": "brevo-resend-456"}
        retried = self.client.post(
            reverse("organization-social-account-invitation-email-retry", kwargs=kwargs),
            {},
            format="json",
        )
        self.assertEqual(retried.status_code, 200, retried.data)
        new_token = send_email.call_args.kwargs["params"]["InvitationUrl"].split("#", 1)[1]
        self.assertNotEqual(old_token, new_token)
        self.assertFalse(validate_invitation(old_token)["valid"])
        self.assertTrue(validate_invitation(new_token)["usable"])

    @override_settings(FRONTEND_URL="https://crm.example.test")
    def test_share_invitation_token_validation_and_claim(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {"platforms": ["facebook"]}, format="json")
        token = response.data["data"]["share_url"].split("#", 1)[1]
        validate_url = reverse("social-account-invitation-validate")
        validation = self.client.post(validate_url, {"token": token}, format="json")
        self.assertEqual(validation.status_code, 200)
        self.assertTrue(validation.data["data"]["valid"])
        self.assertTrue(validation.data["data"]["usable"])
        self.assertEqual(validation.data["data"]["organization_name"], self.organization.name)
        self.assertNotIn("organization_id", validation.data["data"])
        claim_url = reverse("social-account-invitation-claim")
        claim = self.client.post(claim_url, {"token": token, "platforms": ["facebook"]}, format="json")
        self.assertEqual(claim.status_code, 201, claim.data)
        acceptance = SocialAccountInvitationAcceptance.objects.get(
            token_hash__isnull=False
        )
        self.assertNotEqual(acceptance.token_hash, claim.data["data"]["acceptance_token"])

    @override_settings(FRONTEND_URL="https://crm.example.test")
    def test_public_cancel_endpoint_releases_a_claim(self):
        self.client.force_authenticate(self.owner)
        created = self.client.post(
            self.url,
            {"platforms": ["facebook"], "usage_limit": 1},
            format="json",
        )
        token = created.data["data"]["share_url"].split("#", 1)[1]
        claim_response = self.client.post(
            reverse("social-account-invitation-claim"),
            {"token": token, "platforms": ["facebook"]},
            format="json",
        )
        cancel_response = self.client.post(
            reverse("social-account-invitation-cancel"),
            {"acceptance_token": claim_response.data["data"]["acceptance_token"]},
            format="json",
        )
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.data["data"]["status"], AcceptanceStatus.CANCELLED)
        retry = self.client.post(
            reverse("social-account-invitation-claim"),
            {"token": token, "platforms": ["facebook"]},
            format="json",
        )
        self.assertEqual(retry.status_code, 201)

    def test_anonymous_oauth_attempt_uses_organization_from_acceptance(self):
        invitation_result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )
        invitation_token = invitation_result["share_url"].split("#", 1)[1]
        _, acceptance_token = claim_invitation(invitation_token, ["facebook"])

        response = self.client.post(
            reverse("social-account-invitation-oauth-attempt"),
            {
                "acceptance_token": acceptance_token,
                "platform": InvitationOAuthPlatform.FACEBOOK,
                "organization_id": "ORG-CLIENT-SUPPLIED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        attempt = SocialAccountInvitationOAuthAttempt.objects.get(
            pk=response.data["data"]["attempt_id"]
        )
        self.assertEqual(attempt.acceptance.invitation.organization, self.organization)
        self.assertEqual(attempt.platform, InvitationOAuthPlatform.FACEBOOK)
        self.assertNotEqual(attempt.state_hash, response.data["data"]["state"])

    def test_oauth_attempt_rejects_invalid_acceptance_and_unselected_platform(self):
        endpoint = reverse("social-account-invitation-oauth-attempt")
        invalid = self.client.post(
            endpoint,
            {"acceptance_token": "x" * 48, "platform": "facebook"},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)

        invitation_result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
        )
        invitation_token = invitation_result["share_url"].split("#", 1)[1]
        _, acceptance_token = claim_invitation(invitation_token, ["facebook"])
        rejected = self.client.post(
            endpoint,
            {"acceptance_token": acceptance_token, "platform": "instagram"},
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)

    def test_oauth_attempt_rejects_expired_or_revoked_acceptance_context(self):
        endpoint = reverse("social-account-invitation-oauth-attempt")
        for invalidation in ("acceptance_expired", "invitation_expired", "revoked"):
            with self.subTest(invalidation=invalidation):
                invitation_result = create_invitation(
                    organization=self.organization,
                    inviter=self.owner,
                    platforms=["facebook"],
                    mode=InvitationMode.SHARE_LINK,
                )
                invitation_token = invitation_result["share_url"].split("#", 1)[1]
                acceptance, acceptance_token = claim_invitation(
                    invitation_token, ["facebook"]
                )
                if invalidation == "acceptance_expired":
                    acceptance.expires_at = timezone.now() - timedelta(seconds=1)
                    acceptance.save(update_fields=["expires_at"])
                else:
                    invitation = invitation_result["invitation"]
                    if invalidation == "invitation_expired":
                        invitation.expires_at = timezone.now() - timedelta(seconds=1)
                        invitation.save(update_fields=["expires_at"])
                    else:
                        invitation.status = InvitationStatus.REVOKED
                        invitation.save(update_fields=["status"])

                response = self.client.post(
                    endpoint,
                    {"acceptance_token": acceptance_token, "platform": "facebook"},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)

    def test_email_invitation_cannot_be_claimed_until_delivery_is_sent(self):
        result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.EMAIL,
            recipient_email="client@example.com",
        )
        with self.assertRaises(InvalidInvitation):
            claim_invitation("x" * 48)
        self.assertFalse(validate_invitation("x" * 48)["usable"])

    def test_email_delivery_can_be_prepared_without_persisting_raw_token(self):
        invitation = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.EMAIL,
            recipient_email="client@example.com",
        )["invitation"]
        delivery = prepare_email_invitation_delivery(invitation)
        invitation.refresh_from_db()
        self.assertEqual(delivery["recipient_email"], "client@example.com")
        self.assertTrue(delivery["invitation_url"].endswith(f"#{delivery['token']}"))
        self.assertNotEqual(invitation.token_hash, hashlib.sha256(
            delivery["token"].encode("utf-8")
        ).hexdigest())
        self.assertEqual(invitation.pending_token_hash, hashlib.sha256(
            delivery["token"].encode("utf-8")
        ).hexdigest())
        self.assertTrue(invitation.pending_delivery_token_encrypted)
        self.assertNotIn(delivery["token"], invitation.pending_delivery_token_encrypted)
        from .invitation_crypto import decrypt_invitation_token
        self.assertEqual(
            decrypt_invitation_token(invitation.pending_delivery_token_encrypted),
            delivery["token"],
        )
        self.assertEqual(len(invitation.token_hash), 64)
        self.assertTrue(mark_email_invitation_sent(
            invitation,
            delivery["attempt_id"],
            "provider-message-123",
        ))
        self.assertTrue(validate_invitation(delivery["token"])["usable"])
        invitation.refresh_from_db()
        self.assertEqual(invitation.pending_delivery_token_encrypted, "")
        acceptance, session_token = claim_invitation(delivery["token"], ["facebook"])
        persisted = persist_invitation_account(
            session_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "email-page-1", SocialPlatform.FACEBOOK
            ),
        )
        self.assertEqual(persisted.platform_account_id, "email-page-1")
        complete_invitation_acceptance(session_token)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.ACCEPTED)

    def test_invitation_models_do_not_store_provider_credentials(self):
        forbidden_fields = {"access_token", "refresh_token", "client_secret"}
        for model in (
            SocialAccountInvitation,
            SocialAccountInvitationAcceptance,
            SocialAccountInvitationAcceptanceAccount,
        ):
            model_fields = {field.name for field in model._meta.get_fields()}
            self.assertTrue(forbidden_fields.isdisjoint(model_fields))


class SocialAccountInvitationPlatformResumptionTests(TestCase):
    def setUp(self):
        self.enterContext(self.settings(
            FRONTEND_URL="https://crm.example.test",
            META_CREDENTIAL_ENCRYPTION_KEY=TEST_INVITATION_ENCRYPTION_KEY,
        ))
        self.owner = User.objects.create_user(
            email="resume-owner@example.test",
            password="test-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-RESUME-1",
            name="Resumption Test Org",
            slug="resumption-test-org",
            industry="Testing",
            created_by=self.owner,
        )
        created = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            mode=InvitationMode.EMAIL,
            recipient_email="client@example.test",
            platforms=[SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM],
        )
        self.invitation = created["invitation"]
        self.delivery = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(
            self.invitation,
            self.delivery["attempt_id"],
        ))
        self.invitation.refresh_from_db()
        self.facebook_url = platform_resumption_url(
            self.invitation,
            self.delivery["token"],
            SocialPlatform.FACEBOOK,
        )
        self.instagram_url = platform_resumption_url(
            self.invitation,
            self.delivery["token"],
            SocialPlatform.INSTAGRAM,
        )

    @staticmethod
    def token_from_url(url):
        from urllib.parse import parse_qs, urlsplit

        fragment = parse_qs(urlsplit(url).fragment)
        return fragment["resume"][0]

    def test_platform_ctas_reuse_one_acceptance_across_independent_requests(self):
        facebook_token = self.token_from_url(self.facebook_url)
        instagram_token = self.token_from_url(self.instagram_url)

        facebook_context = resume_invitation_platform(
            facebook_token,
            expected_platform=SocialPlatform.FACEBOOK,
        )
        _attempt, facebook_state, _context = create_invitation_oauth_attempt_for_resumption(
            facebook_token,
            platform=SocialPlatform.FACEBOOK,
        )
        consume_invitation_oauth_attempt(
            facebook_state,
            expected_platform=SocialPlatform.FACEBOOK,
        )
        instagram_context = resume_invitation_platform(
            instagram_token,
            expected_platform=SocialPlatform.INSTAGRAM,
        )

        self.assertEqual(facebook_context["acceptance_id"], instagram_context["acceptance_id"])
        self.assertEqual(
            set(facebook_context["selected_platforms"]),
            {SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM},
        )
        self.assertEqual(self.invitation.usage_count, 0)
        self.assertEqual(
            SocialAccountInvitationAcceptance.objects.filter(
                invitation=self.invitation,
                status=AcceptanceStatus.ACTIVE,
                is_deleted=False,
            ).count(),
            1,
        )
        self.assertEqual(
            get_invitation_acceptance_context_for_resumption(
                facebook_token,
                expected_platform=SocialPlatform.FACEBOOK,
            )["acceptance_id"],
            instagram_context["acceptance_id"],
        )

    def test_later_platform_cta_preserves_verified_partial_connection_after_claim_expiry(self):
        facebook_token = self.token_from_url(self.facebook_url)
        instagram_token = self.token_from_url(self.instagram_url)
        original_context = resume_invitation_platform(
            facebook_token,
            expected_platform=SocialPlatform.FACEBOOK,
        )
        original_acceptance = SocialAccountInvitationAcceptance.objects.get(
            pk=original_context["acceptance_id"]
        )
        account = create_connected_account(
            self.organization,
            "persisted-facebook-page",
            SocialPlatform.FACEBOOK,
        )
        SocialAccountInvitationAcceptanceAccount.objects.create(
            acceptance=original_acceptance,
            social_account=account,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=account.platform_account_id,
        )
        original_acceptance.expires_at = timezone.now() - timedelta(seconds=1)
        original_acceptance.save(update_fields=["expires_at", "updated_at"])

        resumed = resume_invitation_platform(
            instagram_token,
            expected_platform=SocialPlatform.INSTAGRAM,
        )

        self.assertNotEqual(resumed["acceptance_id"], original_acceptance.pk)
        self.assertEqual(resumed["connected_platforms"], (SocialPlatform.FACEBOOK,))
        self.assertTrue(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance_id=resumed["acceptance_id"],
                social_account=account,
                is_deleted=False,
            ).exists()
        )
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.usage_count, 0)

    def test_completed_resumption_retry_remains_idempotent_after_invitation_expiry(self):
        context = resume_invitation_platform(
            self.token_from_url(self.facebook_url),
            expected_platform=SocialPlatform.FACEBOOK,
        )
        acceptance = SocialAccountInvitationAcceptance.objects.get(
            pk=context["acceptance_id"]
        )
        for platform, account_id in (
            (SocialPlatform.FACEBOOK, "completed-facebook-page"),
            (SocialPlatform.INSTAGRAM, "completed-instagram-account"),
        ):
            account = create_connected_account(
                self.organization,
                account_id,
                platform,
            )
            SocialAccountInvitationAcceptanceAccount.objects.create(
                acceptance=acceptance,
                social_account=account,
                platform=platform,
                platform_account_id=account.platform_account_id,
            )

        completed = complete_invitation_acceptance_for_resumption(
            self.token_from_url(self.facebook_url)
        )
        usage_after_first_completion = completed.usage_count
        self.invitation.refresh_from_db()
        self.invitation.expires_at = timezone.now() - timedelta(seconds=1)
        self.invitation.save(update_fields=["expires_at", "updated_at"])

        retried = complete_invitation_acceptance_for_resumption(
            self.token_from_url(self.facebook_url)
        )

        self.assertEqual(retried.pk, completed.pk)
        self.assertEqual(retried.usage_count, usage_after_first_completion)
        self.assertEqual(retried.usage_count, 1)

    def test_resumption_capability_is_platform_bound_and_tamper_evident(self):
        facebook_token = self.token_from_url(self.facebook_url)
        with self.assertRaises(InvalidInvitation):
            resume_invitation_platform(
                facebook_token,
                expected_platform=SocialPlatform.INSTAGRAM,
            )
        with self.assertRaises(InvalidInvitation):
            resume_invitation_platform(
                facebook_token[:-1] + ("A" if facebook_token[-1] != "A" else "B"),
                expected_platform=SocialPlatform.FACEBOOK,
            )

    def test_cta_url_keeps_resumption_secret_in_fragment_not_query(self):
        from urllib.parse import parse_qs, urlsplit

        parsed = urlsplit(self.facebook_url)
        self.assertEqual(parse_qs(parsed.query), {"connect": [SocialPlatform.FACEBOOK]})
        self.assertTrue(parsed.fragment.startswith("resume="))
        self.assertNotIn(self.delivery["token"], parsed.query)
        self.assertNotIn("acceptance_token", parsed.query)

    def test_platform_resumption_api_returns_scope_without_acceptance_secret(self):
        client = APIClient()
        response = client.post(
            reverse("social-account-invitation-platform-resume"),
            {
                "resumption_token": self.token_from_url(self.facebook_url),
                "platform": SocialPlatform.FACEBOOK,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["platform"], SocialPlatform.FACEBOOK)
        self.assertEqual(
            set(response.data["data"]["selected_platforms"]),
            {SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM},
        )
        self.assertNotIn("acceptance_token", response.data["data"])

    def test_revocation_expiry_and_successful_resend_invalidate_old_ctas(self):
        old_facebook_token = self.token_from_url(self.facebook_url)
        replacement = resend_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(
            self.invitation,
            replacement["attempt_id"],
        ))
        with self.assertRaises(InvalidInvitation):
            resume_invitation_platform(
                old_facebook_token,
                expected_platform=SocialPlatform.FACEBOOK,
            )

        self.invitation.refresh_from_db()
        new_url = platform_resumption_url(
            self.invitation,
            replacement["token"],
            SocialPlatform.FACEBOOK,
        )
        new_token = self.token_from_url(new_url)
        revoke_invitation(self.invitation)
        with self.assertRaises(InvalidInvitation):
            resume_invitation_platform(
                new_token,
                expected_platform=SocialPlatform.FACEBOOK,
            )

    def test_expired_invitation_rejects_platform_resumption(self):
        token = self.token_from_url(self.facebook_url)
        self.invitation.expires_at = timezone.now() - timedelta(seconds=1)
        self.invitation.save(update_fields=["expires_at", "updated_at"])
        with self.assertRaises(InvalidInvitation):
            resume_invitation_platform(token, expected_platform=SocialPlatform.FACEBOOK)


class SocialAccountInvitationLifecycleTests(TestCase):
    def setUp(self):
        self.enterContext(self.settings(FRONTEND_URL="https://crm.example.test"))
        self.owner = User.objects.create_user(
            email="life@example.com", password="test-password", first_name="Life"
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INV-2",
            name="Invitation Lifecycle Org",
            slug="invitation-lifecycle-org",
            industry="Retail",
            created_by=self.owner,
        )

    def create_share(self, usage_limit=2):
        return create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook", "instagram"],
            mode=InvitationMode.SHARE_LINK,
            usage_limit=usage_limit,
        )

    def create_oauth_staging_rows(self):
        result = self.create_share(usage_limit=2)
        invitation = result["invitation"]
        acceptance, acceptance_token = claim_invitation(
            result["share_url"].split("#", 1)[1],
            [SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM],
        )
        meta_attempt, _ = create_invitation_oauth_attempt(
            acceptance_token, SocialPlatform.FACEBOOK
        )
        instagram_attempt, _ = create_invitation_oauth_attempt(
            acceptance_token, SocialPlatform.INSTAGRAM
        )
        now = timezone.now()
        meta_session = InvitationMetaOAuthSession.objects.create(
            acceptance=acceptance,
            oauth_attempt=meta_attempt,
            provider_user_id="temporary-meta-user",
            encrypted_access_token="encrypted-temporary-meta-user-token",
            encrypted_accounts="encrypted-temporary-page-token-payload",
            expires_at=now + timedelta(minutes=5),
        )
        instagram_session = InvitationInstagramOAuthSession.objects.create(
            acceptance=acceptance,
            oauth_attempt=instagram_attempt,
            instagram_user_id="temporary-instagram-user",
            encrypted_access_token="encrypted-temporary-instagram-token",
            token_expires_at=now + timedelta(days=1),
            expires_at=now + timedelta(minutes=5),
        )
        return invitation, acceptance, acceptance_token, meta_session, instagram_session

    def test_bounded_cleanup_clears_expired_staging_and_preserves_permanent_credentials(self):
        _invitation, _acceptance, _token, meta_session, instagram_session = (
            self.create_oauth_staging_rows()
        )
        meta_session.expires_at = timezone.now() - timedelta(seconds=1)
        meta_session.save(update_fields=["expires_at"])
        instagram_session.expires_at = timezone.now() - timedelta(seconds=1)
        instagram_session.save(update_fields=["expires_at"])
        permanent_account = create_connected_account(
            self.organization, "permanent-facebook-page", SocialPlatform.FACEBOOK
        )
        permanent_credentials = list(
            MetaAccountCredential.objects.filter(social_account=permanent_account)
            .order_by("credential_type")
            .values_list("access_token", flat=True)
        )

        result = cleanup_expired_invitation_oauth_secrets(batch_size=10)
        repeated = cleanup_expired_invitation_oauth_secrets(batch_size=10)

        self.assertEqual(result["meta_sessions_cleared"], 1)
        self.assertEqual(result["instagram_sessions_expired"], 1)
        self.assertEqual(repeated, {
            "meta_sessions_cleared": 0,
            "instagram_sessions_expired": 0,
            "instagram_sessions_invalidated": 0,
            "invitation_delivery_tokens_cleared": 0,
        })
        meta_session.refresh_from_db()
        instagram_session.refresh_from_db()
        self.assertEqual(meta_session.encrypted_access_token, "")
        self.assertEqual(meta_session.encrypted_accounts, "")
        self.assertEqual(instagram_session.status, InvitationInstagramOAuthStatus.EXPIRED)
        self.assertEqual(instagram_session.encrypted_access_token, "")
        self.assertTrue(InvitationMetaOAuthSession.objects.filter(pk=meta_session.pk).exists())
        self.assertTrue(InvitationInstagramOAuthSession.objects.filter(pk=instagram_session.pk).exists())
        self.assertEqual(
            list(
                MetaAccountCredential.objects.filter(social_account=permanent_account)
                .order_by("credential_type")
                .values_list("access_token", flat=True)
            ),
            permanent_credentials,
        )

    def test_cleanup_processes_only_a_bounded_batch_per_invocation(self):
        sessions = [self.create_oauth_staging_rows() for _ in range(2)]
        for _invitation, _acceptance, _token, meta_session, instagram_session in sessions:
            meta_session.expires_at = timezone.now() - timedelta(seconds=1)
            meta_session.save(update_fields=["expires_at"])
            instagram_session.expires_at = timezone.now() - timedelta(seconds=1)
            instagram_session.save(update_fields=["expires_at"])

        first = cleanup_expired_invitation_oauth_secrets(batch_size=1)
        remaining_meta = InvitationMetaOAuthSession.objects.filter(
            encrypted_access_token__gt=""
        ).count()
        remaining_instagram = InvitationInstagramOAuthSession.objects.filter(
            encrypted_access_token__gt="",
            status=InvitationInstagramOAuthStatus.STAGED,
        ).count()
        second = cleanup_expired_invitation_oauth_secrets(batch_size=1)

        self.assertEqual(first["meta_sessions_cleared"], 1)
        self.assertEqual(first["instagram_sessions_expired"], 1)
        self.assertEqual(remaining_meta, 1)
        self.assertEqual(remaining_instagram, 1)
        self.assertEqual(second["meta_sessions_cleared"], 1)
        self.assertEqual(second["instagram_sessions_expired"], 1)

    def test_cancel_and_revoke_clear_both_provider_staging_secrets(self):
        _invitation, _acceptance, token, meta_session, instagram_session = (
            self.create_oauth_staging_rows()
        )
        cancel_invitation_acceptance(token)
        for session in (meta_session, instagram_session):
            session.refresh_from_db()
            self.assertEqual(session.encrypted_access_token, "")
        meta_session.refresh_from_db()
        self.assertEqual(meta_session.encrypted_accounts, "")
        instagram_session.refresh_from_db()
        self.assertEqual(instagram_session.status, InvitationInstagramOAuthStatus.INVALIDATED)

        invitation, _acceptance, _token, meta_session, instagram_session = (
            self.create_oauth_staging_rows()
        )
        revoke_invitation(invitation)
        for session in (meta_session, instagram_session):
            session.refresh_from_db()
            self.assertEqual(session.encrypted_access_token, "")
        meta_session.refresh_from_db()
        self.assertEqual(meta_session.encrypted_accounts, "")
        instagram_session.refresh_from_db()
        self.assertEqual(instagram_session.status, InvitationInstagramOAuthStatus.INVALIDATED)

    def test_completion_clears_temporary_secrets_but_keeps_connected_credentials(self):
        _invitation, _acceptance, token, meta_session, instagram_session = (
            self.create_oauth_staging_rows()
        )
        for platform, account_id in (
            (SocialPlatform.FACEBOOK, "completion-facebook"),
            (SocialPlatform.INSTAGRAM, "completion-instagram"),
        ):
            persist_invitation_account(
                token,
                lambda organization, platform=platform, account_id=account_id, **_kwargs:
                create_connected_account(organization, account_id, platform),
            )

        complete_invitation_acceptance(token)

        meta_session.refresh_from_db()
        instagram_session.refresh_from_db()
        self.assertEqual(meta_session.encrypted_access_token, "")
        self.assertEqual(meta_session.encrypted_accounts, "")
        self.assertEqual(instagram_session.encrypted_access_token, "")
        self.assertEqual(instagram_session.status, InvitationInstagramOAuthStatus.INVALIDATED)
        self.assertTrue(
            MetaAccountCredential.objects.filter(
                social_account__platform_account_id="completion-facebook",
                access_token="encrypted-page-token-placeholder",
            ).exists()
        )
        self.assertTrue(
            InstagramAccountCredential.objects.filter(
                social_account__platform_account_id="completion-instagram",
                encrypted_access_token="encrypted-instagram-token-placeholder",
            ).exists()
        )

    def test_expired_and_revoked_tokens_are_unusable(self):
        result = self.create_share()
        invitation = result["invitation"]
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])
        self.assertFalse(validate_invitation(result["share_url"].split("#", 1)[1])["usable"])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.EXPIRED)

        result = self.create_share()
        invitation = result["invitation"]
        invitation.status = InvitationStatus.REVOKED
        invitation.save(update_fields=["status"])
        self.assertFalse(validate_invitation(result["share_url"].split("#", 1)[1])["usable"])

    def test_validation_reports_available_capacity_as_usable(self):
        result = self.create_share(usage_limit=2)

        validation = validate_invitation(result["share_url"].split("#", 1)[1])

        self.assertTrue(validation["valid"])
        self.assertTrue(validation["usable"])

    def test_validation_reports_fully_reserved_capacity_as_unusable(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        claim_invitation(token, ["facebook"])

        validation = validate_invitation(token)

        self.assertTrue(validation["valid"])
        self.assertFalse(validation["usable"])
        self.assertEqual(validation["platforms"], [])

    def test_expired_acceptance_does_not_reserve_capacity_in_validation(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        acceptance, _ = claim_invitation(token, ["facebook"])
        acceptance.expires_at = timezone.now() - timedelta(seconds=1)
        acceptance.save(update_fields=["expires_at"])

        self.assertTrue(validate_invitation(token)["usable"])

    def test_cancelled_acceptance_does_not_reserve_capacity_in_validation(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook"])
        cancel_invitation_acceptance(session_token)

        self.assertTrue(validate_invitation(token)["usable"])

    def test_completed_usage_and_active_reservations_are_not_double_counted(self):
        result = self.create_share(usage_limit=3)
        invitation = result["invitation"]
        invitation.usage_count = 1
        invitation.save(update_fields=["usage_count"])
        SocialAccountInvitationAcceptance.objects.create(
            invitation=invitation,
            token_hash="c" * 64,
            selected_platforms=["facebook"],
            status=AcceptanceStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(minutes=30),
            completed_at=timezone.now(),
        )
        claim_invitation(result["share_url"].split("#", 1)[1], ["facebook"])

        validation = validate_invitation(result["share_url"].split("#", 1)[1])

        # One completed use plus one active reservation leaves one of three uses.
        self.assertTrue(validation["usable"])

    def test_expired_or_revoked_invitation_stays_unusable_with_active_reservation(self):
        expired_result = self.create_share(usage_limit=2)
        expired_token = expired_result["share_url"].split("#", 1)[1]
        claim_invitation(expired_token, ["facebook"])
        expired_invitation = expired_result["invitation"]
        expired_invitation.expires_at = timezone.now() - timedelta(seconds=1)
        expired_invitation.save(update_fields=["expires_at"])
        self.assertFalse(validate_invitation(expired_token)["usable"])

        revoked_result = self.create_share(usage_limit=2)
        revoked_token = revoked_result["share_url"].split("#", 1)[1]
        claim_invitation(revoked_token, ["facebook"])
        revoked_invitation = revoked_result["invitation"]
        revoked_invitation.status = InvitationStatus.REVOKED
        revoked_invitation.save(update_fields=["status"])
        self.assertFalse(validate_invitation(revoked_token)["usable"])

    def test_claim_reserves_capacity_and_completion_consumes_once(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        acceptance, session_token = claim_invitation(token, ["facebook"])
        with self.assertRaises(InvalidInvitation):
            claim_invitation(token, ["instagram"])
        with self.assertRaises(IncompleteInvitation):
            complete_invitation_acceptance(session_token)
        persist_invitation_account(
            session_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "page-complete-1", SocialPlatform.FACEBOOK
            ),
        )
        invitation = result["invitation"]
        invitation.refresh_from_db()
        self.assertEqual(invitation.usage_count, 1)
        complete_invitation_acceptance(session_token)
        invitation.refresh_from_db()
        self.assertEqual(invitation.usage_count, 1)
        self.assertEqual(acceptance.status, AcceptanceStatus.COMPLETED)
        self.assertEqual(invitation.status, InvitationStatus.EXHAUSTED)

    def test_one_acceptance_can_add_multiple_pages_before_completion(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        acceptance, session_token = claim_invitation(token, ["facebook"])
        first = persist_invitation_account(
            session_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "page-multi-1", SocialPlatform.FACEBOOK
            ),
        )
        second = persist_invitation_account(
            session_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "page-multi-2", SocialPlatform.FACEBOOK
            ),
        )
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                acceptance=acceptance,
            ).count(),
            2,
        )
        completed = complete_invitation_acceptance(session_token)
        self.assertEqual(completed.usage_count, 1)

    def test_combined_platform_claim_requires_each_selected_platform(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook", "instagram"])
        persist_invitation_account(
            session_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "page-combined-1", SocialPlatform.FACEBOOK
            ),
        )
        with self.assertRaises(IncompleteInvitation):
            complete_invitation_acceptance(session_token)
        persist_invitation_account(
            session_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "instagram-combined-1", SocialPlatform.INSTAGRAM
            ),
        )
        self.assertEqual(complete_invitation_acceptance(session_token).usage_count, 1)

    def test_account_without_active_provider_credential_is_not_accepted(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook"])
        with self.assertRaises(InvitationError):
            persist_invitation_account(
                session_token,
                lambda **kwargs: create_connected_account(
                    kwargs["organization"],
                    "page-no-credential",
                    SocialPlatform.FACEBOOK,
                    with_credentials=False,
                ),
            )
        self.assertFalse(
            SocialAccount.objects.filter(platform_account_id="page-no-credential").exists()
        )

    def test_expired_claim_releases_capacity_and_is_marked_expired(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        first_acceptance, _ = claim_invitation(token, ["facebook"])
        first_acceptance.expires_at = timezone.now() - timedelta(seconds=1)
        first_acceptance.save(update_fields=["expires_at"])

        second_acceptance, _ = claim_invitation(token, ["facebook"])

        first_acceptance.refresh_from_db()
        self.assertEqual(first_acceptance.status, AcceptanceStatus.EXPIRED)
        self.assertEqual(second_acceptance.status, AcceptanceStatus.ACTIVE)

    def test_cancellation_releases_claim_and_is_idempotent(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook"])
        cancelled = cancel_invitation_acceptance(session_token)
        self.assertEqual(cancelled.status, AcceptanceStatus.CANCELLED)
        self.assertEqual(
            cancel_invitation_acceptance(session_token).status,
            AcceptanceStatus.CANCELLED,
        )
        new_acceptance, _ = claim_invitation(token, ["facebook"])
        self.assertEqual(new_acceptance.status, AcceptanceStatus.ACTIVE)

    def test_revoked_invitation_blocks_acceptance_completion(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook"])
        invitation = result["invitation"]
        invitation.status = InvitationStatus.REVOKED
        invitation.save(update_fields=["status"])
        with self.assertRaises(InvalidInvitation):
            persist_invitation_account(
                session_token,
                lambda **kwargs: create_connected_account(
                    kwargs["organization"], "page-revoked-1", SocialPlatform.FACEBOOK
                ),
            )
        self.assertFalse(SocialAccount.objects.filter(platform_account_id="page-revoked-1").exists())

    def test_acceptance_context_derives_org_and_platforms_from_invitation(self):
        result = self.create_share()
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook"])
        context = get_invitation_acceptance_context(session_token)
        self.assertEqual(context["organization"].pk, self.organization.pk)
        self.assertEqual(context["allowed_platforms"], ("facebook", "instagram"))
        self.assertEqual(context["selected_platforms"], ("facebook",))

    def test_oauth_attempt_state_is_one_time_and_platform_bound(self):
        result = self.create_share()
        token = result["share_url"].split("#", 1)[1]
        _, acceptance_token = claim_invitation(token, ["facebook"])
        attempt, state = create_invitation_oauth_attempt(
            acceptance_token, InvitationOAuthPlatform.FACEBOOK
        )

        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(
                state,
                expected_platform=InvitationOAuthPlatform.INSTAGRAM,
            )

        consumed = consume_invitation_oauth_attempt(
            state,
            expected_platform=InvitationOAuthPlatform.FACEBOOK,
        )
        self.assertEqual(consumed["attempt_id"], attempt.pk)
        self.assertEqual(consumed["organization"].pk, self.organization.pk)
        self.assertEqual(consumed["platform"], InvitationOAuthPlatform.FACEBOOK)
        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(state)

    def test_oauth_attempt_rejects_tampered_and_expired_state(self):
        result = self.create_share()
        token = result["share_url"].split("#", 1)[1]
        _, acceptance_token = claim_invitation(token, ["facebook"])
        attempt, state = create_invitation_oauth_attempt(
            acceptance_token, InvitationOAuthPlatform.FACEBOOK
        )

        tampered_state = ("A" if state[0] != "A" else "B") + state[1:]
        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(tampered_state)

        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=["expires_at"])
        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(state)

    def test_oauth_attempt_cannot_be_consumed_after_invitation_revocation(self):
        result = self.create_share()
        token = result["share_url"].split("#", 1)[1]
        _, acceptance_token = claim_invitation(token, ["facebook"])
        _, state = create_invitation_oauth_attempt(
            acceptance_token, InvitationOAuthPlatform.FACEBOOK
        )
        invitation = result["invitation"]
        invitation.status = InvitationStatus.REVOKED
        invitation.save(update_fields=["status"])

        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(state)

    def test_persistence_boundary_rejects_wrong_org_and_rolls_back(self):
        result = self.create_share(usage_limit=1)
        token = result["share_url"].split("#", 1)[1]
        _, session_token = claim_invitation(token, ["facebook"])
        other_org = Organization.objects.create(
            organization_id="ORG-INV-OTHER",
            name="Other Invitation Org",
            slug="other-invitation-org",
            industry="Retail",
            created_by=self.owner,
        )
        with self.assertRaises(InvitationError):
            persist_invitation_account(
                session_token,
                lambda **kwargs: create_connected_account(
                    other_org, "foreign-page-1", SocialPlatform.FACEBOOK
                ),
            )
        self.assertFalse(SocialAccount.objects.filter(platform_account_id="foreign-page-1").exists())

    def test_claim_rejects_platform_outside_allowlist(self):
        result = self.create_share()
        token = result["share_url"].split("#", 1)[1]
        with self.assertRaises(InvalidInvitation):
            claim_invitation(token, ["linkedin"])


class SocialAccountInvitationDeliveryLifecycleTests(TestCase):
    def setUp(self):
        self.enterContext(self.settings(
            FRONTEND_URL="https://crm.example.test",
            META_CREDENTIAL_ENCRYPTION_KEY=TEST_INVITATION_ENCRYPTION_KEY,
        ))
        self.owner = User.objects.create_user(
            email="delivery@example.com", password="test-password", first_name="Delivery"
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INV-DELIVERY",
            name="Invitation Delivery Org",
            slug="invitation-delivery-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.invitation = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook", "instagram"],
            mode=InvitationMode.EMAIL,
            recipient_email="client@example.com",
        )["invitation"]

    def send_current_invitation(self):
        attempt = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(
            mark_email_invitation_sent(self.invitation, attempt["attempt_id"])
        )
        return attempt

    def claim_acceptance(self, link, platforms=None):
        return claim_invitation(
            link["token"],
            platforms or [SocialPlatform.INSTAGRAM],
        )

    def create_staging_sessions(self, acceptance_token):
        now = timezone.now()
        meta_attempt, meta_state = create_invitation_oauth_attempt(
            acceptance_token, SocialPlatform.FACEBOOK
        )
        meta_context = consume_invitation_oauth_attempt(
            meta_state, expected_platform=SocialPlatform.FACEBOOK
        )
        instagram_attempt, instagram_state = create_invitation_oauth_attempt(
            acceptance_token, SocialPlatform.INSTAGRAM
        )
        instagram_context = consume_invitation_oauth_attempt(
            instagram_state, expected_platform=SocialPlatform.INSTAGRAM
        )
        meta_session = InvitationMetaOAuthSession.objects.create(
            acceptance_id=meta_context["acceptance_id"],
            oauth_attempt=meta_attempt,
            provider_user_id="resend-meta-user",
            encrypted_access_token="encrypted-meta-user-token",
            encrypted_accounts="encrypted-page-token-payload",
            expires_at=now + timedelta(minutes=5),
        )
        instagram_session = InvitationInstagramOAuthSession.objects.create(
            acceptance_id=instagram_context["acceptance_id"],
            oauth_attempt=instagram_attempt,
            instagram_user_id="resend-instagram-user",
            encrypted_access_token="encrypted-instagram-token",
            token_expires_at=now + timedelta(days=30),
            expires_at=now + timedelta(minutes=5),
        )
        outstanding_attempt, outstanding_state = create_invitation_oauth_attempt(
            acceptance_token, SocialPlatform.FACEBOOK
        )
        return (
            meta_session,
            instagram_session,
            outstanding_attempt,
            outstanding_state,
        )

    def test_valid_provider_message_id_is_stored_without_truncation(self):
        attempt = prepare_email_invitation_delivery(self.invitation)
        message_id = "m" * SocialAccountInvitation._meta.get_field(
            "provider_message_id"
        ).max_length

        self.assertTrue(mark_email_invitation_sent(
            self.invitation, attempt["attempt_id"], message_id
        ))
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.provider_message_id, message_id)
        self.assertEqual(
            self.invitation.token_hash,
            hashlib.sha256(attempt["token"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(self.invitation.pending_token_hash, "")

    def test_missing_provider_message_id_remains_permitted(self):
        attempt = prepare_email_invitation_delivery(self.invitation)

        self.assertTrue(mark_email_invitation_sent(self.invitation, attempt["attempt_id"]))
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.provider_message_id, "")
        self.assertEqual(self.invitation.pending_token_hash, "")

    def test_failed_initial_delivery_keeps_invitation_unusable(self):
        attempt = prepare_email_invitation_delivery(self.invitation)

        self.assertTrue(
            mark_email_invitation_failed(
                self.invitation, attempt["attempt_id"], "provider_rejected"
            )
        )

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.FAILED)
        self.assertTrue(self.invitation.pending_token_hash)
        self.assertFalse(validate_invitation(attempt["token"])["usable"])

    def test_late_success_callback_can_promote_after_initial_failure_callback(self):
        attempt = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(
            mark_email_invitation_failed(
                self.invitation, attempt["attempt_id"], "network_error"
            )
        )
        self.assertFalse(validate_invitation(attempt["token"])["usable"])

        self.assertTrue(
            mark_email_invitation_sent(
                self.invitation,
                attempt["attempt_id"],
                "provider-message-late-success",
            )
        )

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.SENT)
        self.assertTrue(validate_invitation(attempt["token"])["usable"])

    def test_overlong_provider_message_id_is_rejected_without_marking_sent(self):
        attempt = prepare_email_invitation_delivery(self.invitation)
        message_id_limit = SocialAccountInvitation._meta.get_field(
            "provider_message_id"
        ).max_length

        with self.assertRaises(InvitationError):
            mark_email_invitation_sent(
                self.invitation,
                attempt["attempt_id"],
                "m" * (message_id_limit + 1),
            )
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.PENDING)
        self.assertEqual(self.invitation.provider_message_id, "")

    def test_invalid_provider_message_id_types_are_rejected(self):
        attempt = prepare_email_invitation_delivery(self.invitation)

        for message_id in (None, 123):
            with self.subTest(message_id=message_id):
                with self.assertRaises(InvitationError):
                    mark_email_invitation_sent(
                        self.invitation, attempt["attempt_id"], message_id
                    )
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.PENDING)

    def test_prepare_after_sent_requires_explicit_resend(self):
        first = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(self.invitation, first["attempt_id"]))
        self.invitation.refresh_from_db()
        sent_hash = self.invitation.token_hash

        with self.assertRaises(InvitationError):
            prepare_email_invitation_delivery(self.invitation)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.token_hash, sent_hash)
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.SENT)

    def test_stale_success_cannot_mark_newer_attempt_sent(self):
        first = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_failed(
            self.invitation, first["attempt_id"], "provider_rejected"
        ))
        second = retry_email_invitation_delivery(self.invitation, first["attempt_id"])

        self.assertTrue(mark_email_invitation_sent(self.invitation, second["attempt_id"]))
        self.assertFalse(mark_email_invitation_sent(self.invitation, first["attempt_id"]))
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.SENT)
        self.assertEqual(
            self.invitation.token_hash,
            hashlib.sha256(second["token"].encode("utf-8")).hexdigest(),
        )

    def test_stale_resend_success_cannot_promote_after_retry_starts(self):
        first = self.send_current_invitation()
        stale = resend_email_invitation_delivery(self.invitation)
        self.assertTrue(
            mark_email_invitation_failed(
                self.invitation, stale["attempt_id"], "network_error"
            )
        )
        current = retry_email_invitation_delivery(self.invitation, stale["attempt_id"])

        self.assertFalse(
            mark_email_invitation_sent(self.invitation, stale["attempt_id"])
        )
        self.assertTrue(
            validate_invitation(first["token"])["usable"]
        )
        self.assertFalse(validate_invitation(stale["token"])["usable"])
        self.assertTrue(
            mark_email_invitation_sent(self.invitation, current["attempt_id"])
        )
        self.assertFalse(validate_invitation(first["token"])["valid"])
        self.assertTrue(validate_invitation(current["token"])["usable"])

    def test_stale_failure_cannot_overwrite_successful_newer_attempt(self):
        first = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_failed(
            self.invitation, first["attempt_id"], "request_error"
        ))
        second = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(self.invitation, second["attempt_id"]))

        self.assertFalse(mark_email_invitation_failed(
            self.invitation, first["attempt_id"], "provider_rejected"
        ))
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.SENT)

    def test_explicit_resend_stages_new_token_and_stale_callback_is_ignored(self):
        first = prepare_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(self.invitation, first["attempt_id"]))
        self.invitation.refresh_from_db()
        old_hash = self.invitation.token_hash

        second = resend_email_invitation_delivery(self.invitation)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.token_hash, old_hash)
        self.assertTrue(self.invitation.pending_token_hash)
        self.assertTrue(validate_invitation(first["token"])["usable"])
        self.assertFalse(validate_invitation(second["token"])["usable"])
        self.assertFalse(mark_email_invitation_sent(self.invitation, first["attempt_id"]))
        self.assertTrue(mark_email_invitation_sent(self.invitation, second["attempt_id"]))
        self.assertTrue(mark_email_invitation_sent(self.invitation, second["attempt_id"]))
        self.assertFalse(validate_invitation(first["token"])["valid"])
        self.assertTrue(validate_invitation(second["token"])["usable"])

    def test_failed_resend_keeps_the_previously_active_token_usable(self):
        first = self.send_current_invitation()
        resend = resend_email_invitation_delivery(self.invitation)

        self.assertTrue(
            mark_email_invitation_failed(
                self.invitation, resend["attempt_id"], "provider_rejected"
            )
        )

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.SENT)
        self.assertTrue(validate_invitation(first["token"])["valid"])
        self.assertTrue(validate_invitation(first["token"])["usable"])
        self.assertFalse(validate_invitation(resend["token"])["valid"])

    def test_resend_invalidates_active_acceptance_only_after_successful_delivery(self):
        first = self.send_current_invitation()
        acceptance, acceptance_token = self.claim_acceptance(
            first, [SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM]
        )

        resend = resend_email_invitation_delivery(self.invitation)
        acceptance.refresh_from_db()
        self.assertEqual(acceptance.status, AcceptanceStatus.ACTIVE)
        self.assertTrue(validate_invitation(first["token"])["valid"])
        self.assertFalse(validate_invitation(resend["token"])["usable"])
        self.assertEqual(
            get_invitation_acceptance_context(acceptance_token)["organization"].pk,
            self.organization.pk,
        )
        self.assertEqual(self.invitation.usage_count, 0)

        self.assertTrue(
            mark_email_invitation_sent(self.invitation, resend["attempt_id"])
        )

        acceptance.refresh_from_db()
        self.assertEqual(acceptance.status, AcceptanceStatus.CANCELLED)
        with self.assertRaises(InvalidInvitation):
            get_invitation_acceptance_context(acceptance_token)
        self.assertFalse(validate_invitation(first["token"])["valid"])
        self.assertTrue(validate_invitation(resend["token"])["usable"])
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.usage_count, 0)

    def test_resend_clears_facebook_and_instagram_staging_and_rejects_old_oauth_state(self):
        first = self.send_current_invitation()
        acceptance, acceptance_token = self.claim_acceptance(
            first, [SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM]
        )
        meta_session, instagram_session, outstanding_attempt, outstanding_state = (
            self.create_staging_sessions(acceptance_token)
        )
        resend = resend_email_invitation_delivery(self.invitation)

        self.assertTrue(
            mark_email_invitation_sent(self.invitation, resend["attempt_id"])
        )

        acceptance.refresh_from_db()
        meta_session.refresh_from_db()
        instagram_session.refresh_from_db()
        outstanding_attempt.refresh_from_db()
        self.assertEqual(acceptance.status, AcceptanceStatus.CANCELLED)
        self.assertEqual(meta_session.encrypted_access_token, "")
        self.assertEqual(meta_session.encrypted_accounts, "")
        self.assertEqual(instagram_session.status, InvitationInstagramOAuthStatus.INVALIDATED)
        self.assertEqual(instagram_session.encrypted_access_token, "")
        self.assertLessEqual(outstanding_attempt.expires_at, timezone.now())
        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(outstanding_state)
        self.assertTrue(validate_invitation(resend["token"])["usable"])

    def test_failed_resend_preserves_claim_until_retry_is_successfully_delivered(self):
        first = self.send_current_invitation()
        acceptance, acceptance_token = self.claim_acceptance(
            first, [SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM]
        )
        (
            meta_session,
            instagram_session,
            outstanding_attempt,
            outstanding_state,
        ) = self.create_staging_sessions(acceptance_token)

        failed_resend = resend_email_invitation_delivery(self.invitation)
        self.assertTrue(
            mark_email_invitation_failed(
                self.invitation,
                failed_resend["attempt_id"],
                "provider_rejected",
            )
        )
        acceptance.refresh_from_db()
        meta_session.refresh_from_db()
        instagram_session.refresh_from_db()
        self.assertEqual(acceptance.status, AcceptanceStatus.ACTIVE)
        self.assertTrue(meta_session.encrypted_access_token)
        self.assertTrue(instagram_session.encrypted_access_token)
        outstanding_attempt.refresh_from_db()
        self.assertGreater(outstanding_attempt.expires_at, timezone.now())
        self.assertTrue(validate_invitation(first["token"])["valid"])
        self.assertFalse(validate_invitation(failed_resend["token"])["usable"])
        self.assertEqual(
            get_invitation_acceptance_context(acceptance_token)["organization"].pk,
            self.organization.pk,
        )

        retry = retry_email_invitation_delivery(
            self.invitation, failed_resend["attempt_id"]
        )
        self.assertTrue(mark_email_invitation_sent(self.invitation, retry["attempt_id"]))

        acceptance.refresh_from_db()
        meta_session.refresh_from_db()
        instagram_session.refresh_from_db()
        outstanding_attempt.refresh_from_db()
        self.assertEqual(acceptance.status, AcceptanceStatus.CANCELLED)
        self.assertEqual(meta_session.encrypted_access_token, "")
        self.assertEqual(instagram_session.encrypted_access_token, "")
        self.assertLessEqual(outstanding_attempt.expires_at, timezone.now())
        with self.assertRaises(InvalidInvitation):
            consume_invitation_oauth_attempt(outstanding_state)
        self.assertTrue(validate_invitation(retry["token"])["usable"])
        self.assertEqual(self.invitation.usage_count, 0)

    def test_in_flight_resend_retry_reuses_same_token_until_failure_is_confirmed(self):
        self.send_current_invitation()
        pending = resend_email_invitation_delivery(self.invitation)

        recovered = retry_email_invitation_delivery(self.invitation, pending["attempt_id"])
        self.assertEqual(recovered["attempt_id"], pending["attempt_id"])
        self.assertEqual(recovered["token"], pending["token"])

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_attempts, pending["attempt_id"])
        self.assertTrue(self.invitation.pending_token_hash)
        self.assertTrue(self.invitation.pending_delivery_token_encrypted)
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.SENT)

        self.assertTrue(
            mark_email_invitation_failed(
                self.invitation, pending["attempt_id"], "network_error"
            )
        )
        retry = retry_email_invitation_delivery(self.invitation, pending["attempt_id"])
        self.assertGreater(retry["attempt_id"], pending["attempt_id"])
        self.assertNotEqual(retry["token"], pending["token"])

    def test_provider_success_with_lost_callback_can_be_reconciled_by_replaying_callback(self):
        first = self.send_current_invitation()
        resend = resend_email_invitation_delivery(self.invitation)

        # Provider send succeeds, but its application callback is lost. The
        # durable pending hash and attempt ID allow the caller to replay it.
        self.assertTrue(validate_invitation(first["token"])["usable"])
        self.assertFalse(validate_invitation(resend["token"])["usable"])
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_attempts, resend["attempt_id"])
        self.assertEqual(
            self.invitation.pending_token_hash,
            hashlib.sha256(resend["token"].encode("utf-8")).hexdigest(),
        )

        recovered_attempt = retry_email_invitation_delivery(
            self.invitation,
            resend["attempt_id"],
        )
        self.assertEqual(recovered_attempt["token"], resend["token"])
        self.assertEqual(recovered_attempt["attempt_id"], resend["attempt_id"])
        recovered = mark_email_invitation_sent(
            self.invitation,
            recovered_attempt["attempt_id"],
            "provider-message-recovered",
        )

        self.assertTrue(recovered)
        self.assertTrue(validate_invitation(resend["token"])["usable"])
        self.assertFalse(validate_invitation(first["token"])["valid"])

    def test_repeated_resend_releases_reservations_and_preserves_completed_history(self):
        first = self.send_current_invitation()
        completed = SocialAccountInvitationAcceptance.objects.create(
            invitation=self.invitation,
            token_hash="f" * 64,
            selected_platforms=[SocialPlatform.INSTAGRAM],
            status=AcceptanceStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(minutes=30),
            completed_at=timezone.now(),
        )
        completed_audit = SocialAccountInvitationAcceptanceAccount.objects.create(
            acceptance=completed,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="historical-instagram-account",
        )
        first_acceptance, _first_acceptance_token = self.claim_acceptance(first)

        second = resend_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(self.invitation, second["attempt_id"]))
        first_acceptance.refresh_from_db()
        self.assertEqual(first_acceptance.status, AcceptanceStatus.CANCELLED)
        self.assertTrue(validate_invitation(second["token"])["usable"])

        second_acceptance, _second_acceptance_token = self.claim_acceptance(second)
        third = resend_email_invitation_delivery(self.invitation)
        self.assertTrue(mark_email_invitation_sent(self.invitation, third["attempt_id"]))

        second_acceptance.refresh_from_db()
        completed.refresh_from_db()
        self.assertEqual(second_acceptance.status, AcceptanceStatus.CANCELLED)
        self.assertEqual(completed.status, AcceptanceStatus.COMPLETED)
        self.assertTrue(
            SocialAccountInvitationAcceptanceAccount.objects.filter(
                pk=completed_audit.pk,
                acceptance=completed,
            ).exists()
        )
        self.assertTrue(validate_invitation(third["token"])["usable"])
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.usage_count, 0)

    def test_initial_pending_retry_reuses_token_without_superseding_attempt(self):
        first = prepare_email_invitation_delivery(self.invitation)
        pending_hash = self.invitation.pending_token_hash

        retry = retry_email_invitation_delivery(self.invitation, first["attempt_id"])
        self.assertEqual(retry["attempt_id"], first["attempt_id"])
        self.assertEqual(retry["token"], first["token"])

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_attempts, first["attempt_id"])
        self.assertEqual(self.invitation.pending_token_hash, pending_hash)
        self.assertTrue(self.invitation.pending_delivery_token_encrypted)
        self.assertEqual(self.invitation.delivery_status, DeliveryStatus.PENDING)
        self.assertTrue(mark_email_invitation_sent(self.invitation, first["attempt_id"]))
        self.assertTrue(validate_invitation(first["token"])["usable"])
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.pending_delivery_token_encrypted, "")

    def test_cleanup_clears_expired_pending_invitation_delivery_token(self):
        attempt = prepare_email_invitation_delivery(self.invitation)
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.pending_delivery_token_encrypted)
        self.invitation.expires_at = timezone.now() - timedelta(seconds=1)
        self.invitation.save(update_fields=["expires_at"])

        result = cleanup_expired_invitation_oauth_secrets(batch_size=20)

        self.invitation.refresh_from_db()
        self.assertGreaterEqual(result["invitation_delivery_tokens_cleared"], 1)
        self.assertEqual(self.invitation.pending_token_hash, "")
        self.assertEqual(self.invitation.pending_delivery_token_encrypted, "")
        with self.assertRaises(InvitationError):
            retry_email_invitation_delivery(self.invitation, attempt["attempt_id"])

    def test_revoked_or_expired_invitation_cannot_be_reactivated_by_retry_or_callback(self):
        revoked = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=InvitationMode.EMAIL,
            recipient_email="revoked@example.test",
        )["invitation"]
        revoked_attempt = prepare_email_invitation_delivery(revoked)
        revoke_invitation(revoked)
        revoked.refresh_from_db()
        self.assertEqual(revoked.pending_token_hash, "")
        self.assertEqual(revoked.pending_delivery_token_encrypted, "")

        with self.assertRaises(InvitationError):
            retry_email_invitation_delivery(revoked, revoked_attempt["attempt_id"])
        self.assertFalse(
            mark_email_invitation_sent(revoked, revoked_attempt["attempt_id"])
        )
        revoked.refresh_from_db()
        self.assertEqual(revoked.status, InvitationStatus.REVOKED)
        self.assertFalse(validate_invitation(revoked_attempt["token"])["valid"])

        expired = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=InvitationMode.EMAIL,
            recipient_email="expired@example.test",
        )["invitation"]
        expired_attempt = prepare_email_invitation_delivery(expired)
        expired.expires_at = timezone.now() - timedelta(seconds=1)
        expired.save(update_fields=["expires_at"])

        with self.assertRaises(InvitationError):
            retry_email_invitation_delivery(expired, expired_attempt["attempt_id"])
        # The callback is handled, but it marks the invitation expired rather
        # than promoting the pending token.
        self.assertTrue(
            mark_email_invitation_sent(expired, expired_attempt["attempt_id"])
        )
        expired.refresh_from_db()
        self.assertEqual(expired.status, InvitationStatus.EXPIRED)
        self.assertEqual(expired.delivery_status, DeliveryStatus.FAILED)
        self.assertFalse(validate_invitation(expired_attempt["token"])["valid"])

    def test_failure_code_is_allowlisted_and_never_stores_exception_text(self):
        attempt = prepare_email_invitation_delivery(self.invitation)
        supplied = "Provider failure invitation_url=https://example/#secret-token"
        self.assertTrue(mark_email_invitation_failed(
            self.invitation, attempt["attempt_id"], supplied
        ))
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.delivery_error_code, "delivery_error")
        self.assertNotIn("secret-token", self.invitation.delivery_error_code)


class SocialAccountInvitationPendingTokenMigrationTests(TransactionTestCase):
    """Verify the 0010 backfill using historical models without live schema assumptions."""

    migrate_from = ("social_accounts", "0009_socialaccountinvitationoauthattempt")
    migrate_to = ("social_accounts", "0010_socialaccountinvitation_pending_token_hash")

    def setUp(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        self.old_apps = self.executor.loader.project_state([self.migrate_from]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _create_legacy_invitation(
        self,
        Invitation,
        *,
        raw_token,
        delivery_status,
        status="pending",
        usage_count=0,
        delivery_attempts=0,
        provider_message_id="",
        delivery_error_code="",
    ):
        Organization = self.old_apps.get_model("organizations", "Organization")
        organization = Organization.objects.create(
            organization_id=f"ORG-MIG-{raw_token[:8]}",
            name=f"Migration {raw_token[:8]}",
            slug=f"migration-{raw_token[:8]}",
            industry="Testing",
        )
        return Invitation.objects.create(
            organization_id=organization.pk,
            mode="email",
            recipient_email=f"{raw_token[:8]}@example.test",
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            allowed_platforms=["instagram"],
            status=status,
            expires_at=timezone.now() + timedelta(days=2),
            usage_limit=1,
            usage_count=usage_count,
            delivery_status=delivery_status,
            delivery_attempts=delivery_attempts,
            provider_message_id=provider_message_id,
            delivery_error_code=delivery_error_code,
        )

    def test_migration_backfills_only_legacy_pending_delivery_hashes(self):
        Invitation = self.old_apps.get_model(
            "social_accounts", "SocialAccountInvitation"
        )
        raw_tokens = {
            "pending_configuration": "never-sent-token",
            "initial_pending": "pending-delivery-token",
            "resend_pending": "pending-resend-token",
            "failed": "failed-delivery-token",
            "resend_failed": "failed-resend-token",
            "sent": "sent-delivery-token",
            "completed": "completed-invitation-token",
        }
        legacy = {
            "pending_configuration": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["pending_configuration"],
                delivery_status="pending_configuration",
            ),
            "initial_pending": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["initial_pending"],
                delivery_status="pending",
                delivery_attempts=1,
            ),
            # The prior implementation had already overwritten the active
            # hash, so this row contains only the resend token hash.
            "resend_pending": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["resend_pending"],
                delivery_status="pending",
                delivery_attempts=2,
                provider_message_id="previous-successful-message",
            ),
            "failed": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["failed"],
                delivery_status="failed",
                delivery_attempts=1,
                delivery_error_code="provider_rejected",
            ),
            "resend_failed": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["resend_failed"],
                delivery_status="failed",
                delivery_attempts=2,
                provider_message_id="previous-successful-message",
                delivery_error_code="provider_rejected",
            ),
            "sent": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["sent"],
                delivery_status="sent",
            ),
            "completed": self._create_legacy_invitation(
                Invitation,
                raw_token=raw_tokens["completed"],
                delivery_status="sent",
                status="accepted",
                usage_count=1,
            ),
        }

        Acceptance = self.old_apps.get_model(
            "social_accounts", "SocialAccountInvitationAcceptance"
        )
        completed_acceptance = Acceptance.objects.create(
            invitation_id=legacy["completed"].pk,
            token_hash="a" * 64,
            selected_platforms=["instagram"],
            status="completed",
            expires_at=timezone.now() + timedelta(days=1),
            completed_at=timezone.now(),
        )
        AuditAssociation = self.old_apps.get_model(
            "social_accounts", "SocialAccountInvitationAcceptanceAccount"
        )
        audit = AuditAssociation.objects.create(
            acceptance_id=completed_acceptance.pk,
            platform="instagram",
            platform_account_id="legacy-instagram-account",
        )

        MigrationExecutor(connection).migrate([self.migrate_to])
        new_apps = MigrationExecutor(connection).loader.project_state(
            [self.migrate_to]
        ).apps
        MigratedInvitation = new_apps.get_model(
            "social_accounts", "SocialAccountInvitation"
        )

        expected_pending = {
            "pending_configuration": "",
            "initial_pending": legacy["initial_pending"].token_hash,
            "resend_pending": legacy["resend_pending"].token_hash,
            "failed": "",
            "resend_failed": "",
            "sent": "",
            "completed": "",
        }
        expected_delivery_status = {
            "pending_configuration": "pending_configuration",
            "initial_pending": "pending",
            "resend_pending": "pending",
            "failed": "failed",
            "resend_failed": "failed",
            "sent": "sent",
            "completed": "sent",
        }
        for state, original in legacy.items():
            with self.subTest(state=state):
                migrated = MigratedInvitation.objects.get(pk=original.pk)
                self.assertEqual(migrated.token_hash, original.token_hash)
                self.assertEqual(migrated.pending_token_hash, expected_pending[state])
                self.assertEqual(
                    migrated.delivery_status,
                    expected_delivery_status[state],
                )

        for state in (
            "pending_configuration",
            "initial_pending",
            "resend_pending",
            "failed",
            "resend_failed",
        ):
            with self.subTest(unusable_state=state):
                self.assertFalse(validate_invitation(raw_tokens[state])["usable"])
        self.assertTrue(validate_invitation(raw_tokens["sent"])["usable"])

        MigratedAcceptance = new_apps.get_model(
            "social_accounts", "SocialAccountInvitationAcceptance"
        )
        migrated_acceptance = MigratedAcceptance.objects.get(pk=completed_acceptance.pk)
        self.assertEqual(migrated_acceptance.status, "completed")
        self.assertEqual(migrated_acceptance.completed_at, completed_acceptance.completed_at)
        completed_invitation = MigratedInvitation.objects.get(
            pk=legacy["completed"].pk
        )
        self.assertEqual(completed_invitation.status, "accepted")
        self.assertEqual(completed_invitation.usage_count, 1)
        MigratedAuditAssociation = new_apps.get_model(
            "social_accounts", "SocialAccountInvitationAcceptanceAccount"
        )
        migrated_audit = MigratedAuditAssociation.objects.get(pk=audit.pk)
        self.assertEqual(migrated_audit.acceptance_id, completed_acceptance.pk)
        self.assertEqual(migrated_audit.platform, "instagram")
        self.assertEqual(migrated_audit.platform_account_id, "legacy-instagram-account")

    def test_backfill_preserves_an_already_populated_pending_hash(self):
        MigrationExecutor(connection).migrate([self.migrate_to])
        new_apps = MigrationExecutor(connection).loader.project_state(
            [self.migrate_to]
        ).apps
        Invitation = new_apps.get_model(
            "social_accounts", "SocialAccountInvitation"
        )
        original_hash = hashlib.sha256(b"existing-active-token").hexdigest()
        pending_hash = hashlib.sha256(b"existing-pending-token").hexdigest()
        organization = new_apps.get_model("organizations", "Organization").objects.create(
            organization_id="ORG-MIG-EXISTING",
            name="Migration Existing Pending",
            slug="migration-existing-pending",
            industry="Testing",
        )
        invitation = Invitation.objects.create(
            organization_id=organization.pk,
            mode="email",
            recipient_email="existing-pending@example.test",
            token_hash=original_hash,
            pending_token_hash=pending_hash,
            allowed_platforms=["instagram"],
            status="pending",
            expires_at=timezone.now() + timedelta(days=2),
            usage_limit=1,
            delivery_status="pending",
        )

        migration_module = import_module(
            "apps.social_accounts.migrations.0010_socialaccountinvitation_pending_token_hash"
        )
        migration_module.copy_legacy_pending_hashes(new_apps, schema_editor=None)

        invitation.refresh_from_db()
        self.assertEqual(invitation.token_hash, original_hash)
        self.assertEqual(invitation.pending_token_hash, pending_hash)
        self.assertEqual(invitation.delivery_status, "pending")


class SocialAccountInvitationEncryptedDeliveryTokenMigrationTests(TransactionTestCase):
    migrate_from = ("social_accounts", "0010_socialaccountinvitation_pending_token_hash")
    migrate_to = (
        "social_accounts",
        "0011_socialaccountinvitation_pending_delivery_token_encrypted",
    )

    def setUp(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        self.old_apps = self.executor.loader.project_state([self.migrate_from]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_adds_blank_encrypted_token_without_changing_existing_delivery_state(self):
        Organization = self.old_apps.get_model("organizations", "Organization")
        Invitation = self.old_apps.get_model(
            "social_accounts", "SocialAccountInvitation"
        )
        organization = Organization.objects.create(
            organization_id="ORG-MIG-ENC",
            name="Encrypted Token Migration",
            slug="encrypted-token-migration",
            industry="Testing",
        )
        original_hash = hashlib.sha256(b"pending-delivery-token").hexdigest()
        invitation = Invitation.objects.create(
            organization_id=organization.pk,
            mode="email",
            recipient_email="client@example.test",
            token_hash=hashlib.sha256(b"active-token").hexdigest(),
            pending_token_hash=original_hash,
            allowed_platforms=["facebook"],
            status="pending",
            expires_at=timezone.now() + timedelta(hours=72),
            usage_limit=1,
            usage_count=0,
            delivery_status="pending",
            delivery_attempts=1,
        )

        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_to])
        new_apps = self.executor.loader.project_state([self.migrate_to]).apps
        MigratedInvitation = new_apps.get_model(
            "social_accounts", "SocialAccountInvitation"
        )
        migrated = MigratedInvitation.objects.get(pk=invitation.pk)
        self.assertEqual(migrated.token_hash, invitation.token_hash)
        self.assertEqual(migrated.pending_token_hash, original_hash)
        self.assertEqual(migrated.pending_delivery_token_encrypted, "")
        self.assertEqual(migrated.delivery_status, "pending")


@skipUnless(connection.vendor == "postgresql", "select_for_update concurrency requires PostgreSQL")
class SocialAccountInvitationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.enterContext(self.settings(
            FRONTEND_URL="https://crm.example.test",
            META_CREDENTIAL_ENCRYPTION_KEY=TEST_INVITATION_ENCRYPTION_KEY,
        ))
        self.owner = User.objects.create_user(
            email="concurrency@example.com", password="test-password", first_name="Concurrent"
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INV-CONCURRENT",
            name="Invitation Concurrent Org",
            slug="invitation-concurrent-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.result = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=["facebook"],
            mode=InvitationMode.SHARE_LINK,
            usage_limit=1,
        )
        self.token = self.result["share_url"].split("#", 1)[1]

    def test_simultaneous_claims_cannot_exceed_usage_limit(self):
        barrier = Barrier(2)

        def attempt_claim():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                claim_invitation(self.token, ["facebook"])
                return "claimed"
            except InvalidInvitation:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: attempt_claim(), range(2)))

        self.assertEqual(outcomes.count("claimed"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)
        self.assertEqual(
            SocialAccountInvitationAcceptance.objects.filter(
                invitation=self.result["invitation"],
                status=AcceptanceStatus.ACTIVE,
                expires_at__gt=timezone.now(),
            ).count(),
            1,
        )

    def test_simultaneous_oauth_callbacks_consume_attempt_once(self):
        _, acceptance_token = claim_invitation(self.token, ["facebook"])
        attempt, state = create_invitation_oauth_attempt(
            acceptance_token, InvitationOAuthPlatform.FACEBOOK
        )
        barrier = Barrier(2)

        def consume_state():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                consume_invitation_oauth_attempt(
                    state,
                    expected_platform=InvitationOAuthPlatform.FACEBOOK,
                )
                return "consumed"
            except InvalidInvitation:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: consume_state(), range(2)))

        self.assertEqual(outcomes.count("consumed"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.consumed_at)

    def test_simultaneous_completion_requests_increment_usage_once(self):
        _, acceptance_token = claim_invitation(self.token, ["facebook"])
        persist_invitation_account(
            acceptance_token,
            lambda **kwargs: create_connected_account(
                kwargs["organization"], "concurrent-completion-page", SocialPlatform.FACEBOOK
            ),
        )
        completion_url = reverse("social-account-invitation-complete")
        barrier = Barrier(2)

        def complete_request():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                response = APIClient().post(
                    completion_url,
                    {"acceptance_token": acceptance_token},
                    format="json",
                )
                return response.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: complete_request(), range(2)))

        self.assertEqual(statuses, [200, 200])
        self.result["invitation"].refresh_from_db()
        self.assertEqual(self.result["invitation"].usage_count, 1)
        self.assertEqual(
            SocialAccountInvitationAcceptance.objects.filter(
                invitation=self.result["invitation"],
                status=AcceptanceStatus.COMPLETED,
            ).count(),
            1,
        )

    def _sent_email_invitation(self):
        invitation = create_invitation(
            organization=self.organization,
            inviter=self.owner,
            platforms=[SocialPlatform.FACEBOOK],
            mode=InvitationMode.EMAIL,
            recipient_email="concurrent-client@example.test",
        )["invitation"]
        delivery = prepare_email_invitation_delivery(invitation)
        mark_email_invitation_sent(invitation, delivery["attempt_id"])
        return invitation, delivery

    def test_concurrent_resend_starts_only_one_pending_attempt(self):
        invitation, first_delivery = self._sent_email_invitation()
        barrier = Barrier(2)

        def start_resend():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                resend_email_invitation_delivery(invitation)
                return "started"
            except InvitationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _index: start_resend(), range(2)))

        self.assertEqual(outcomes.count("started"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)
        invitation.refresh_from_db()
        self.assertEqual(invitation.token_hash, hashlib.sha256(
            first_delivery["token"].encode("utf-8")
        ).hexdigest())
        self.assertTrue(invitation.pending_token_hash)

    def test_concurrent_retries_allow_only_the_current_attempt_to_supersede(self):
        invitation, _first_delivery = self._sent_email_invitation()
        pending = resend_email_invitation_delivery(invitation)
        self.assertTrue(
            mark_email_invitation_failed(
                invitation, pending["attempt_id"], "network_error"
            )
        )
        barrier = Barrier(2)

        def retry_resend():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                retry_email_invitation_delivery(invitation, pending["attempt_id"])
                return "retried"
            except InvitationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _index: retry_resend(), range(2)))

        self.assertEqual(outcomes.count("retried"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)
        invitation.refresh_from_db()
        self.assertEqual(invitation.delivery_attempts, pending["attempt_id"] + 1)
        self.assertTrue(invitation.pending_token_hash)
