from datetime import date

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.integrations.instagram.models import InstagramAccountCredential, InstagramCredentialStatus
from apps.insights.models import InsightsAccountSnapshot, InsightsMediaSnapshot
from apps.organizations.models import Organization
from apps.social_accounts.lifecycle import disconnect_social_account_with_credentials
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform
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
        self.assertTrue(InsightsAccountSnapshot.objects.filter(pk=self.snapshot.pk).exists())
        self.assertTrue(InsightsMediaSnapshot.objects.filter(pk=self.media_snapshot.pk).exists())
        self.assertEqual(Organization.objects.count(), 2)
        self.assertEqual(
            SocialAccount.objects.filter(organization=self.keep_organization, is_deleted=False).count(),
            1,
        )
