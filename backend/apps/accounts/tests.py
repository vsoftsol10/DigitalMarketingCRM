from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.throttles import RedisRateThrottle

from .views import LoginAPIView, RateLimitedTokenRefreshView


class InMemoryAtomicRedis:
    """Small deterministic stand-in for the limiter's atomic EVAL call."""

    def __init__(self):
        self.now_ms = 0
        self.counters = {}
        self.keys_seen = []

    def eval(self, _script, key_count, *keys_and_windows):
        keys = keys_and_windows[:key_count]
        windows_ms = keys_and_windows[key_count:]
        self.keys_seen.extend(keys)
        result = []
        for key, window_ms in zip(keys, windows_ms):
            counter = self.counters.get(key)
            if counter and counter[1] <= self.now_ms:
                counter = None
            if counter is None:
                counter = [0, self.now_ms + window_ms]
            counter[0] += 1
            self.counters[key] = counter
            result.extend([counter[0], counter[1] - self.now_ms])
        return result


@override_settings(
    DMC_RATE_LIMITS={"login": ((5, 60), (30, 3600))},
    DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="closed",
)
class LoginRateLimitTests(SimpleTestCase):
    databases = set()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.redis = InMemoryAtomicRedis()
        self.redis_patcher = patch.object(
            RedisRateThrottle,
            "_redis_client",
            return_value=self.redis,
        )
        self.redis_patcher.start()
        self.addCleanup(self.redis_patcher.stop)

        self.login_patcher = patch("apps.accounts.views.login_user")
        self.login_user = self.login_patcher.start()
        self.addCleanup(self.login_patcher.stop)
        self.login_user.return_value = Mock(pk="user-id", email="member@example.com")

        refresh = Mock()
        refresh.access_token = "access-token"
        refresh.__str__ = Mock(return_value="refresh-token")
        self.refresh_patcher = patch(
            "apps.accounts.views.RefreshToken.for_user",
            return_value=refresh,
        )
        self.refresh_patcher.start()
        self.addCleanup(self.refresh_patcher.stop)

        self.serializer_patcher = patch("apps.accounts.views.UserSerializer")
        serializer = self.serializer_patcher.start()
        serializer.return_value.data = {"id": "user-id", "email": "member@example.com"}
        self.addCleanup(self.serializer_patcher.stop)

        self.login_view = LoginAPIView.as_view()

    def post_login(
        self,
        email,
        password="synthetic-password",
        remote_addr="198.51.100.20",
        forwarded_for=None,
    ):
        headers = {}
        if forwarded_for is not None:
            headers["HTTP_X_FORWARDED_FOR"] = forwarded_for
        request = self.factory.post(
            "/api/auth/login/",
            {"email": email, "password": password},
            format="json",
            REMOTE_ADDR=remote_addr,
            **headers,
        )
        return self.login_view(request)

    def test_under_limit_login_preserves_existing_success_response(self):
        response = self.post_login("Member@example.com", password="synthetic-password")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["message"], "Login successful.")
        self.assertEqual(
            response.data["data"],
            {
                "access": "access-token",
                "refresh": "refresh-token",
                "user": {"id": "user-id", "email": "member@example.com"},
            },
        )
        self.login_user.assert_called_once_with(
            email="Member@example.com",
            password="synthetic-password",
        )

    def test_login_failure_preserves_existing_authentication_error_envelope(self):
        from rest_framework.exceptions import AuthenticationFailed

        self.login_user.side_effect = AuthenticationFailed("Invalid email or password.")

        response = self.post_login("unknown@example.com")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid email or password.")
        self.assertIn("errors", response.data)

    def test_minute_limit_is_per_source_ip_and_normalized_account(self):
        responses = [
            self.post_login("Member@example.com" if index % 2 else " member@EXAMPLE.com ")
            for index in range(6)
        ]

        self.assertEqual([response.status_code for response in responses[:5]], [200] * 5)
        self.assertEqual(responses[5].status_code, 429)
        self.assertIn("Retry-After", responses[5])
        self.assertLessEqual(int(responses[5]["Retry-After"]), 60)

    def test_hourly_limit_is_per_source_ip_across_accounts(self):
        responses = [
            self.post_login(f"person-{index}@example.com")
            for index in range(31)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:30]))
        self.assertEqual(responses[30].status_code, 429)
        self.assertGreater(int(responses[30]["Retry-After"]), 60)

    def test_different_identifiers_have_distinct_minute_buckets(self):
        responses = [
            self.post_login("first@example.com")
            for _ in range(6)
        ]
        other_account_response = self.post_login("second@example.com")

        self.assertEqual(responses[-1].status_code, 429)
        self.assertEqual(other_account_response.status_code, 200)

    def test_forwarded_for_is_not_trusted_without_project_proxy_configuration(self):
        responses = [
            self.post_login(
                "member@example.com",
                forwarded_for=f"203.0.113.{index}",
            )
            for index in range(6)
        ]

        self.assertEqual(responses[-1].status_code, 429)

    def test_redis_keys_never_contain_raw_account_identifier_or_password(self):
        email = "private-person@example.com"
        password = "private-synthetic-password"

        self.post_login(email, password=password)

        self.assertTrue(self.redis.keys_seen)
        for key in self.redis.keys_seen:
            self.assertTrue(key.startswith("dmc:ratelimit:v1:login:"))
            self.assertNotIn(email, key)
            self.assertNotIn(email.casefold(), key)
            self.assertNotIn(password, key)

    def test_throttle_response_is_generic_across_account_identifiers(self):
        responses = {}
        for email in ("unknown-a@example.com", "unknown-b@example.com"):
            for _ in range(6):
                response = self.post_login(email)
            responses[email] = response

        self.assertEqual(responses["unknown-a@example.com"].status_code, 429)
        self.assertEqual(responses["unknown-b@example.com"].status_code, 429)
        self.assertEqual(
            responses["unknown-a@example.com"].data,
            responses["unknown-b@example.com"].data,
        )


