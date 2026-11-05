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

META_PAGE_DISCOVERY_MAX_PAGES = 100


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
        self.last_response_status_code = None

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
        self.last_response_status_code = None

        try:
            response = requests.post(url, data=payload, timeout=self.timeout)
            self.last_response_status_code = response.status_code
        except requests.Timeout as exc:
            logger.warning(
                "Meta POST request timed out. exception_type=%s",
                type(exc).__name__,
            )
            logger.error("Meta POST request failed.")
            raise MetaAPIError("Meta API request failed.") from None
        except requests.RequestException as exc:
            logger.warning(
                "Meta POST request raised a transport error. exception_type=%s",
                type(exc).__name__,
            )
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

        self.last_response_status_code = None
        try:
            response = requests.post(
                upload_url,
                data=video_file,
                headers={
                    "Authorization": f"OAuth {access_token}",
                    "offset": "0",
                    "file_size": str(file_size),
                    "Content-Length": str(file_size),
                    "Content-Type": "application/octet-stream",
                },
                timeout=self.timeout,
            )
            self.last_response_status_code = response.status_code
        except requests.Timeout as exc:
            logger.warning(
                "Meta video upload timed out. exception_type=%s",
                type(exc).__name__,
            )
            logger.error("Meta Reel video upload failed.")
            raise MetaAPIError("Meta Reel video upload failed.") from None
        except requests.RequestException as exc:
            logger.warning(
                "Meta video upload raised a transport error. exception_type=%s",
                type(exc).__name__,
            )
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
        redirect_uri: Optional[str] = None,
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
            redirect_uri
            or getattr(
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
        discovered_pages = []
        cursor = None
        seen_cursors = set()
        first_response = None
        final_status = None
        total_count = 0
        paging_present = False
        paging_next_present = False
        data_present = True
        unexpected_response_structure = False

        try:
            for page_number in range(1, META_PAGE_DISCOVERY_MAX_PAGES + 1):
                page_metadata = {}
                params = {"fields": META_PAGE_FIELDS}
                if cursor:
                    params["after"] = cursor

                response, final_status = self.get(
                    "/me/accounts",
                    access_token=access_token,
                    params=params,
                    return_http_status=True,
                    response_metadata=page_metadata,
                )

                provider_data_key_present = page_metadata.pop(
                    "_provider_data_key_present",
                    "data" in response,
                )
                unexpected_response_structure = unexpected_response_structure or page_metadata.pop(
                    "_unexpected_response_structure",
                    False,
                )
                data_value = response.get("data")
                batch = data_value if provider_data_key_present else []
                paging = response.get("paging")
                current_paging_present = "paging" in response
                current_paging_valid = isinstance(paging, dict)
                has_next = bool(paging.get("next")) if current_paging_valid else False
                paging_present = paging_present or current_paging_present
                paging_next_present = paging_next_present or has_next
                data_present = data_present and bool(provider_data_key_present)

                if first_response is None:
                    first_response = {
                        "data_type": (
                            type(data_value).__name__
                            if provider_data_key_present
                            else "missing"
                        ),
                        "paging_present": current_paging_present,
                    }

                if not isinstance(batch, list) or (
                    current_paging_present and not current_paging_valid
                ):
                    unexpected_response_structure = True
                    if response_metadata is not None:
                        response_metadata.update(
                            {
                                "http_status_code": final_status,
                                "data_present": bool(provider_data_key_present),
                                "data_type": (
                                    type(data_value).__name__
                                    if provider_data_key_present
                                    else "missing"
                                ),
                                "parsed_page_count": (
                                    None if not isinstance(batch, list) else total_count
                                ),
                                "paging_present": paging_present,
                                "paging_next_present": paging_next_present,
                                "graph_error_code": None,
                                "graph_error_subcode": None,
                                "response_case": "unexpected_response_structure",
                            }
                        )
                    raise MetaAPIError("Meta returned an invalid Pages response.")

                discovered_pages.extend(batch)
                total_count += len(batch)

                if not has_next:
                    break

                cursors = paging.get("cursors")
                next_cursor = cursors.get("after") if isinstance(cursors, dict) else None
                if not isinstance(next_cursor, str) or not next_cursor:
                    raise MetaAPIError(
                        "Meta returned incomplete Facebook Page pagination data."
                    )
                if next_cursor in seen_cursors or next_cursor == cursor:
                    raise MetaAPIError("Meta returned a repeated Facebook Page cursor.")
                seen_cursors.add(next_cursor)
                cursor = next_cursor
            else:
                raise MetaAPIError(
                    "Facebook Page discovery exceeded the pagination limit."
                )

        except MetaAPIError as exc:
            if response_metadata is not None:
                error_metadata = self.safe_error_metadata(exc)
                response_metadata.update(
                    {
                        "http_status_code": error_metadata["http_status"],
                        "graph_error_code": error_metadata["graph_error_code"],
                        "graph_error_subcode": error_metadata["graph_error_subcode"],
                        "response_case": (
                            "unexpected_response_structure"
                            if unexpected_response_structure
                            else "api_request_failure"
                        ),
                    }
                )
            raise

        if response_metadata is not None:
            if unexpected_response_structure:
                response_case = "unexpected_response_structure"
            elif not data_present:
                response_case = "missing_data_key"
            elif not discovered_pages:
                response_case = "explicitly_empty_data"
            elif paging_next_present:
                response_case = "response_contains_additional_pages"
            else:
                response_case = "pages_returned"

            response_metadata.update(
                {
                    "http_status_code": final_status,
                    "data_present": data_present,
                    "data_type": first_response["data_type"] if first_response else "missing",
                    "parsed_page_count": total_count,
                    "paging_present": paging_present,
                    "paging_next_present": paging_next_present,
                    "response_case": response_case,
                    "graph_error_code": None,
                    "graph_error_subcode": None,
                }
            )

        return discovered_pages

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
