import json
import time
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache

from .constants import (
    INSTAGRAM_GRAPH_API_VERSION,
    INSTAGRAM_GRAPH_BASE_URL,
    INSTAGRAM_HTTP_TIMEOUT_SECONDS,
    INSTAGRAM_PROFILE_FIELDS,
    INSTAGRAM_TOKEN_URL,
)
from .exceptions import (
    InstagramAPIError,
    InstagramOAuthConfigurationError,
)


class InstagramAPIClient:
    """
    Server-side client for Instagram API with Instagram Login.

    OAuth token exchange uses:
        api.instagram.com

    Instagram Graph API requests use:
        graph.instagram.com
    """

    # Meta's documented application-usage response header. Keep the parsed
    # diagnostics deliberately narrow: request headers can contain secrets,
    # and provider payloads must not become an unbounded logging surface.
    _USAGE_HEADER_NAME = "X-App-Usage"
    _USAGE_FIELDS = {
        "call_count",
        "total_cputime",
        "total_time",
        "estimated_time_to_regain_access",
    }
    _GRAPH_REQUEST_PACER_KEY = "instagram:graph-request-pacer:v1"
    _RESERVE_GRAPH_REQUEST_SLOT_SCRIPT = """
local current = redis.call('TIME')
local now_ms = (tonumber(current[1]) * 1000) + math.floor(tonumber(current[2]) / 1000)
local interval_ms = tonumber(ARGV[1])
local next_ms = tonumber(redis.call('GET', KEYS[1])) or now_ms
local slot_ms = math.max(now_ms, next_ms)
local following_ms = slot_ms + interval_ms
local ttl_ms = math.max(1000, following_ms - now_ms + 1000)
redis.call('SET', KEYS[1], following_ms, 'PX', ttl_ms)
return slot_ms - now_ms
"""

    def __init__(self):
        # Diagnostic metadata only; response payloads remain unchanged.
        self.last_response_status_code = None
        self.last_response_usage_diagnostics = {}
        self.client_id = getattr(
            settings,
            "INSTAGRAM_APP_ID",
            "",
        )

        self.client_secret = getattr(
            settings,
            "INSTAGRAM_APP_SECRET",
            "",
        )

        self.redirect_uri = getattr(
            settings,
            "INSTAGRAM_OAUTH_REDIRECT_URI",
            "",
        )

        self.timeout = INSTAGRAM_HTTP_TIMEOUT_SECONDS

        if not self.client_id:
            raise InstagramOAuthConfigurationError(
                "Instagram app ID is not configured."
            )

        if not self.client_secret:
            raise InstagramOAuthConfigurationError(
                "Instagram app secret is not configured."
            )

        if not self.redirect_uri:
            raise InstagramOAuthConfigurationError(
                "Instagram OAuth redirect URI is not configured."
            )

    # ========================================================
    # INTERNAL REQUEST HANDLER
    # ========================================================

    @classmethod
    def _safe_usage_diagnostics(cls, response):
        """Return a numeric-only, allowlisted subset of Meta usage data."""
        raw_value = response.headers.get(cls._USAGE_HEADER_NAME)
        if not raw_value:
            return {}

        try:
            usage = json.loads(raw_value)
        except (TypeError, ValueError):
            return {}

        if not isinstance(usage, dict):
            return {}

        safe_usage = {
            key: value
            for key, value in usage.items()
            if key in cls._USAGE_FIELDS
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        }
        return {"x-app-usage": safe_usage} if safe_usage else {}

    def _handle_response(
        self,
        response,
        *,
        operation,
    ):
        self.last_response_status_code = response.status_code
        self.last_response_usage_diagnostics = self._safe_usage_diagnostics(
            response,
        )

        try:
            payload = response.json()
        except ValueError:
            payload = {
                "raw": response.text,
            }

        if not response.ok:
            raise InstagramAPIError(
                (
                    f"Instagram API request failed "
                    f"during {operation}."
                ),
                status_code=response.status_code,
                error_payload=payload,
                usage_diagnostics=self.last_response_usage_diagnostics,
            )

        return payload

    @classmethod
    def _reserve_graph_request_slot(cls):
        """Atomically reserve one globally paced Instagram Graph request slot."""
        interval_seconds = float(
            getattr(settings, "INSTAGRAM_GRAPH_REQUEST_INTERVAL_SECONDS", 1.0)
        )
        if interval_seconds <= 0:
            raise InstagramAPIError(
                "Instagram Graph request pacing is not configured safely."
            )

        try:
            redis_client = cache._cache.get_client(write=True)
            delay_ms = redis_client.eval(
                cls._RESERVE_GRAPH_REQUEST_SLOT_SCRIPT,
                1,
                cache.make_key(cls._GRAPH_REQUEST_PACER_KEY),
                max(1, round(interval_seconds * 1000)),
            )
        except Exception as exc:
            raise InstagramAPIError(
                "Instagram Graph request pacing is unavailable."
            ) from exc

        if delay_ms > 0:
            time.sleep(delay_ms / 1000)

    def _pace_graph_request(self):
        """Wait for the shared application-wide request reservation."""
        self._reserve_graph_request_slot()

    # ========================================================
    # AUTHORIZATION CODE → SHORT TOKEN
    # ========================================================

    def exchange_code(
        self,
        *,
        code,
    ):
        if not code:
            raise InstagramAPIError(
                "Instagram authorization code is missing."
            )

        response = requests.post(
            INSTAGRAM_TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": code,
            },
            timeout=self.timeout,
        )

        return self._handle_response(
            response,
            operation="authorization code exchange",
        )

    # ========================================================
    # SHORT TOKEN → LONG-LIVED TOKEN
    # ========================================================

    def exchange_long_lived_token(
        self,
        *,
        short_lived_token,
    ):
        if not short_lived_token:
            raise InstagramAPIError(
                "Short-lived Instagram access token is missing."
            )

        self._pace_graph_request()

        response = requests.get(
            f"{INSTAGRAM_GRAPH_BASE_URL}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": self.client_secret,
                "access_token": short_lived_token,
            },
            timeout=self.timeout,
        )

        return self._handle_response(
            response,
            operation="long-lived token exchange",
        )

    # ========================================================
    # LONG-LIVED TOKEN REFRESH
    # ========================================================

    def refresh_long_lived_token(
        self,
        *,
        access_token,
    ):
        if not access_token:
            raise InstagramAPIError(
                "Instagram access token is missing."
            )

        self._pace_graph_request()

        response = requests.get(
            f"{INSTAGRAM_GRAPH_BASE_URL}/refresh_access_token",
            params={
                "grant_type": "ig_refresh_token",
                "access_token": access_token,
            },
            timeout=self.timeout,
        )

        return self._handle_response(
            response,
            operation="long-lived token refresh",
        )

    # ========================================================
    # PROFILE
    # ========================================================

    def get_profile(
        self,
        *,
        access_token,
    ):
        self._pace_graph_request()
        response = requests.get(
            (
                f"{INSTAGRAM_GRAPH_BASE_URL}/"
                f"{INSTAGRAM_GRAPH_API_VERSION}/me"
            ),
            params={
                "fields": INSTAGRAM_PROFILE_FIELDS,
                "access_token": access_token,
            },
            timeout=self.timeout,
        )

        return self._handle_response(
            response,
            operation="Instagram profile lookup",
        )

    def graph_post(self, path, *, access_token, data):
        if not access_token:
            raise InstagramAPIError("Instagram access token is missing.")
        self._pace_graph_request()
        response = requests.post(
            f"{INSTAGRAM_GRAPH_BASE_URL}/{INSTAGRAM_GRAPH_API_VERSION}/{path.lstrip('/')}",
            data={**data, "access_token": access_token},
            timeout=self.timeout,
        )
        return self._handle_response(response, operation="Instagram content publishing")

    def graph_get(self, path, *, access_token, params=None):
        if not access_token:
            raise InstagramAPIError("Instagram access token is missing.")
        self._pace_graph_request()
        response = requests.get(
            f"{INSTAGRAM_GRAPH_BASE_URL}/{INSTAGRAM_GRAPH_API_VERSION}/{path.lstrip('/')}",
            params={**(params or {}), "access_token": access_token},
            timeout=self.timeout,
        )
        return self._handle_response(response, operation="Instagram content publishing")
