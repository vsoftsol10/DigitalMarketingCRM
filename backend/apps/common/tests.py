import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import Throttled, ValidationError

from .exception_handler import custom_exception_handler
from .throttles import RateLimitBackendUnavailable, RedisRateThrottle


class ExampleRateThrottle(RedisRateThrottle):
    scope = "example"


@override_settings(
    DMC_RATE_LIMITS={"example": ((2, 60), (4, 3600))},
    DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="closed",
)
class RedisRateThrottleTests(SimpleTestCase):
    databases = set()

    def setUp(self):
        self.redis = Mock()
        redis_client_patcher = patch.object(
            RedisRateThrottle,
            "_redis_client",
            return_value=self.redis,
        )
        redis_client_patcher.start()
        self.addCleanup(redis_client_patcher.stop)
        self.request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, pk=42),
            META={"REMOTE_ADDR": "203.0.113.15"},
        )

    def test_multiple_windows_are_counted_in_one_atomic_eval(self):
        self.redis.eval.return_value = [1, 59999, 1, 3599999]
        throttle = ExampleRateThrottle()

        self.assertTrue(throttle.allow_request(self.request, None))

        args = self.redis.eval.call_args.args
        self.assertEqual(args[1], 2)
        digest = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            b"user:42",
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(args[2], f"dmc:ratelimit:v1:example:{digest}:2:60")
        self.assertEqual(args[3], f"dmc:ratelimit:v1:example:{digest}:4:3600")
        self.assertEqual(args[4:], (60000, 3600000))
        self.assertIn("redis.call('INCR'", args[0])
        self.assertIn("redis.call('PEXPIRE'", args[0])
        self.assertEqual(throttle.remaining_requests, 1)
        self.assertIsNone(throttle.wait())

    def test_exceeded_window_rejects_request_and_calculates_retry_time(self):
        self.redis.eval.return_value = [3, 1250, 5, 2500]
        throttle = ExampleRateThrottle()

        self.assertFalse(throttle.allow_request(self.request, None))

        self.assertEqual(throttle.remaining_requests, 0)
        self.assertEqual(throttle.wait(), 3)

    def test_counter_reset_after_expiry_is_allowed_and_remaining_is_recomputed(self):
        now_ms = [0]
        counters = {}

        def increment_windows(_script, key_count, *keys_and_windows):
            keys = keys_and_windows[:key_count]
            windows_ms = keys_and_windows[key_count:]
            result = []
            for key, window_ms in zip(keys, windows_ms):
                current = counters.get(key)
                if current and current[1] <= now_ms[0]:
                    current = None
                if current is None:
                    current = [0, now_ms[0] + window_ms]
                current[0] += 1
                counters[key] = current
                result.extend([current[0], current[1] - now_ms[0]])
            return result

        self.redis.eval.side_effect = increment_windows
        throttle = ExampleRateThrottle()

        self.assertTrue(throttle.allow_request(self.request, None))
        self.assertTrue(throttle.allow_request(self.request, None))
        self.assertFalse(throttle.allow_request(self.request, None))
        now_ms[0] = 60000
        self.assertTrue(throttle.allow_request(self.request, None))
        self.assertEqual(throttle.remaining_requests, 0)

    def test_anonymous_subject_uses_hashed_client_identity(self):
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=False),
            META={"REMOTE_ADDR": "203.0.113.15"},
        )
        self.redis.eval.return_value = [1, 59999, 1, 3599999]
        throttle = ExampleRateThrottle()

        self.assertTrue(throttle.allow_request(request, None))

        key = self.redis.eval.call_args.args[2]
        digest = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            b"ip:203.0.113.15",
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(key, f"dmc:ratelimit:v1:example:{digest}:2:60")
        self.assertNotIn("203.0.113.15", key)

    def test_redis_failure_fails_closed_with_service_unavailable(self):
        self.redis.eval.side_effect = OSError("synthetic Redis unavailable")
        throttle = ExampleRateThrottle()

        with self.assertRaises(RateLimitBackendUnavailable):
            throttle.allow_request(self.request, None)

    @override_settings(DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="open")
    def test_redis_failure_can_be_explicitly_configured_to_fail_open(self):
        self.redis.eval.side_effect = OSError("synthetic Redis unavailable")
        throttle = ExampleRateThrottle()

        self.assertTrue(throttle.allow_request(self.request, None))


class CustomExceptionHandlerHeaderTests(SimpleTestCase):
    databases = set()

    def test_throttled_response_preserves_retry_after_header_and_envelope(self):
        response = custom_exception_handler(Throttled(wait=12), {})

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "12")
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

    def test_validation_error_structure_and_status_are_preserved(self):
        response = custom_exception_handler(
            ValidationError({"name": ["This field is required."]}),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"], {"name": ["This field is required."]})

    def test_authentication_challenge_header_is_preserved(self):
        from rest_framework.exceptions import NotAuthenticated

        exception = NotAuthenticated()
        exception.auth_header = "Bearer"
        response = custom_exception_handler(
            exception,
            {},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("WWW-Authenticate", response)
