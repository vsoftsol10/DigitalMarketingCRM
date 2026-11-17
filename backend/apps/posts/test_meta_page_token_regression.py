from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import User
from apps.integrations.meta.exceptions import MetaIntegrationError
from apps.integrations.meta.models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
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

from .models import Post, PostPlatform, PostPublishType, PostStatus
from .publishing.meta import MetaPublisher
from .services import validate_target_accounts


class FacebookPageTokenPublishingRegressionTests(TestCase):
    """Publishing remains scoped to each Page token, independent of USER health."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="fb-page-token-regression@example.test",
            first_name="Regression",
            password="synthetic-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-FB-PAGE-TOKEN-REGRESSION",
            name="Facebook Page Token Regression",
            slug="facebook-page-token-regression",
            industry="Retail",
            created_by=self.user,
        )
        self.connection = self.make_connection("provider-user-one")
        self.account = self.make_account(
            "page-one",
            "Page One",
            self.connection,
        )
        self.user_credential = self.make_user_credential(self.connection)
        self.page_credential = self.make_page_credential(
            self.account,
            status=MetaCredentialStatus.ACTIVE,
        )
        self.post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="Synthetic regression post",
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )

    def make_connection(self, provider_user_id):
        return SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=provider_user_id,
            status=SocialConnectionStatus.ACTIVE,
        )

    def make_account(self, page_id, name, connection):
        return SocialAccount.objects.create(
            organization=self.organization,
            connection=connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=name,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )

    @staticmethod
    def make_user_credential(connection, *, status=MetaCredentialStatus.INVALID):
        return MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token="SYNTHETIC_ENCRYPTED_USER_PLACEHOLDER",
            status=status,
        )

    @staticmethod
    def make_page_credential(account, *, status):
        return MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token="SYNTHETIC_ENCRYPTED_PAGE_PLACEHOLDER",
            status=status,
        )

    def make_target(self, account):
        return PostPlatform.objects.create(
            post=self.post,
            platform=SocialPlatform.FACEBOOK,
            social_account=account,
            content_type="POST",
            status=PostStatus.PUBLISHING,
        )

    @patch("apps.posts.publishing.meta.MetaAPIClient")
    @patch("apps.integrations.meta.credentials.decrypt_token", return_value="SYNTHETIC_PAGE_TOKEN")
    def test_invalid_parent_user_does_not_block_page_publish_or_replace_page_token(
        self, _decrypt, client_class,
    ):
        target = self.make_target(self.account)
        client_class.return_value.post.return_value = {"id": "synthetic-published-post"}

        self.assertEqual(self.user_credential.status, MetaCredentialStatus.INVALID)
        self.assertEqual(self.page_credential.status, MetaCredentialStatus.ACTIVE)

        validate_target_accounts(
            organization=self.organization,
            targets=[{"social_account": str(self.account.id)}],
        )
        with patch.object(MetaPublisher, "_media", return_value=[]):
            result = MetaPublisher().publish_facebook(post_platform=target)

        self.assertEqual(result["external_post_id"], "synthetic-published-post")
        client_class.return_value.post.assert_called_once()
        self.assertEqual(
            client_class.return_value.post.call_args.args[0],
            "/page-one/feed",
        )
        self.assertEqual(
            client_class.return_value.post.call_args.kwargs["access_token"],
            "SYNTHETIC_PAGE_TOKEN",
        )

    @patch("apps.posts.publishing.meta.MetaAPIClient")
    @patch("apps.integrations.meta.credentials.decrypt_token", return_value="SYNTHETIC_PAGE_TOKEN")
    def test_invalid_page_is_rejected_and_does_not_affect_valid_sibling_on_other_connection(
        self, _decrypt, client_class,
    ):
        invalid_connection = self.make_connection("provider-user-invalid-page")
        invalid_account = self.make_account(
            "invalid-page",
            "Invalid Page",
            invalid_connection,
        )
        self.make_user_credential(invalid_connection)
        self.make_page_credential(
            invalid_account,
            status=MetaCredentialStatus.INVALID,
        )

        sibling_connection = self.make_connection("provider-user-valid-page")
        sibling_account = self.make_account(
            "valid-sibling-page",
            "Valid Sibling Page",
            sibling_connection,
        )
        sibling_user = self.make_user_credential(sibling_connection)
        sibling_page = self.make_page_credential(
            sibling_account,
            status=MetaCredentialStatus.ACTIVE,
        )
        sibling_target = self.make_target(sibling_account)
        client_class.return_value.post.return_value = {"id": "sibling-published-post"}

        with self.assertRaises(MetaIntegrationError):
            validate_target_accounts(
                organization=self.organization,
                targets=[{"social_account": str(invalid_account.id)}],
            )
        with self.assertRaises(MetaIntegrationError):
            MetaPublisher().publish_facebook(
                post_platform=self.make_target(invalid_account),
            )
        with patch.object(MetaPublisher, "_media", return_value=[]):
            self.assertEqual(
                MetaPublisher().publish_facebook(post_platform=sibling_target)["external_post_id"],
                "sibling-published-post",
            )
        self.assertEqual(
            client_class.return_value.post.call_args.kwargs["access_token"],
            "SYNTHETIC_PAGE_TOKEN",
        )

        sibling_user.refresh_from_db()
        sibling_page.refresh_from_db()
        sibling_account.refresh_from_db()
        self.assertEqual(sibling_user.status, MetaCredentialStatus.INVALID)
        self.assertEqual(sibling_page.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(sibling_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(sibling_account.is_valid)
