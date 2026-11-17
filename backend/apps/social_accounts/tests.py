from datetime import date, timedelta
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.integrations.instagram.crypto import (
    decrypt_token as decrypt_instagram_token,
    encrypt_token as encrypt_instagram_token,
)
from apps.integrations.instagram.lifecycle import InstagramTokenLifecycleService
from apps.integrations.instagram.models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
)
from apps.integrations.instagram.selectors import get_active_instagram_credential
from apps.integrations.instagram.services import (
    InstagramOAuthResult,
    InstagramOAuthService,
)
from apps.integrations.meta.credentials import MetaCredentialService
from apps.integrations.meta.crypto import (
    decrypt_token as decrypt_meta_token,
    encrypt_token as encrypt_meta_token,
)
from apps.integrations.meta.exceptions import MetaIntegrationError
from apps.integrations.meta.lifecycle import MetaTokenLifecycleService
from apps.integrations.meta.models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
)
from apps.integrations.meta.services import MetaOAuthService
from apps.insights.models import InsightsAccountSnapshot, InsightsMediaSnapshot
from apps.organizations.models import Organization
from apps.social_accounts.lifecycle import disconnect_social_account_with_credentials
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialPlatform,
)
from apps.social_accounts.services import delete_social_account


class SocialAccountCleanupLifecycleTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="social-cleanup-owner@example.com",
            first_name="Social Cleanup Owner",
            password="password",
        )
        self.keep_organization = Organization.objects.create(
            organization_id="ORG-CLEANUP-KEEP",
            name="Keep Organization",
            slug="keep-organization",
            industry="Retail",
            created_by=self.owner,
        )
        self.outside_organization = Organization.objects.create(
            organization_id="ORG-CLEANUP-OUTSIDE",
            name="Outside Organization",
            slug="outside-organization",
            industry="Retail",
            created_by=self.owner,
        )
        self.keep_account = self.make_account(self.keep_organization, "keep")
        self.outside_account = self.make_account(self.outside_organization, "outside")
        self.credential = InstagramAccountCredential.objects.create(
            social_account=self.outside_account,
            encrypted_access_token="encrypted-test-token",
        )
        self.snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.outside_account,
            since=date(2026, 9, 1),
            until=date(2026, 9, 7),
            api_version="v26.0",
            metrics={"reach": {"value": 10, "availability": "available"}},
            fetched_at=timezone.now(),
        )
        self.media_snapshot = InsightsMediaSnapshot.objects.create(
            social_account=self.outside_account,
            provider_media_id="media-test-1",
            api_version="v26.0",
            metrics={"reach": {"value": 5, "availability": "available"}},
        )

    @staticmethod
    def make_account(organization, suffix):
        return SocialAccount.objects.create(
            organization=organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id=f"cleanup-{suffix}",
            username=f"cleanup-{suffix}",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )

    def test_soft_cleanup_preserves_target_organization_and_historical_records(self):
        candidates = SocialAccount.objects.filter(is_deleted=False).exclude(
            organization=self.keep_organization,
        )
        self.assertEqual(list(candidates.values_list("id", flat=True)), [self.outside_account.id])

        for account in candidates:
            disconnect_social_account_with_credentials(social_account=account)
            delete_social_account(social_account=account)

        self.keep_account.refresh_from_db()
        self.outside_account.refresh_from_db()
        self.credential.refresh_from_db()
        self.assertFalse(self.keep_account.is_deleted)
        self.assertEqual(self.keep_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(self.outside_account.is_deleted)
        self.assertEqual(self.outside_account.status, SocialAccountStatus.DISCONNECTED)
        self.assertEqual(self.credential.status, InstagramCredentialStatus.REVOKED)
        self.assertEqual(self.credential.encrypted_access_token, "")
        self.assertTrue(InsightsAccountSnapshot.objects.filter(pk=self.snapshot.pk).exists())
        self.assertTrue(InsightsMediaSnapshot.objects.filter(pk=self.media_snapshot.pk).exists())
        self.assertEqual(Organization.objects.count(), 2)
        self.assertEqual(
            SocialAccount.objects.filter(organization=self.keep_organization, is_deleted=False).count(),
            1,
        )


@override_settings(META_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode())
class SocialAccountDisconnectCredentialTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="disconnect-credentials@example.com",
            first_name="Disconnect Credentials",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-DISCONNECT-CREDENTIALS",
            name="Disconnect Credentials",
            slug="disconnect-credentials",
            industry="Retail",
            created_by=self.owner,
        )

    def make_account(self, platform, suffix):
        return SocialAccount.objects.create(
            organization=self.organization,
            platform=platform,
            platform_account_id=f"disconnect-{suffix}",
            account_name=f"Disconnect {suffix}",
            username=f"disconnect_{suffix}",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )

    def test_facebook_disconnect_clears_page_token_and_preserves_shared_user(self):
        connection = SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id="meta-user-disconnect-test",
        )
        account = self.make_account(SocialPlatform.FACEBOOK, "facebook")
        account.connection = connection
        account.save(update_fields=["connection"])
        page_expiry = timezone.now() + timedelta(days=10)
        user_credential = MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token=encrypt_meta_token("shared-user-token-fixture"),
            status=MetaCredentialStatus.ACTIVE,
        )
        page_credential = MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token=encrypt_meta_token("page-token-fixture"),
            token_expires_at=page_expiry,
            status=MetaCredentialStatus.ACTIVE,
        )
        shared_user_ciphertext = user_credential.access_token

        disconnect_social_account_with_credentials(social_account=account)

        page_credential.refresh_from_db()
        user_credential.refresh_from_db()
        self.assertTrue(
            MetaAccountCredential.objects.filter(pk=page_credential.pk).exists()
        )
        self.assertEqual(page_credential.access_token, "")
        self.assertEqual(page_credential.status, MetaCredentialStatus.REVOKED)
        self.assertEqual(page_credential.token_expires_at, page_expiry)
        self.assertEqual(user_credential.access_token, shared_user_ciphertext)
        self.assertEqual(user_credential.status, MetaCredentialStatus.ACTIVE)
        with self.assertRaises(MetaIntegrationError):
            MetaCredentialService.get_access_token(social_account=account)

        lifecycle = MetaTokenLifecycleService(api_client=MagicMock())
        self.assertEqual(lifecycle.refresh_due_credentials()["checked"], 0)

    def test_facebook_reconnect_stores_a_fresh_encrypted_token(self):
        account = self.make_account(SocialPlatform.FACEBOOK, "facebook-reconnect")
        credential = MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token="old-page-ciphertext-fixture",
            status=MetaCredentialStatus.REVOKED,
        )

        reconnected = MetaOAuthService()._save_page_credential(
            social_account=account,
            page_access_token="fresh-page-token-fixture",
        )

        credential.refresh_from_db()
        self.assertEqual(reconnected.pk, credential.pk)
        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(
            decrypt_meta_token(credential.access_token),
            "fresh-page-token-fixture",
        )

    def test_instagram_disconnect_clears_token_and_reconnect_restores_active_credential(self):
        account = self.make_account(SocialPlatform.INSTAGRAM, "instagram")
        original_expiry = timezone.now() + timedelta(days=30)
        credential = InstagramAccountCredential.objects.create(
            social_account=account,
            encrypted_access_token=encrypt_instagram_token("instagram-token-fixture"),
            token_expires_at=original_expiry,
            status=InstagramCredentialStatus.ACTIVE,
        )

        disconnect_social_account_with_credentials(social_account=account)

        credential.refresh_from_db()
        self.assertTrue(
            InstagramAccountCredential.objects.filter(pk=credential.pk).exists()
        )
        self.assertEqual(credential.encrypted_access_token, "")
        self.assertEqual(credential.status, InstagramCredentialStatus.REVOKED)
        self.assertEqual(credential.token_expires_at, original_expiry)
        self.assertIsNone(get_active_instagram_credential(social_account=account))

        lifecycle = InstagramTokenLifecycleService.__new__(
            InstagramTokenLifecycleService
        )
        lifecycle.client = MagicMock()
        with (
            patch("apps.integrations.instagram.lifecycle.cache.add", return_value=True),
            patch("apps.integrations.instagram.lifecycle.cache.delete"),
        ):
            result = lifecycle.refresh_credential(credential.pk)
        self.assertEqual(result["status"], "revoked")
        lifecycle.client.refresh_long_lived_token.assert_not_called()

        fresh_expiry = timezone.now() + timedelta(days=60)
        InstagramOAuthService.persist_authorized_profile(
            organization=self.organization,
            result=InstagramOAuthResult(
                instagram_user_id=account.platform_account_id,
                username=account.username,
                account_name=account.account_name,
                profile_image="",
                access_token="fresh-instagram-token-fixture",
                token_expires_at=fresh_expiry,
            ),
        )

        credential.refresh_from_db()
        account.refresh_from_db()
        self.assertEqual(credential.status, InstagramCredentialStatus.ACTIVE)
        self.assertEqual(
            decrypt_instagram_token(credential.encrypted_access_token),
            "fresh-instagram-token-fixture",
        )
        self.assertEqual(account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(account.is_valid)

    def test_disconnect_api_response_excludes_credential_fields(self):
        account = self.make_account(SocialPlatform.INSTAGRAM, "api")
        InstagramAccountCredential.objects.create(
            social_account=account,
            encrypted_access_token=encrypt_instagram_token("api-token-fixture"),
            status=InstagramCredentialStatus.ACTIVE,
        )
        client = APIClient()
        client.force_authenticate(self.owner)
        url = reverse(
            "organization-social-account-disconnect",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": account.id,
            },
        )

        response = client.post(url, {}, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        response_data = response.data["data"]
        self.assertNotIn("access_token", response_data)
        self.assertNotIn("encrypted_access_token", response_data)
        self.assertNotIn("api-token-fixture", str(response_data))


class FacebookDisconnectIsolationUnitTests(SimpleTestCase):
    def test_disconnecting_one_page_leaves_sibling_page_and_shared_user_credential_unchanged(self):
        organization = object()
        connection = SimpleNamespace(pk="meta-connection-1", organization=organization)
        target = SimpleNamespace(
            pk="facebook-target",
            platform=SocialPlatform.FACEBOOK,
            is_deleted=False,
            connection=connection,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
            save=MagicMock(),
        )
        sibling = SimpleNamespace(
            pk="facebook-sibling",
            platform=SocialPlatform.FACEBOOK,
            connection=connection,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        target_credential = SimpleNamespace(
            access_token="synthetic-target-page-ciphertext",
            status=MetaCredentialStatus.ACTIVE,
            save=MagicMock(),
        )
        sibling_credential = SimpleNamespace(
            access_token="synthetic-sibling-page-ciphertext",
            status=MetaCredentialStatus.ACTIVE,
        )
        user_credential = SimpleNamespace(
            access_token="synthetic-shared-user-ciphertext",
            status=MetaCredentialStatus.ACTIVE,
        )
        queryset = MagicMock()
        queryset.filter.return_value.first.return_value = target
        credential_queryset = MagicMock()
        credential_queryset.filter.return_value.first.return_value = target_credential

        with (
            patch("apps.social_accounts.lifecycle.SocialAccount.objects.select_for_update", return_value=queryset),
            patch("apps.social_accounts.lifecycle.transaction.atomic", return_value=nullcontext()),
            patch("django.db.transaction.Atomic.__enter__", return_value=None),
            patch("django.db.transaction.Atomic.__exit__", return_value=False),
            patch(
                "apps.integrations.meta.services.MetaAccountCredential.objects.select_for_update",
                return_value=credential_queryset,
            ),
        ):
            result = disconnect_social_account_with_credentials.__wrapped__(social_account=target)

        self.assertIs(result, target)
        self.assertEqual(target.status, SocialAccountStatus.DISCONNECTED)
        self.assertFalse(target.is_valid)
        self.assertEqual(target_credential.access_token, "")
        self.assertEqual(target_credential.status, MetaCredentialStatus.REVOKED)
        self.assertEqual(sibling.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(sibling.is_valid)
        self.assertEqual(sibling_credential.access_token, "synthetic-sibling-page-ciphertext")
        self.assertEqual(sibling_credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(user_credential.access_token, "synthetic-shared-user-ciphertext")
        self.assertEqual(user_credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(target.connection, sibling.connection)
        credential_queryset.filter.assert_called_once_with(
            social_account=target,
            credential_type=MetaCredentialType.PAGE,
            is_deleted=False,
        )
