import requests

from .constants import (
    META_GRAPH_BASE_URL,
    META_TOKEN_URL,
)
from .exceptions import MetaIntegrationError


class MetaAPIClient:
    """
    Small provider client responsible only for
    communicating with Meta Graph API.
    """

    def __init__(self, *, access_token=None):
        self.access_token = access_token

    # ========================================================
    # ACCESS TOKEN
    # ========================================================

    def exchange_code_for_access_token(
        self,
        *,
        app_id,
        app_secret,
        redirect_uri,
        code,
    ):
        """
        Exchange OAuth authorization code for a Meta
        access token.
        """

        params = {
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }

        try:
            response = requests.get(
                META_TOKEN_URL,
                params=params,
                timeout=15,
            )
        except requests.RequestException as exc:
            raise MetaIntegrationError(
                "Unable to connect to Meta."
            ) from exc

        if not response.ok:
            raise MetaIntegrationError(
                "Meta token exchange failed."
            )

        data = response.json()

        access_token = data.get("access_token")

        if not access_token:
            raise MetaIntegrationError(
                "Meta did not return an access token."
            )

        return data

    # ========================================================
    # GRAPH API
    # ========================================================

    def get(
        self,
        endpoint,
        *,
        params=None,
    ):
        """
        Perform an authenticated GET request against
        the Meta Graph API.
        """

        if not self.access_token:
            raise MetaIntegrationError(
                "Meta access token is required."
            )

        request_params = dict(params or {})

        request_params["access_token"] = (
            self.access_token
        )

        url = (
            f"{META_GRAPH_BASE_URL}"
            f"/{endpoint.lstrip('/')}"
        )

        try:
            response = requests.get(
                url,
                params=request_params,
                timeout=15,
            )
        except requests.RequestException as exc:
            raise MetaIntegrationError(
                "Unable to connect to Meta Graph API."
            ) from exc

        if not response.ok:
            raise MetaIntegrationError(
                "Meta Graph API request failed."
            )

        data = response.json()

        if isinstance(data, dict) and data.get("error"):
            raise MetaIntegrationError(
                data["error"].get(
                    "message",
                    "Meta Graph API returned an error.",
                )
            )

        return data