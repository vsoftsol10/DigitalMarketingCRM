import logging
from typing import Any, Dict, Optional, Tuple, Union

import requests
from django.conf import settings

from .constants import (
    META_GRAPH_BASE_URL,
    META_HTTP_TIMEOUT_SECONDS,
    META_INSTAGRAM_PROFILE_FIELDS,
    META_PAGE_DETAIL_FIELDS,
    META_PAGE_FIELDS,
    META_TOKEN_URL,
)
from .exceptions import MetaAPIError

logger = logging.getLogger(__name__)


class MetaAPIClient:
    """
    Small, provider-specific HTTP client for Meta Graph API.

    Responsibilities:
        - Build Graph API URLs.
        - Attach access tokens.
        - Exchange OAuth authorization codes.
        - Normalize Meta API errors.
        - Retrieve Pages and linked Instagram accounts.

    This class does not contain persistence logic.
    """

    def __init__(self):
        self.base_url = META_GRAPH_BASE_URL

        self.timeout = getattr(
            settings,
            "META_HTTP_TIMEOUT_SECONDS",
            META_HTTP_TIMEOUT_SECONDS,
        )

    # ========================================================
    # URL
    # ========================================================

    def _build_url(
        self,
        path: str,
    ) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path

        return f"{self.base_url}/" f"{path.lstrip('/')}"

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    @staticmethod
    def _extract_error_message(
        payload: Any,
    ) -> str:
        if isinstance(payload, dict):
            error = payload.get("error")

            if isinstance(error, dict):
                message = error.get("message")

                if message:
                    return str(message)

            message = payload.get("message")

            if message:
                return str(message)

        return "Meta API request failed."

    @staticmethod
    def _safe_response(
        response: requests.Response,
        response_metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        try:
            payload = response.json()

            if isinstance(payload, dict):
                if response_metadata is not None:
                    response_metadata["_provider_data_key_present"] = "data" in payload
                return payload

            if response_metadata is not None:
                response_metadata["_provider_data_key_present"] = False
                response_metadata["_unexpected_response_structure"] = True
            return {
                "data": payload,
            }

        except ValueError:
            if response_metadata is not None:
                response_metadata["_provider_data_key_present"] = False
                response_metadata["_unexpected_response_structure"] = True
            return {
                "error": {"message": (response.text or "Invalid response from Meta.")}
            }

    def _handle_response(
        self,
        response: requests.Response,
        response_metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        payload = self._safe_response(response, response_metadata)

        if not response.ok:
            message = self._extract_error_message(
                payload,
            )

            raise MetaAPIError(
                message,
                status_code=response.status_code,
                error_payload=payload,
            )

        return payload

    @staticmethod
    def safe_error_metadata(error: MetaAPIError) -> dict:
        """Return only non-sensitive HTTP and Graph error identifiers."""
        payload = getattr(error, "error_payload", None)
        graph_error = payload.get("error") if isinstance(payload, dict) else None
        if not isinstance(graph_error, dict):
            graph_error = {}

        def safe_integer(value):
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            return None

        return {
            "http_status": safe_integer(getattr(error, "status_code", None)),
            "graph_error_code": safe_integer(graph_error.get("code")),
            "graph_error_subcode": safe_integer(
                graph_error.get("error_subcode"),
            ),
        }

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        path: str,
        *,
        access_token: str,
        params: Optional[Dict[str, Any]] = None,
        return_http_status: bool = False,
        response_metadata: Optional[Dict[str, Any]] = None,
    ) -> Union[dict, Tuple[dict, int]]:
        if not access_token:
            raise MetaAPIError(
                "Meta access token is required.",
            )

        request_params = dict(
            params or {},
        )

        request_params["access_token"] = access_token

        url = self._build_url(path)

        try:
            response = requests.get(
                url,
                params=request_params,
                timeout=self.timeout,
            )

        except requests.RequestException:
            # GET requests carry the access token in query parameters, and
            # logging request details or a traceback can expose that token.
            logger.error("Meta GET request failed.")

            raise MetaAPIError(
                "Meta API request failed.",
            ) from None

        payload = self._handle_response(
            response,
            response_metadata,
        )
        if return_http_status:
            return payload, response.status_code
        return payload

    def post(self, path: str, *, access_token: str, data=None) -> dict:
        """POST to Graph without ever logging credentials or request bodies."""
        if not access_token:
            raise MetaAPIError("Meta access token is required.")

        payload = dict(data or {})
        payload["access_token"] = access_token
        url = self._build_url(path)

        try:
            response = requests.post(url, data=payload, timeout=self.timeout)
        except requests.RequestException:
            logger.error("Meta POST request failed.")
            raise MetaAPIError("Meta API request failed.") from None

        return self._handle_response(response)

    def upload_reel_video(
        self,
        upload_url: str,
        *,
        access_token: str,
        video_file,
        file_size: int,
    ) -> dict:
        """Upload a Page Reel binary to Meta's resumable-upload URL."""
        if not upload_url:
            raise MetaAPIError("Facebook Reel upload URL is required.")
        if not access_token:
            raise MetaAPIError("Meta access token is required.")

        try:
            response = requests.post(
                upload_url,
                data=video_file,
                headers={
                    "Authorization": f"OAuth {access_token}",
                    "offset": "0",
                    "file_size": str(file_size),
                    "Content-Type": "application/octet-stream",
                },
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.error("Meta Reel video upload failed.")
            raise MetaAPIError("Meta Reel video upload failed.") from None

        return self._handle_response(response)

    # ========================================================
    # OAUTH CODE EXCHANGE
    # ========================================================

    def exchange_code_for_access_token(
        self,
        *,
        code: str,
    ) -> dict:
        if not code:
            raise MetaAPIError(
                "Meta authorization code is required.",
            )

        app_id = getattr(
            settings,
            "META_APP_ID",
            "",
        )

        app_secret = getattr(
            settings,
            "META_APP_SECRET",
            "",
        )

        redirect_uri = (
            getattr(
                settings,
                "META_OAUTH_REDIRECT_URI",
                "",
            )
            or ""
        ).strip()

        if not app_id:
            raise MetaAPIError(
                "META_APP_ID is not configured.",
            )

        if not app_secret:
            raise MetaAPIError(
                "META_APP_SECRET is not configured.",
            )

        if not redirect_uri:
            raise MetaAPIError(
                "META_OAUTH_REDIRECT_URI is not configured.",
            )

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
                timeout=self.timeout,
            )

        except requests.RequestException:
            # The request URL contains the app secret and OAuth code. Do not
            # log the request exception or chain it into later traceback logs.
            logger.error("Meta OAuth token exchange request failed.")

            raise MetaAPIError(
                "Meta token exchange request failed.",
            ) from None

        return self._handle_response(
            response,
        )

    # ========================================================
    # CURRENT META USER
    # ========================================================

    def get_current_user(
        self,
        *,
        access_token: str,
    ) -> dict:
        return self.get(
            "/me",
            access_token=access_token,
            params={
                "fields": "id,name",
            },
        )

    # ========================================================
    # USER PERMISSIONS
    # ========================================================

    def get_user_permissions(
        self,
        *,
        access_token: str,
    ) -> dict:
        return self.get(
            "/me/permissions",
            access_token=access_token,
        )

    # ========================================================
    # DEBUG TOKEN
    # ========================================================

    def debug_token(
        self,
        *,
        input_token: str,
    ) -> dict:
        app_id = getattr(
            settings,
            "META_APP_ID",
            "",
        )

        app_secret = getattr(
            settings,
            "META_APP_SECRET",
            "",
        )

        if not app_id or not app_secret:
            raise MetaAPIError(
                "Meta app credentials are not configured.",
            )

        app_access_token = f"{app_id}|{app_secret}"

        return self.get(
            "/debug_token",
            access_token=app_access_token,
            params={
                "input_token": input_token,
            },
        )

    # ========================================================
    # FACEBOOK PAGES
    # ========================================================

    def get_pages(
        self,
        *,
        access_token: str,
        response_metadata: Optional[Dict[str, Any]] = None,
    ) -> list:
        try:
            response, http_status_code = self.get(
                "/me/accounts",
                access_token=access_token,
                params={
                    "fields": META_PAGE_FIELDS,
                },
                return_http_status=True,
                response_metadata=response_metadata,
            )
        except MetaAPIError as exc:
            if response_metadata is not None:
                error_metadata = self.safe_error_metadata(exc)
                response_metadata.update(
                    {
                        "http_status_code": error_metadata["http_status"],
                        "graph_error_code": error_metadata["graph_error_code"],
                        "graph_error_subcode": error_metadata[
                            "graph_error_subcode"
                        ],
                        "response_case": "api_request_failure",
                    }
                )
            raise

        provider_data_key_present = (
            response_metadata.pop("_provider_data_key_present", "data" in response)
            if response_metadata is not None
            else "data" in response
        )
        unexpected_response_structure = (
            response_metadata.pop("_unexpected_response_structure", False)
            if response_metadata is not None
            else False
        )
        data_present = bool(provider_data_key_present)
        data_value = response.get("data")
        pages = data_value if "data" in response else []
        paging_present = "paging" in response
        paging = response.get("paging")
        paging_is_dict = isinstance(paging, dict)
        paging_next_present = bool(paging.get("next")) if paging_is_dict else False
        pages_is_list = isinstance(pages, list)

        if unexpected_response_structure:
            response_case = "unexpected_response_structure"
        elif not data_present:
            response_case = "missing_data_key"
        elif not pages_is_list or (paging_present and not paging_is_dict):
            response_case = "unexpected_response_structure"
        elif not pages:
            response_case = "explicitly_empty_data"
        elif paging_next_present:
            response_case = "response_contains_additional_pages"
        else:
            response_case = "pages_returned"

        if response_metadata is not None:
            response_metadata.update(
                {
                    "http_status_code": http_status_code,
                    "data_present": data_present,
                    "data_type": type(data_value).__name__ if data_present else "missing",
                    "parsed_page_count": len(pages) if pages_is_list else None,
                    "paging_present": paging_present,
                    "paging_next_present": paging_next_present,
                    "response_case": response_case,
                    "graph_error_code": None,
                    "graph_error_subcode": None,
                }
            )

        if not pages_is_list:
            raise MetaAPIError(
                "Meta returned an invalid Pages response.",
            )

        return pages

    # ========================================================
    # SPECIFIC FACEBOOK PAGE
    # ========================================================

    def get_page(
        self,
        *,
        page_id: str,
        access_token: str,
    ) -> dict:
        if not page_id:
            raise MetaAPIError(
                "Facebook Page ID is required.",
            )

        return self.get(
            f"/{page_id}",
            access_token=access_token,
            params={
                "fields": META_PAGE_DETAIL_FIELDS,
            },
        )

    # ========================================================
    # INSTAGRAM PROFILE
    # ========================================================

    def get_instagram_profile(
        self,
        *,
        instagram_account_id: str,
        access_token: str,
    ) -> dict:
        if not instagram_account_id:
            raise MetaAPIError(
                "Instagram account ID is required.",
            )

        return self.get(
            f"/{instagram_account_id}",
            access_token=access_token,
            params={
                "fields": META_INSTAGRAM_PROFILE_FIELDS,
            },
        )

    # ========================================================
    # COMPATIBILITY ALIAS
    # ========================================================

    def get_assigned_pages(
        self,
        *,
        access_token: str,
    ) -> list:
        return self.get_pages(
            access_token=access_token,
        )

    # ========================================================
    # TOKEN DIAGNOSTICS
    # ========================================================

    def diagnose_token(
        self,
        *,
        access_token: str,
    ) -> dict:
        debug = self.debug_token(
            input_token=access_token,
        )

        return debug.get(
            "data",
            {},
        )
