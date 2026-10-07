from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from django.test import SimpleTestCase, TestCase
from django.test import override_settings

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.posts.publishing.meta import MetaPublisher
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .client import InstagramAPIClient
from .exceptions import InstagramAPIError
from .services import InstagramOAuthService


class InstagramAPIClientObservabilityTests(SimpleTestCase):
    def make_client(self):
        client = InstagramAPIClient.__new__(InstagramAPIClient)
        client.timeout = 10
        return client

    @patch("apps.integrations.instagram.client.requests.get")
    def test_graph_get_passes_through_limiter(self, get):
        get.return_value.status_code = 200
        get.return_value.ok = True
        get.return_value.headers = {}
        get.return_value.json.return_value = {"status_code": "FINISHED"}
        client = self.make_client()

        with patch.object(client, "_pace_graph_request") as pace:
            result = client.graph_get(
                "container-1",
                access_token="token",
                params={"fields": "status_code"},
            )

        pace.assert_called_once_with()
        self.assertEqual(result, {"status_code": "FINISHED"})
        get.assert_called_once_with(
            "https://graph.instagram.com/v26.0/container-1",
            params={"fields": "status_code", "access_token": "token"},
            timeout=10,
        )

    @patch("apps.integrations.instagram.client.requests.post")
    def test_graph_post_passes_through_limiter(self, post):
        post.return_value.status_code = 200
        post.return_value.ok = True
        post.return_value.headers = {}
        post.return_value.json.return_value = {"id": "media-1"}
        client = self.make_client()

        with patch.object(client, "_pace_graph_request") as pace:
            result = client.graph_post(
                "account-1/media_publish",
                access_token="token",
                data={"creation_id": "container-1"},
            )

        pace.assert_called_once_with()
        self.assertEqual(result, {"id": "media-1"})
        post.assert_called_once_with(
            "https://graph.instagram.com/v26.0/account-1/media_publish",
            data={"creation_id": "container-1", "access_token": "token"},
            timeout=10,
        )

    @override_settings(INSTAGRAM_GRAPH_REQUEST_INTERVAL_SECONDS=0.25)
    @patch("apps.integrations.instagram.client.time.sleep")
    @patch("apps.integrations.instagram.client.cache._cache")
    def test_client_instances_share_atomic_limiter_state_and_spacing(
        self,
        redis_cache,
        sleep,
    ):
        redis_client = MagicMock()
        redis_client.eval.side_effect = [0, 250]
        redis_cache.get_client.return_value = redis_client

        self.make_client()._pace_graph_request()
        self.make_client()._pace_graph_request()

        self.assertEqual(redis_client.eval.call_count, 2)
        first_call, second_call = redis_client.eval.call_args_list
        self.assertEqual(first_call.args[2], second_call.args[2])
        self.assertIn("redis.call('TIME')", first_call.args[0])
        self.assertEqual(first_call.args[3], 250)
        self.assertEqual(second_call.args[3], 250)
        sleep.assert_called_once_with(0.25)

    @patch("apps.integrations.instagram.client.cache._cache")
    def test_limiter_fails_closed_when_redis_coordination_is_unavailable(
        self,
        redis_cache,
    ):
        redis_cache.get_client.side_effect = OSError("Redis unavailable")

        with self.assertRaisesMessage(
            InstagramAPIError,
            "Instagram Graph request pacing is unavailable.",
        ):
            self.make_client()._pace_graph_request()

    def test_response_usage_diagnostics_are_allowlisted_and_ephemeral(self):
        client = InstagramAPIClient.__new__(InstagramAPIClient)
        response = MagicMock()
        response.status_code = 403
        response.ok = False
        response.headers = {
            "X-App-Usage": (
                '{"call_count": 81, "total_cputime": 14, '
                '"total_time": 7, "access_token": "must-not-appear"}'
            ),
            "Authorization": "Bearer must-not-appear",
            "X-Unrelated": "must-not-appear",
        }
        response.json.return_value = {
            "error": {"access_token": "must-not-appear"},
        }

        with self.assertRaises(InstagramAPIError) as raised:
            client._handle_response(response, operation="Instagram content publishing")

        expected = {
            "x-app-usage": {
                "call_count": 81,
                "total_cputime": 14,
                "total_time": 7,
            },
        }
        self.assertEqual(client.last_response_usage_diagnostics, expected)
        self.assertEqual(raised.exception.usage_diagnostics, expected)
        self.assertNotIn("must-not-appear", repr(expected))

    def test_missing_or_invalid_usage_header_produces_no_diagnostics(self):
        client = InstagramAPIClient.__new__(InstagramAPIClient)
        response = MagicMock()
        response.status_code = 200
        response.ok = True
        response.headers = {"X-App-Usage": "not-json"}
        response.json.return_value = {"id": "container-1"}

        self.assertEqual(
            client._handle_response(response, operation="Instagram content publishing"),
            {"id": "container-1"},
        )
        self.assertEqual(client.last_response_usage_diagnostics, {})

    def test_media_publish_failure_log_contains_safe_diagnostics_only(self):
        error = InstagramAPIError(
            "Instagram API request failed during content publishing.",
            status_code=403,
            error_payload={
                "error": {
                    "message": "Application request limit reached",
                    "code": 4,
                    "error_subcode": 2207051,
                    "type": "OAuthException",
                    "fbtrace_id": "safe-trace-id",
                    "error_user_title": "Private title",
                    "error_user_msg": "Private detail",
                    "access_token": "must-not-appear",
                    "client_secret": "must-not-appear",
                    "authorization": "Bearer must-not-appear",
                    "cookie": "must-not-appear",
                }
            },
            usage_diagnostics={
                "x-app-usage": {
                    "call_count": 81,
                    "total_cputime": 14,
                    "total_time": 7,
                    "estimated_time_to_regain_access": 3,
                }
            },
        )

        with self.assertLogs("apps.posts.publishing.meta", level="WARNING") as logs:
            MetaPublisher._log_instagram_media_publish_failure(
                post_platform=SimpleNamespace(
                    id="target-id",
                    provider_container_id="container-id",
                ),
                exc=error,
            )

        output = "\n".join(logs.output)
        for diagnostic in (
            "http_status=403",
            "message=Application request limit reached",
            "code=4",
            "error_subcode=2207051",
            "type=OAuthException",
            "fbtrace_id=safe-trace-id",
            "usage_diagnostics=",
            "call_count",
            "total_cputime",
            "total_time",
            "estimated_time_to_regain_access",
        ):
            self.assertIn(diagnostic, output)
        for secret in (
            "must-not-appear",
            "Private title",
            "Private detail",
        ):
            self.assertNotIn(secret, output)


