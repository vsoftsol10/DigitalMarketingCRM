from datetime import date
from unittest.mock import call, patch

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
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

from .models import (
    InsightsSyncState,
    InsightsSyncStatus,
    InsightsSyncWork,
    InsightsSyncWorkStage,
    InsightsSyncWorkStatus,
)
from .providers import fetch_provider_insights
from .sync_service import claim_stage_work, process_content_sync_batch


class FacebookPageTokenInsightsRegressionTests(TestCase):
    since = date(2026, 9, 1)
    until = date(2026, 9, 30)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="fb-insights-page-token@example.test",
            first_name="Insights Regression",
            password="synthetic-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-FB-INSIGHTS-PAGE-TOKEN",
            name="Facebook Insights Page Token",
            slug="facebook-insights-page-token",
            industry="Retail",
            created_by=self.owner,
        )

    def make_page(self, *, page_id, provider_user_id, page_status=MetaCredentialStatus.ACTIVE):
        connection = SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=provider_user_id,
            status=SocialConnectionStatus.ACTIVE,
        )
        account = SocialAccount.objects.create(
            organization=self.organization,
            connection=connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=page_id,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        user_credential = MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token="SYNTHETIC_ENCRYPTED_USER_PLACEHOLDER",
            status=MetaCredentialStatus.INVALID,
        )
        page_credential = MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token="SYNTHETIC_ENCRYPTED_PAGE_PLACEHOLDER",
            status=page_status,
        )
        return connection, account, user_credential, page_credential

    @patch("apps.insights.providers.MetaAPIClient")
    @patch("apps.integrations.meta.credentials.decrypt_token", return_value="SYNTHETIC_PAGE_TOKEN")
    def test_account_insights_and_page_posts_use_active_page_token_with_invalid_parent(
        self, _decrypt, client_class,
    ):
        _connection, account, parent_credential, page_credential = self.make_page(
            page_id="page-account-insights",
            provider_user_id="invalid-parent-account-insights",
        )
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-account-insights", "name": "Page", "followers_count": 17},
            {"data": []},
            {"data": [], "paging": {}},
        ]

        result = fetch_provider_insights(
            account=account,
            since=self.since,
            until=self.until,
        )

        self.assertEqual(parent_credential.status, MetaCredentialStatus.INVALID)
        self.assertEqual(page_credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(result["provider_metadata"]["availability"], "available")
        self.assertEqual(client.get.call_count, 3)
        self.assertEqual(
            client.get.call_args_list,
            [
                call(
                    "/page-account-insights",
                    access_token="SYNTHETIC_PAGE_TOKEN",
                    params={"fields": "id,name,username,followers_count,picture"},
                ),
                call(
                    "/page-account-insights/insights",
                    access_token="SYNTHETIC_PAGE_TOKEN",
                    params={
                        "metric": "page_follows,page_post_engagements,page_media_view,page_total_media_view_unique",
                        "period": "day",
                        "since": self.since.isoformat(),
                        "until": self.until.isoformat(),
                    },
                ),
                call(
                    "/page-account-insights/posts",
                    access_token="SYNTHETIC_PAGE_TOKEN",
                    params={
                        "fields": (
                            "id,message,created_time,permalink_url,shares,"
                            "comments.limit(0).summary(true),reactions.limit(0).summary(true)"
                        ),
                        "limit": 25,
                    },
                ),
            ],
        )

    @patch("apps.insights.providers.MetaAPIClient")
    @patch("apps.integrations.meta.credentials.decrypt_token", return_value="SYNTHETIC_PAGE_TOKEN")
    def test_invalid_page_is_rejected_for_insights_but_valid_page_on_sibling_connection_works(
        self, _decrypt, client_class,
    ):
        _invalid_connection, invalid_account, _invalid_parent, invalid_page = self.make_page(
            page_id="invalid-page-insights",
            provider_user_id="invalid-page-parent",
            page_status=MetaCredentialStatus.INVALID,
        )
        _valid_connection, valid_account, valid_parent, valid_page = self.make_page(
            page_id="valid-sibling-insights",
            provider_user_id="valid-sibling-parent",
        )
        client_class.return_value.get.side_effect = [
            {"id": "valid-sibling-insights", "name": "Sibling", "followers_count": 4},
            {"data": []},
            {"data": [], "paging": {}},
        ]

        invalid_result = fetch_provider_insights(
            account=invalid_account,
            since=self.since,
            until=self.until,
        )
        self.assertEqual(invalid_result["provider_metadata"]["reason"], "invalid_credential")
        client_class.return_value.get.assert_not_called()

        invalid_state = InsightsSyncState.objects.create(
            social_account=invalid_account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.SYNCING,
            content_status=InsightsSyncStatus.QUEUED,
        )
        invalid_work = InsightsSyncWork.objects.create(
            sync_state=invalid_state,
            stage=InsightsSyncWorkStage.CONTENT,
            generation=1,
            status=InsightsSyncWorkStatus.DISPATCHED,
            next_attempt_at=timezone.now(),
        )
        invalid_claim = claim_stage_work(
            work_id=invalid_work.id,
            generation=1,
        )
        with patch("apps.insights.sync_service.MetaAPIClient") as sync_client_class:
            sync_result = process_content_sync_batch(claim=invalid_claim)
        self.assertEqual(sync_result["status"], "failed")
        self.assertEqual(sync_result["error_code"], "invalid_credential")
        sync_client_class.assert_not_called()

        valid_result = fetch_provider_insights(
            account=valid_account,
            since=self.since,
            until=self.until,
        )
        self.assertEqual(valid_result["provider_metadata"]["availability"], "available")
        self.assertEqual(client_class.return_value.get.call_count, 3)
        self.assertTrue(all(
            call_item.kwargs["access_token"] == "SYNTHETIC_PAGE_TOKEN"
            for call_item in client_class.return_value.get.call_args_list
        ))
        self.assertEqual(invalid_page.status, MetaCredentialStatus.INVALID)
        self.assertEqual(valid_page.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(valid_parent.status, MetaCredentialStatus.INVALID)
        self.assertEqual(valid_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(valid_account.is_valid)

    @patch("apps.insights.sync_service.MetaAPIClient")
    @patch("apps.integrations.meta.credentials.decrypt_token", return_value="SYNTHETIC_PAGE_TOKEN")
    def test_page_posts_and_post_insights_sync_use_page_token_with_invalid_parent(
        self, _decrypt, client_class,
    ):
        _connection, account, parent_credential, page_credential = self.make_page(
            page_id="page-post-insights",
            provider_user_id="invalid-parent-post-insights",
        )
        state = InsightsSyncState.objects.create(
            social_account=account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.SYNCING,
            content_status=InsightsSyncStatus.QUEUED,
        )
        work = InsightsSyncWork.objects.create(
            sync_state=state,
            stage=InsightsSyncWorkStage.CONTENT,
            generation=1,
            status=InsightsSyncWorkStatus.DISPATCHED,
            next_attempt_at=timezone.now(),
        )
        client = client_class.return_value
        client.get.side_effect = [
            {
                "data": [{
                    "id": "page-post-insights_123",
                    "message": "Synthetic post",
                    "created_time": "2026-09-15T13:24:00+0000",
                    "permalink_url": "https://facebook.example.test/synthetic-post",
                    "shares": {"count": 1},
                    "comments": {"summary": {"total_count": 2}},
                    "reactions": {"summary": {"total_count": 3}},
                }],
                "paging": {},
            },
            {"data": [
                {"name": "post_total_media_view_unique", "period": "lifetime", "values": [{"value": 8}]},
                {"name": "post_media_view", "period": "lifetime", "values": [{"value": 13}]},
                {"name": "post_clicks", "period": "lifetime", "values": [{"value": 2}]},
            ]},
        ]
        claim = claim_stage_work(work_id=work.id, generation=1)
        result = process_content_sync_batch(claim=claim)

        self.assertEqual(result["content_status"], InsightsSyncStatus.COMPLETE)
        self.assertEqual(parent_credential.status, MetaCredentialStatus.INVALID)
        self.assertEqual(page_credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(client.get.call_args_list[0].args[0], "/page-post-insights/posts")
        self.assertEqual(client.get.call_args_list[1].args[0], "/page-post-insights_123/insights")
        self.assertTrue(all(
            call_item.kwargs["access_token"] == "SYNTHETIC_PAGE_TOKEN"
            for call_item in client.get.call_args_list
        ))
