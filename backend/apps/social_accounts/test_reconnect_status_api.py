from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.integrations.meta.models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaProviderExpiryState,
)
from apps.organizations.models import Organization
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialConnectionStatus,
    SocialPlatform,
)

from .serializers import SocialAccountReadSerializer


class FacebookReconnectStatusSerializationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="reconnect-status-owner@example.test",
            first_name="Reconnect Status",
            password="synthetic-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-RECONNECT-STATUS-TEST",
            name="Reconnect Status Test",
            slug="reconnect-status-test",
            industry="Retail",
            created_by=self.owner,
        )

    def make_connection(self, provider_user_id, *, user_status):
        connection = SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=provider_user_id,
            status=SocialConnectionStatus.ACTIVE,
        )
        credential_fields = {}
        if user_status == MetaCredentialStatus.ACTIVE:
            now = timezone.now()
            credential_fields = {
                "provider_expiry_state": MetaProviderExpiryState.FINITE,
                "provider_is_valid": True,
                "provider_expires_at": now + timedelta(days=30),
                "data_access_expires_at": now + timedelta(days=60),
            }
        MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token="SYNTHETIC_ENCRYPTED_USER_PLACEHOLDER",
            status=user_status,
            **credential_fields,
        )
        return connection

    def make_page(
        self,
        page_id,
        connection,
        *,
        page_credential_status=MetaCredentialStatus.ACTIVE,
        account_status=SocialAccountStatus.CONNECTED,
        is_valid=True,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            connection=connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=page_id,
            status=account_status,
            is_valid=is_valid,
        )
        MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token="SYNTHETIC_ENCRYPTED_PAGE_PLACEHOLDER",
            status=page_credential_status,
        )
        return account

    @staticmethod
    def serialize(account):
        return SocialAccountReadSerializer(account).data

    def test_invalid_parent_and_active_page_are_reported_independently(self):
        connection = self.make_connection(
            "parent-invalid-page-active",
            user_status=MetaCredentialStatus.INVALID,
        )
        account = self.make_page("page-active", connection)

        data = self.serialize(account)

        self.assertEqual(data["parent_user_credential_status"], "invalid")
        self.assertTrue(data["parent_needs_reconnect"])
        self.assertFalse(data["page_needs_reconnect"])
        self.assertTrue(data["needs_reconnect"])
        self.assertEqual(data["credential_status"], "active")
        self.assertTrue(data["connected"])
        self.assertTrue(data["valid"])
        self.assertEqual(data["parent_connection_id"], str(connection.id))

    def test_active_parent_and_invalid_page_only_require_page_reconnect(self):
        connection = self.make_connection(
            "parent-active-page-invalid",
            user_status=MetaCredentialStatus.ACTIVE,
        )
        account = self.make_page(
            "page-invalid",
            connection,
            page_credential_status=MetaCredentialStatus.INVALID,
        )

        data = self.serialize(account)

        self.assertEqual(data["parent_user_credential_status"], "active")
        self.assertFalse(data["parent_needs_reconnect"])
        self.assertTrue(data["page_needs_reconnect"])
        self.assertTrue(data["needs_reconnect"])
        self.assertEqual(data["credential_status"], "invalid")

    def test_active_parent_and_active_page_need_no_reconnect(self):
        connection = self.make_connection(
            "parent-active-page-active",
            user_status=MetaCredentialStatus.ACTIVE,
        )
        account = self.make_page("page-all-active", connection)

        data = self.serialize(account)

        self.assertEqual(data["parent_user_credential_status"], "active")
        self.assertFalse(data["parent_needs_reconnect"])
        self.assertFalse(data["page_needs_reconnect"])
        self.assertFalse(data["needs_reconnect"])

    def test_both_invalid_states_are_reported_without_conflating_them(self):
        connection = self.make_connection(
            "parent-invalid-page-invalid",
            user_status=MetaCredentialStatus.INVALID,
        )
        account = self.make_page(
            "page-and-parent-invalid",
            connection,
            page_credential_status=MetaCredentialStatus.INVALID,
            account_status=SocialAccountStatus.ERROR,
            is_valid=False,
        )

        data = self.serialize(account)

        self.assertEqual(data["parent_user_credential_status"], "invalid")
        self.assertTrue(data["parent_needs_reconnect"])
        self.assertTrue(data["page_needs_reconnect"])
        self.assertTrue(data["needs_reconnect"])

    def test_shared_invalid_parent_has_same_connection_identity_for_each_page(self):
        connection = self.make_connection(
            "one-invalid-parent-two-pages",
            user_status=MetaCredentialStatus.INVALID,
        )
        first = self.make_page("shared-page-one", connection)
        second = self.make_page("shared-page-two", connection)

        first_data = self.serialize(first)
        second_data = self.serialize(second)

        self.assertTrue(first_data["parent_needs_reconnect"])
        self.assertTrue(second_data["parent_needs_reconnect"])
        self.assertEqual(first_data["parent_connection_id"], second_data["parent_connection_id"])
        self.assertFalse(first_data["page_needs_reconnect"])
        self.assertFalse(second_data["page_needs_reconnect"])

    def test_page_reconnect_is_isolated_across_separate_connections(self):
        invalid_connection = self.make_connection(
            "separate-connection-invalid-page",
            user_status=MetaCredentialStatus.ACTIVE,
        )
        valid_connection = self.make_connection(
            "separate-connection-valid-page",
            user_status=MetaCredentialStatus.ACTIVE,
        )
        invalid_page = self.make_page(
            "separate-invalid-page",
            invalid_connection,
            page_credential_status=MetaCredentialStatus.INVALID,
        )
        valid_page = self.make_page("separate-valid-page", valid_connection)

        invalid_data = self.serialize(invalid_page)
        valid_data = self.serialize(valid_page)

        self.assertTrue(invalid_data["page_needs_reconnect"])
        self.assertFalse(invalid_data["parent_needs_reconnect"])
        self.assertFalse(valid_data["page_needs_reconnect"])
        self.assertFalse(valid_data["parent_needs_reconnect"])
        self.assertNotEqual(
            invalid_data["parent_connection_id"],
            valid_data["parent_connection_id"],
        )