class InstagramOAuthProfileImageLengthTests(TestCase):
    @override_settings(META_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode())
    @patch.object(InstagramOAuthService, "__init__", return_value=None)
    def test_callback_stores_profile_picture_url_longer_than_200_characters(
        self,
        _service_init,
    ):
        user = User.objects.create_user(
            email="instagram-length@example.com",
            password="test-password",
            first_name="Instagram",
        )
        organization = Organization.objects.create(
            organization_id="ORG-IG-LENGTH",
            name="Instagram URL Length Test",
            slug="instagram-url-length-test",
            industry="Retail",
            created_by=user,
        )
        profile_picture_url = "https://cdn.instagram.example/" + "a" * 240
        service = InstagramOAuthService()
        service.client = MagicMock()
        service.client.exchange_code.return_value = {"access_token": "short-token"}
        service.client.exchange_long_lived_token.return_value = {
            "access_token": "long-lived-token",
            "expires_in": 3600,
        }
        service.client.get_profile.return_value = {
            "id": "instagram-user-123",
            "username": "test_account",
            "name": "Test Account",
            "profile_picture_url": profile_picture_url,
        }

        social_account = service.handle_callback(
            code="authorization-code",
            organization=organization,
            user=user,
        )

        self.assertEqual(len(profile_picture_url), 270)
        self.assertGreater(len(profile_picture_url), 200)
        self.assertEqual(social_account.profile_image, profile_picture_url)
        self.assertEqual(social_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(social_account.is_valid)
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=organization,
                platform=SocialPlatform.INSTAGRAM,
                platform_account_id="instagram-user-123",
            ).count(),
            1,
        )
