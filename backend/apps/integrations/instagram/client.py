from datetime import timedelta

import requests
from django.conf import settings

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

    def __init__(self):
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

    def _handle_response(
        self,
        response,
        *,
        operation,
    ):
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
            )

        return payload

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
        response = requests.post(
            f"{INSTAGRAM_GRAPH_BASE_URL}/{INSTAGRAM_GRAPH_API_VERSION}/{path.lstrip('/')}",
            data={**data, "access_token": access_token},
            timeout=self.timeout,
        )
        return self._handle_response(response, operation="Instagram content publishing")

    def graph_get(self, path, *, access_token, params=None):
        if not access_token:
            raise InstagramAPIError("Instagram access token is missing.")
        response = requests.get(
            f"{INSTAGRAM_GRAPH_BASE_URL}/{INSTAGRAM_GRAPH_API_VERSION}/{path.lstrip('/')}",
            params={**(params or {}), "access_token": access_token},
            timeout=self.timeout,
        )
        return self._handle_response(response, operation="Instagram content publishing")