class FakeRefreshSerializer:
    def __init__(self, data, context=None):
        self.initial_data = data
        self.context = context or {}
        self.validated_data = {
            "access": "rotated-access-token",
            "refresh": "rotated-refresh-token",
        }
        self.data = self.validated_data

    def is_valid(self, raise_exception=False):
        return True


@override_settings(
    DMC_RATE_LIMITS={"token_refresh": ((10, 60), (30, 3600))},
    DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="closed",
)
class RefreshRateLimitTests(SimpleTestCase):
    databases = set()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.redis = InMemoryAtomicRedis()
        self.redis_patcher = patch.object(
            RedisRateThrottle,
            "_redis_client",
            return_value=self.redis,
        )
        self.redis_patcher.start()
        self.addCleanup(self.redis_patcher.stop)
        self.refresh_view = RateLimitedTokenRefreshView.as_view()

    def post_refresh(
        self,
        refresh_token="synthetic-refresh-token",
        remote_addr="198.51.100.30",
    ):
        request = self.factory.post(
            "/api/auth/refresh/",
            {"refresh": refresh_token},
            format="json",
            REMOTE_ADDR=remote_addr,
        )
        with patch.object(
            RateLimitedTokenRefreshView,
            "serializer_class",
            FakeRefreshSerializer,
        ):
            return self.refresh_view(request)

    def test_refresh_succeeds_under_limit_with_existing_response_shape(self):
        response = self.post_refresh()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "access": "rotated-access-token",
                "refresh": "rotated-refresh-token",
            },
        )

    def test_minute_limit_is_per_ip_and_refresh_token_fingerprint(self):
        responses = [
            self.post_refresh("synthetic-refresh-token")
            for _ in range(11)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:10]))
        self.assertEqual(responses[10].status_code, 429)
        self.assertIn("Retry-After", responses[10])
        self.assertLessEqual(int(responses[10]["Retry-After"]), 60)

    def test_different_refresh_tokens_have_distinct_minute_buckets(self):
        responses = [
            self.post_refresh("first-synthetic-refresh-token")
            for _ in range(11)
        ]
        other_token_response = self.post_refresh("second-synthetic-refresh-token")

        self.assertEqual(responses[-1].status_code, 429)
        self.assertEqual(other_token_response.status_code, 200)

    def test_hourly_limit_is_per_ip_across_refresh_tokens(self):
        responses = [
            self.post_refresh(f"synthetic-refresh-token-{index}")
            for index in range(31)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:30]))
        self.assertEqual(responses[30].status_code, 429)
        self.assertGreater(int(responses[30]["Retry-After"]), 60)

    def test_plaintext_refresh_token_never_appears_in_redis_keys(self):
        token = "synthetic-private-refresh-token"

        self.post_refresh(token)

        self.assertTrue(self.redis.keys_seen)
        for key in self.redis.keys_seen:
            self.assertTrue(key.startswith("dmc:ratelimit:v1:token_refresh:"))
            self.assertNotIn(token, key)

    def test_refresh_view_preserves_simplejwt_rotation_and_blacklist_configuration(self):
        self.assertTrue(issubclass(RateLimitedTokenRefreshView, TokenRefreshView))
        self.assertIs(
            RateLimitedTokenRefreshView.post,
            TokenRefreshView.post,
        )
        self.assertIs(
            RateLimitedTokenRefreshView.serializer_class,
            TokenRefreshView.serializer_class,
        )
        self.assertTrue(settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"])
        self.assertTrue(settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"])
