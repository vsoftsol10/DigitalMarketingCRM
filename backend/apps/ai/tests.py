from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.common.throttles import RedisRateThrottle

from .views import AICaptionGenerateAPIView


class InMemoryAtomicRedis:
    """Deterministic in-memory stand-in for the limiter's atomic EVAL."""

    def __init__(self):
        self.now_ms = 0
        self.counters = {}
        self.keys_seen = []

    def advance(self, milliseconds):
        self.now_ms += milliseconds

    def eval(self, _script, key_count, *keys_and_windows):
        keys = keys_and_windows[:key_count]
        windows_ms = keys_and_windows[key_count:]
        self.keys_seen.extend(keys)
        values = []
        for key, window_ms in zip(keys, windows_ms):
            counter = self.counters.get(key)
            if counter and counter[1] <= self.now_ms:
                counter = None
            if counter is None:
                counter = [0, self.now_ms + window_ms]
            counter[0] += 1
            self.counters[key] = counter
            values.extend((counter[0], counter[1] - self.now_ms))
        return values


@override_settings(
    DMC_RATE_LIMITS={"ai_caption_generate": ((5, 60), (50, 86400))},
    DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="closed",
)
class AICaptionRateLimitTests(SimpleTestCase):
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
        self.service_patcher = patch(
            "apps.ai.views.AICaptionService.generate_captions",
            return_value=["First caption", "Second caption", "Third caption"],
        )
        self.generate_captions = self.service_patcher.start()
        self.addCleanup(self.service_patcher.stop)
        self.view = AICaptionGenerateAPIView.as_view()

    def post(self, user_id="synthetic-user", payload=None):
        request = self.factory.post(
            "/api/ai/captions/generate/",
            payload
            or {
                "prompt": "Synthetic prompt",
                "tone": "PROFESSIONAL",
                "length": "SHORT",
                "include_emoji": False,
                "include_hashtags": False,
                "include_cta": False,
            },
            format="json",
        )
        force_authenticate(
            request,
            user=SimpleNamespace(pk=user_id, is_authenticated=True),
        )
        return self.view(request)

    def test_under_limit_preserves_caption_response_and_service_arguments(self):
        response = self.post()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "AI captions generated successfully.")
        self.assertEqual(
            response.data["data"],
            [
                {"id": 1, "title": "Professional", "caption": "First caption"},
                {"id": 2, "title": "Engaging", "caption": "Second caption"},
                {"id": 3, "title": "Promotional", "caption": "Third caption"},
            ],
        )
        self.generate_captions.assert_called_once_with(
            prompt="Synthetic prompt",
            tone="PROFESSIONAL",
            length="SHORT",
            include_emoji=False,
            include_hashtags=False,
            include_cta=False,
        )

    def test_minute_limit_is_five_per_authenticated_user(self):
        responses = [self.post() for _ in range(6)]

        self.assertTrue(all(response.status_code == 200 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)
        self.assertIn("Retry-After", responses[5])
        self.assertEqual(int(responses[5]["Retry-After"]), 60)

    def test_daily_limit_is_fifty_per_authenticated_user(self):
        responses = []
        for _ in range(10):
            responses.extend(self.post() for _ in range(5))
            self.redis.advance(60_000)

        limited = self.post()

        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertEqual(limited.status_code, 429)
        self.assertIn("Retry-After", limited)
        self.assertGreater(int(limited["Retry-After"]), 60)

    def test_different_users_have_separate_counters(self):
        limited_user_responses = [self.post("user-one") for _ in range(6)]
        other_user_response = self.post("user-two")

        self.assertEqual(limited_user_responses[-1].status_code, 429)
        self.assertEqual(other_user_response.status_code, 200)

    def test_redis_keys_use_hashed_authenticated_user_subject(self):
        self.post("private-user-identifier")

        self.assertEqual(len(self.redis.keys_seen), 2)
        for key in self.redis.keys_seen:
            self.assertTrue(key.startswith("dmc:ratelimit:v1:ai_caption_generate:"))
            self.assertNotIn("private-user-identifier", key)

    def test_request_validation_still_returns_existing_error_response(self):
        response = self.post(payload={"prompt": "Synthetic prompt"})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.generate_captions.assert_not_called()
