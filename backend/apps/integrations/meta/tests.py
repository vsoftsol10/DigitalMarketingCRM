import logging
import json
import uuid
from contextlib import nullcontext
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as datetime_timezone
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.models import Q
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.integrations.meta.client import MetaAPIClient
from apps.integrations.meta.exceptions import MetaAPIError
from apps.integrations.meta.lifecycle import MetaTokenLifecycleService
from apps.integrations.meta.models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaProviderExpiryState,
    MetaOAuthSession,
    MetaTokenMaintenanceRun,
)
from apps.integrations.meta.selectors import (
    get_meta_connection_credential,
    meta_user_credential_expiry_eligibility_q,
)
from apps.integrations.meta.services import (
    MetaAccountDiscoveryService,
    MetaAccountData,
    MetaDiscoveryResult,
    MetaOAuthService,
    MetaSocialAccountService,
)
from apps.integrations.meta.views import (
    MetaOAuthCallbackAPIView,
    MetaOAuthSelectionAPIView,
    MetaOAuthSelectionConfirmAPIView,
    MetaOAuthSelectionFinishAPIView,
)
from apps.notifications.models import UserNotification, UserNotificationType
from apps.notifications.services import record_social_credential_reconnect_required
from apps.organizations.models import Organization
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialConnectionStatus,
    SocialPlatform,
)
from apps.social_accounts.status import SocialAccountLifecycleStatus
from config.log_filters import CredentialRedactionFilter


ACCESS_TOKEN_CANARY = "ACCESS_TOKEN_CANARY_DO_NOT_LOG"
PAGE_TOKEN_CANARY = "PAGE_TOKEN_CANARY_DO_NOT_LOG"
APP_SECRET_CANARY = "APP_SECRET_CANARY_DO_NOT_LOG"
OAUTH_CODE_CANARY = "OAUTH_CODE_CANARY_DO_NOT_LOG"


class MetaDiagnosticLoggingConfigurationTests(SimpleTestCase):
    def test_service_diagnostics_use_redacted_local_info_console(self):
        logging_settings = settings.LOGGING
        logger_config = logging_settings["loggers"][
            "apps.integrations.meta.services"
        ]
        handler_config = logging_settings["handlers"][
            "meta_diagnostics_console"
        ]

        self.assertEqual(logger_config["level"], "INFO")
        self.assertEqual(logger_config["handlers"], ["meta_diagnostics_console"])
        self.assertFalse(logger_config["propagate"])
        self.assertEqual(handler_config["class"], "logging.StreamHandler")
        self.assertEqual(handler_config["level"], "INFO")
        self.assertEqual(
            handler_config["filters"],
            ["require_debug_true", "credential_redaction"],
        )
        self.assertEqual(
            logging_settings["filters"]["require_debug_true"]["()"],
            "django.utils.log.RequireDebugTrue",
        )

    def test_task_run_observability_uses_info_console_with_redaction(self):
        logging_settings = settings.LOGGING
        logger_config = logging_settings["loggers"]["apps.integrations.meta.tasks"]
        lifecycle_logger_config = logging_settings["loggers"][
            "apps.integrations.meta.lifecycle"
        ]
        handler_config = logging_settings["handlers"]["meta_maintenance_console"]

        self.assertEqual(logger_config["level"], "INFO")
        self.assertEqual(logger_config["handlers"], ["meta_maintenance_console"])
        self.assertFalse(logger_config["propagate"])
        self.assertEqual(
            lifecycle_logger_config["handlers"],
            ["meta_maintenance_console"],
        )
        self.assertFalse(lifecycle_logger_config["propagate"])
        self.assertEqual(handler_config["class"], "logging.StreamHandler")
        self.assertEqual(handler_config["level"], "INFO")
        self.assertEqual(handler_config["filters"], ["credential_redaction"])


class MetaCredentialRedactionFilterTests(SimpleTestCase):
    def test_sensitive_query_parameters_are_redacted_from_credential_urls(self):
        record = logging.LogRecord(
            name="http.client",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg=(
                "Request failed: https://graph.example/debug?input_token=%s"
                "&access_token=%s&client_secret=%s&code=%s"
                "&app_secret=%s&fb_exchange_token=%s&fields=id"
            ),
            args=(
                ACCESS_TOKEN_CANARY,
                PAGE_TOKEN_CANARY,
                APP_SECRET_CANARY,
                OAUTH_CODE_CANARY,
                APP_SECRET_CANARY,
                PAGE_TOKEN_CANARY,
            ),
            exc_info=None,
        )

        CredentialRedactionFilter().filter(record)
        output = record.getMessage()

        for secret in (
            ACCESS_TOKEN_CANARY,
            PAGE_TOKEN_CANARY,
            APP_SECRET_CANARY,
            OAUTH_CODE_CANARY,
        ):
            self.assertNotIn(secret, output)
        self.assertIn("input_token=[redacted]", output)
        self.assertIn("client_secret=[redacted]", output)
        self.assertIn("app_secret=[redacted]", output)
        self.assertIn("fb_exchange_token=[redacted]", output)
        self.assertIn("fields=id", output)

    def test_exception_traceback_is_redacted_before_record_is_emitted(self):
        try:
            raise requests.ConnectionError(
                "https://graph.example/me?input_token="
                f"{ACCESS_TOKEN_CANARY}&code={OAUTH_CODE_CANARY}"
            )
        except requests.ConnectionError:
            import sys

            exception_info = sys.exc_info()

        record = logging.LogRecord(
            name="http.client",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="request failed",
            args=(),
            exc_info=exception_info,
        )
        CredentialRedactionFilter().filter(record)
        output = record.getMessage() + (record.exc_text or "")

        self.assertNotIn(ACCESS_TOKEN_CANARY, output)
        self.assertNotIn(OAUTH_CODE_CANARY, output)
        self.assertIsNone(record.exc_info)


class MetaAPIClientRequestFailureTests(SimpleTestCase):
    @patch(
        "apps.integrations.meta.client.requests.get",
        side_effect=requests.ConnectionError(
            "https://graph.example/me?access_token="
            f"{ACCESS_TOKEN_CANARY}&input_token={PAGE_TOKEN_CANARY}"
        ),
    )
    def test_get_network_failure_is_generic_and_does_not_chain_url(self, get):
        client = MetaAPIClient()

        with self.assertLogs("apps.integrations.meta.client", level="ERROR") as logs:
            with self.assertRaises(MetaAPIError) as raised:
                client.get("/me", access_token=ACCESS_TOKEN_CANARY)

        output = "\n".join(logs.output)
        self.assertIn("Meta GET request failed", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)
        self.assertNotIn(PAGE_TOKEN_CANARY, output)
        self.assertIsNone(raised.exception.__cause__)
        self.assertTrue(raised.exception.__suppress_context__)

    @patch(
        "apps.integrations.meta.client.requests.post",
        side_effect=requests.ConnectionError(
            "https://graph.example/publish?access_token="
            f"{ACCESS_TOKEN_CANARY}&code={OAUTH_CODE_CANARY}"
        ),
    )
    def test_post_network_failure_does_not_log_or_chain_request_details(self, post):
        client = MetaAPIClient()

        with self.assertLogs("apps.integrations.meta.client", level="ERROR") as logs:
            with self.assertRaises(MetaAPIError) as raised:
                client.post("/publish", access_token=ACCESS_TOKEN_CANARY)

        output = "\n".join(logs.output)
        self.assertIn("Meta POST request failed", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)
        self.assertNotIn(OAUTH_CODE_CANARY, output)
        self.assertIsNone(raised.exception.__cause__)
        self.assertTrue(raised.exception.__suppress_context__)

    @patch(
        "apps.integrations.meta.client.requests.post",
        side_effect=requests.ConnectionError(
            "https://upload.example/reel?access_token="
            f"{PAGE_TOKEN_CANARY}"
        ),
    )
    def test_upload_network_failure_does_not_log_or_chain_upload_url(self, post):
        client = MetaAPIClient()

        with self.assertLogs("apps.integrations.meta.client", level="ERROR") as logs:
            with self.assertRaises(MetaAPIError) as raised:
                client.upload_reel_video(
                    "https://upload.example/reel?access_token=URL_TOKEN_CANARY",
                    access_token=PAGE_TOKEN_CANARY,
                    video_file=b"video",
                    file_size=5,
                )

        output = "\n".join(logs.output)
        self.assertIn("Meta Reel video upload failed", output)
        self.assertNotIn(PAGE_TOKEN_CANARY, output)
        self.assertNotIn("URL_TOKEN_CANARY", output)
        self.assertIsNone(raised.exception.__cause__)
        self.assertTrue(raised.exception.__suppress_context__)


class MetaPagesResponseDiagnosticsTests(SimpleTestCase):
    def make_service(self, response=None, http_status_code=200, error=None):
        service = MetaAccountDiscoveryService(access_token=ACCESS_TOKEN_CANARY)
        service.client = MetaAPIClient()
        service.client.get_current_user = lambda **kwargs: {"id": "meta-user-1"}

        def fake_get(
            path,
            *,
            access_token,
            params=None,
            return_http_status=False,
            response_metadata=None,
        ):
            if error is not None:
                raise error
            if return_http_status:
                return response, http_status_code
            return response

        service.client.get = fake_get
        return service

    @override_settings(
        META_BUSINESS_LOGIN_CONFIG_ID="diagnostic-config-id",
        META_GRAPH_API_VERSION="v-test",
    )
    def test_explicit_empty_data_is_distinguished_and_safe(self):
        service = self.make_service({"data": [], "paging": {}})

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            result = service.discover_accounts(correlation_id="correlation-empty")

        output = "\n".join(logs.output)
        self.assertIn("correlation_id=correlation-empty", output)
        self.assertIn("config_id=diagnostic-config-id", output)
        self.assertIn("http_status_code=200", output)
        self.assertIn("graph_api_version=v-test", output)
        self.assertIn("requested_field_names=", output)
        self.assertIn("data_present=True data_type=list parsed_page_count=0", output)
        self.assertIn("paging_present=True paging_next_present=False", output)
        self.assertIn("response_case=explicitly_empty_data", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)
        self.assertEqual(result.accounts, [])

    def test_missing_data_key_is_distinguished_from_empty_data(self):
        service = self.make_service({"error": {"message": OAUTH_CODE_CANARY}})

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-missing")

        output = "\n".join(logs.output)
        self.assertIn("data_present=False data_type=missing parsed_page_count=0", output)
        self.assertIn("response_case=missing_data_key", output)
        self.assertNotIn(OAUTH_CODE_CANARY, output)

    def test_unexpected_data_structure_is_logged_without_changing_error(self):
        service = self.make_service({"data": {"id": "page-1"}})

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-shape")

        output = "\n".join(logs.output)
        self.assertIn("data_present=True data_type=dict parsed_page_count=None", output)
        self.assertIn("response_case=unexpected_response_structure", output)

    def test_additional_pages_are_indicated_without_logging_next_url(self):
        next_url = (
            "https://graph.example/next?after=CURSOR_CANARY&access_token="
            f"{PAGE_TOKEN_CANARY}&code={OAUTH_CODE_CANARY}"
        )
        service = self.make_service()
        responses = [
            {
                "data": [
                    {"id": "page-1", "name": "Page One", "access_token": PAGE_TOKEN_CANARY}
                ],
                "paging": {"next": next_url, "cursors": {"after": "cursor-1"}},
            },
            {
                "data": [
                    {"id": "page-2", "name": "Page Two", "access_token": "page-token-2"}
                ],
                "paging": {},
            },
        ]
        page_calls = []

        def get_page_response(path, *, access_token, params=None, return_http_status=False, response_metadata=None):
            page_calls.append(params or {})
            response = responses[len(page_calls) - 1]
            return (response, 200) if return_http_status else response

        service.client.get = get_page_response

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            result = service.discover_accounts(correlation_id="correlation-next")

        output = "\n".join(logs.output)
        self.assertEqual(len(result.accounts), 2)
        self.assertEqual(page_calls[0]["fields"], "id,name,access_token,instagram_business_account")
        self.assertEqual(page_calls[1]["after"], "cursor-1")
        self.assertIn("response_case=response_contains_additional_pages", output)
        self.assertIn("paging_present=True paging_next_present=True", output)
        for sensitive_value in (
            next_url,
            "CURSOR_CANARY",
            PAGE_TOKEN_CANARY,
            OAUTH_CODE_CANARY,
            ACCESS_TOKEN_CANARY,
        ):
            self.assertNotIn(sensitive_value, output)

    def test_pagination_failure_does_not_return_partial_page_results(self):
        client = MetaAPIClient()
        page_calls = []

        def get_page_response(path, *, access_token, params=None, return_http_status=False, response_metadata=None):
            page_calls.append(params or {})
            if len(page_calls) == 1:
                return (
                    {
                        "data": [{"id": "page-1"}],
                        "paging": {"next": "credential-bearing-url", "cursors": {"after": "cursor-1"}},
                    },
                    200,
                )
            raise MetaAPIError("Meta API request failed.", status_code=503)

        client.get = get_page_response
        metadata = {}
        with self.assertRaises(MetaAPIError):
            client.get_pages(access_token=ACCESS_TOKEN_CANARY, response_metadata=metadata)

        self.assertEqual(len(page_calls), 2)
        self.assertEqual(page_calls[1]["after"], "cursor-1")
        self.assertEqual(metadata["response_case"], "api_request_failure")
        self.assertNotIn("credential-bearing-url", str(metadata))

    def test_pagination_without_cursor_fails_closed(self):
        client = MetaAPIClient()
        client.get = lambda *args, **kwargs: (
            {"data": [{"id": "page-1"}], "paging": {"next": "provider-url"}},
            200,
        )
        with self.assertRaises(MetaAPIError):
            client.get_pages(access_token=ACCESS_TOKEN_CANARY)

    def test_repeated_pagination_cursor_fails_closed(self):
        client = MetaAPIClient()
        page_calls = []

        def get_page_response(path, *, access_token, params=None, return_http_status=False, response_metadata=None):
            page_calls.append(params or {})
            return (
                {
                    "data": [{"id": f"page-{len(page_calls)}"}],
                    "paging": {
                        "next": "provider-next-url",
                        "cursors": {"after": "repeated-cursor"},
                    },
                },
                200,
            )

        client.get = get_page_response
        with self.assertRaises(MetaAPIError):
            client.get_pages(access_token=ACCESS_TOKEN_CANARY)

        self.assertEqual(len(page_calls), 2)
        self.assertEqual(page_calls[1]["after"], "repeated-cursor")

    def test_pagination_stops_at_the_configured_response_bound(self):
        client = MetaAPIClient()
        page_calls = []

        def get_page_response(path, *, access_token, params=None, return_http_status=False, response_metadata=None):
            page_calls.append(params or {})
            return (
                {
                    "data": [],
                    "paging": {
                        "next": "provider-next-url",
                        "cursors": {"after": f"cursor-{len(page_calls)}"},
                    },
                },
                200,
            )

        client.get = get_page_response
        with self.assertRaises(MetaAPIError):
            client.get_pages(access_token=ACCESS_TOKEN_CANARY)

        self.assertEqual(len(page_calls), 100)

    def test_graph_api_failure_logs_only_status_and_error_numbers(self):
        error = MetaAPIError(
            f"provider echoed {ACCESS_TOKEN_CANARY} {APP_SECRET_CANARY}",
            status_code=403,
            error_payload={
                "error": {
                    "code": 200,
                    "error_subcode": 10,
                    "message": OAUTH_CODE_CANARY,
                }
            },
        )
        service = self.make_service(error=error)

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-failure")

        output = "\n".join(logs.output)
        self.assertIn("http_status_code=403", output)
        self.assertIn("graph_error_code=200 graph_error_subcode=10", output)
        self.assertIn("response_case=api_request_failure", output)
        for sensitive_value in (
            ACCESS_TOKEN_CANARY,
            APP_SECRET_CANARY,
            OAUTH_CODE_CANARY,
        ):
            self.assertNotIn(sensitive_value, output)

    def test_unexpected_request_exception_is_logged_without_exception_text(self):
        service = self.make_service(error=NameError(APP_SECRET_CANARY))

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            with self.assertRaises(NameError):
                service.discover_accounts(correlation_id="correlation-request-error")

        output = "\n".join(logs.output)
        self.assertIn("response_case=api_request_failure", output)
        self.assertIn("http_status_code=None", output)
        self.assertIn("graph_error_code=None graph_error_subcode=None", output)
        self.assertNotIn(APP_SECRET_CANARY, output)


class MetaOAuthDiagnosticsTests(SimpleTestCase):
    def make_discovery(self, pages):
        service = MetaAccountDiscoveryService(access_token=ACCESS_TOKEN_CANARY)
        service.client.get_current_user = lambda **kwargs: {"id": "meta-user-1"}

        def get_pages(*, response_metadata=None, **kwargs):
            if response_metadata is not None:
                response_metadata["response_case"] = (
                    "explicitly_empty_data" if not pages else "pages_returned"
                )
            return pages

        service.client.get_pages = get_pages
        return service

    def test_page_returned_with_access_token_is_kept_without_logging_token(self):
        service = self.make_discovery(
            [
                {
                    "id": "page-1",
                    "name": "Page One",
                    "access_token": PAGE_TOKEN_CANARY,
                }
            ]
        )

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            result = service.discover_accounts(correlation_id="correlation-1")

        self.assertEqual(len(result.accounts), 1)
        self.assertIn("outcome=kept", "\n".join(logs.output))
        self.assertIn("raw_page_count=1 usable_page_count=1", "\n".join(logs.output))
        self.assertNotIn(PAGE_TOKEN_CANARY, "\n".join(logs.output))
        self.assertNotIn(ACCESS_TOKEN_CANARY, "\n".join(logs.output))

    def test_page_returned_without_access_token_is_skipped(self):
        service = self.make_discovery(
            [{"id": "page-2", "name": "Page Two", "access_token": ""}]
        )

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            result = service.discover_accounts(correlation_id="correlation-2")

        output = "\n".join(logs.output)
        self.assertIn("page_access_token_present=False", output)
        self.assertIn("outcome=skipped_missing_page_token", output)
        self.assertEqual(result.accounts, [])

    def test_page_missing_id_is_skipped_and_only_token_presence_is_logged(self):
        service = self.make_discovery(
            [{"name": "Unidentified Page", "access_token": PAGE_TOKEN_CANARY}]
        )

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            result = service.discover_accounts(correlation_id="correlation-3")

        output = "\n".join(logs.output)
        self.assertIn("page_name=Unidentified Page", output)
        self.assertIn("page_access_token_present=True", output)
        self.assertIn("outcome=skipped_missing_id", output)
        self.assertNotIn(PAGE_TOKEN_CANARY, output)
        self.assertEqual(result.accounts, [])

    def test_invalid_page_entry_is_skipped(self):
        service = self.make_discovery([None])

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            result = service.discover_accounts(correlation_id="correlation-4")

        self.assertIn("outcome=skipped_invalid_entry", "\n".join(logs.output))
        self.assertEqual(result.accounts, [])

    def test_permissions_diagnostic_failure_is_non_fatal_and_redacted(self):
        service = MetaOAuthService()
        service.client.get_user_permissions = _raise_permissions_error
        service.client.diagnose_token = lambda **kwargs: {
            "is_valid": True,
            "expires_at": 123456,
            "data_access_expires_at": 234567,
            "scopes": ["pages_show_list", ACCESS_TOKEN_CANARY],
            "application": APP_SECRET_CANARY,
        }

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            service._log_token_diagnostics(
                access_token=ACCESS_TOKEN_CANARY,
                correlation_id="correlation-5",
            )

        output = "\n".join(logs.output)
        self.assertIn("diagnostic=permissions", output)
        self.assertIn("pages_show_list", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)
        self.assertNotIn(APP_SECRET_CANARY, output)

    def test_debug_token_diagnostic_failure_is_non_fatal_and_redacted(self):
        service = MetaOAuthService()
        service.client.get_user_permissions = lambda **kwargs: {
            "data": [
                {"permission": "pages_show_list", "status": "granted"},
                {
                    "permission": "pages_manage_posts",
                    "status": "declined",
                    "access_token": ACCESS_TOKEN_CANARY,
                },
            ],
            "token": ACCESS_TOKEN_CANARY,
        }
        service.client.diagnose_token = _raise_debug_token_error

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            service._log_token_diagnostics(
                access_token=ACCESS_TOKEN_CANARY,
                correlation_id="correlation-6",
            )

        output = "\n".join(logs.output)
        self.assertIn("pages_show_list", output)
        self.assertIn("'status': 'granted'", output)
        self.assertIn("diagnostic=debug_token", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)

    def test_token_diagnostics_log_validated_type_and_separate_expiry_metadata(self):
        service = MetaOAuthService()
        service.client.get_user_permissions = lambda **kwargs: {"data": []}
        service.client.diagnose_token = lambda **kwargs: {
            "type": "USER",
            "is_valid": True,
            "expires_at": 123456,
            "data_access_expires_at": 234567,
            "scopes": ["pages_show_list", "read_insights"],
            "access_token": ACCESS_TOKEN_CANARY,
            "app_secret": APP_SECRET_CANARY,
        }

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            service._log_token_diagnostics(
                access_token=ACCESS_TOKEN_CANARY,
                correlation_id="correlation-token-metadata",
            )

        output = "\n".join(logs.output)
        self.assertIn("token_type=USER is_valid=True", output)
        self.assertIn("expires_at=123456 data_access_expires_at=234567", output)
        self.assertIn("pages_show_list", output)
        self.assertIn("read_insights", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)
        self.assertNotIn(APP_SECRET_CANARY, output)

    def test_unrecognized_token_type_is_not_logged(self):
        service = MetaOAuthService()
        service.client.get_user_permissions = lambda **kwargs: {"data": []}
        service.client.diagnose_token = lambda **kwargs: {
            "type": f"USER {ACCESS_TOKEN_CANARY}",
            "is_valid": True,
        }

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            service._log_token_diagnostics(
                access_token=ACCESS_TOKEN_CANARY,
                correlation_id="correlation-token-type",
            )

        output = "\n".join(logs.output)
        self.assertIn("token_type=unknown", output)
        self.assertNotIn(ACCESS_TOKEN_CANARY, output)

    def test_graph_error_log_contains_only_status_and_error_codes(self):
        service = self.make_discovery([])
        error = MetaAPIError(
            f"provider echoed {ACCESS_TOKEN_CANARY} {APP_SECRET_CANARY}",
            status_code=400,
            error_payload={
                "error": {
                    "code": 190,
                    "error_subcode": 463,
                    "message": f"raw {OAUTH_CODE_CANARY} {PAGE_TOKEN_CANARY}",
                    "access_token": ACCESS_TOKEN_CANARY,
                }
            },
        )
        service.client.get_pages = lambda **kwargs: _raise(error)

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-7")

        output = "\n".join(logs.output)
        self.assertIn("http_status_code=400", output)
        self.assertIn("graph_error_code=190", output)
        self.assertIn("graph_error_subcode=463", output)
        for secret in (
            ACCESS_TOKEN_CANARY,
            PAGE_TOKEN_CANARY,
            APP_SECRET_CANARY,
            OAUTH_CODE_CANARY,
        ):
            self.assertNotIn(secret, output)
        self.assertNotIn("provider echoed", output)
        self.assertNotIn("raw ", output)

    @override_settings(
        META_APP_ID="app-id-canary",
        META_APP_SECRET=APP_SECRET_CANARY,
        META_OAUTH_REDIRECT_URI="https://backend.example/callback",
    )
    @patch(
        "apps.integrations.meta.client.requests.get",
        side_effect=requests.ConnectionError(
            f"{OAUTH_CODE_CANARY} {APP_SECRET_CANARY}"
        ),
    )
    def test_code_exchange_network_failure_does_not_log_credentials(self, get):
        client = MetaAPIClient()

        with self.assertLogs("apps.integrations.meta.client", level="ERROR") as logs:
            with self.assertRaises(MetaAPIError):
                client.exchange_code_for_access_token(code=OAUTH_CODE_CANARY)

        output = "\n".join(logs.output)
        self.assertIn("Meta OAuth token exchange request failed", output)
        for secret in (OAUTH_CODE_CANARY, APP_SECRET_CANARY):
            self.assertNotIn(secret, output)

    @override_settings(FRONTEND_URL="https://frontend.example")
    def test_oauth_error_redirect_and_logs_do_not_expose_credentials(self):
        factory = APIRequestFactory()
        request = factory.get(
            "/api/integrations/meta/callback/",
            {
                "code": OAUTH_CODE_CANARY,
                "state": "state-canary",
            },
        )
        organization = type("OrganizationStub", (), {"organization_id": "ORG000007"})()
        user = object()
        error = MetaAPIError(
            f"raw {ACCESS_TOKEN_CANARY} {APP_SECRET_CANARY} {OAUTH_CODE_CANARY}",
            status_code=400,
            error_payload={
                "error": {
                    "code": 190,
                    "error_subcode": 463,
                    "message": PAGE_TOKEN_CANARY,
                }
            },
        )

        with (
            patch(
                "apps.integrations.meta.views.validate_oauth_state",
                return_value={
                    "organization_id": "ORG000007",
                    "user_id": 7,
                    "action": "connect",
                },
            ),
            patch("apps.integrations.meta.views.Organization.objects.filter") as org_filter,
            patch("apps.integrations.meta.views.get_user_model") as get_user_model,
            patch.object(MetaOAuthService, "prepare_oauth", side_effect=error),
            self.assertLogs("apps.integrations.meta.views", level="WARNING") as logs,
        ):
            org_filter.return_value.first.return_value = organization
            get_user_model.return_value.objects.filter.return_value.first.return_value = user
            response = MetaOAuthCallbackAPIView.as_view()(request)

        location = response["Location"]
        log_output = "\n".join(logs.output)
        for secret in (
            ACCESS_TOKEN_CANARY,
            PAGE_TOKEN_CANARY,
            APP_SECRET_CANARY,
            OAUTH_CODE_CANARY,
        ):
            self.assertNotIn(secret, location)
            self.assertNotIn(secret, log_output)
        self.assertIn("Unable+to+connect+Facebook+Page", location)
        self.assertIn("graph_error_code=190", log_output)
        self.assertIn("graph_error_subcode=463", log_output)


def _raise_permissions_error(**kwargs):
    raise MetaAPIError(
        f"sensitive {ACCESS_TOKEN_CANARY} {APP_SECRET_CANARY}",
        status_code=403,
        error_payload={
            "error": {
                "code": 200,
                "error_subcode": 10,
                "message": OAUTH_CODE_CANARY,
            }
        },
    )


def _raise_debug_token_error(**kwargs):
    raise MetaAPIError(
        f"sensitive {ACCESS_TOKEN_CANARY} {APP_SECRET_CANARY}",
        status_code=400,
        error_payload={
            "error": {
                "code": 190,
                "error_subcode": 463,
                "message": OAUTH_CODE_CANARY,
            }
        },
    )


def _raise(error):
    raise error


class MetaOAuthMultiPageSelectionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="meta-multi-page-owner@example.test",
            password="unused-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            email="meta-multi-page-other@example.test",
            password="unused-test-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORGMULTI001",
            name="Meta Multi Page Test",
            slug="meta-multi-page-test",
            industry="Testing",
            created_by=self.user,
        )
        self.other_organization = Organization.objects.create(
            organization_id="ORGMULTI002",
            name="Meta Other Organization",
            slug="meta-other-organization",
            industry="Testing",
            created_by=self.other_user,
        )
        encrypt_patch = patch(
            "apps.integrations.meta.services.encrypt_token",
            side_effect=lambda value: f"encrypted::{value}",
        )
        decrypt_patch = patch(
            "apps.integrations.meta.services.decrypt_token",
            side_effect=lambda value: str(value).removeprefix("encrypted::"),
        )
        encrypt_patch.start()
        decrypt_patch.start()
        self.addCleanup(encrypt_patch.stop)
        self.addCleanup(decrypt_patch.stop)

    @staticmethod
    def page(page_id, name=None, token=None):
        return MetaAccountData(
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=name or page_id,
            access_token=token or f"page-token-{page_id}",
        )

    def make_session(self, pages=None):
        if pages is None:
            pages = [self.page("page-a"), self.page("page-b")]
        serialized_pages = json.dumps(MetaOAuthService._serialize_accounts(pages))
        return MetaOAuthSession.objects.create(
            organization=self.organization,
            user=self.user,
            provider_user_id="meta-user-multi",
            encrypted_access_token="encrypted::meta-user-token",
            encrypted_accounts=f"encrypted::{serialized_pages}",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def make_existing_page(
        self,
        page_id,
        *,
        account_status=SocialAccountStatus.CONNECTED,
        account_valid=True,
        page_credential_status=MetaCredentialStatus.ACTIVE,
        user_credential_status=MetaCredentialStatus.ACTIVE,
        connection_status=SocialConnectionStatus.ACTIVE,
        is_deleted=False,
        with_page_credential=True,
    ):
        connection = SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id=f"meta-user-{page_id}",
            status=connection_status,
        )
        MetaAccountCredential.objects.create(
            social_connection=connection,
            credential_type=MetaCredentialType.USER,
            access_token="encrypted::meta-user-token",
            status=user_credential_status,
            provider_expiry_state=MetaProviderExpiryState.FINITE,
            provider_is_valid=True,
            provider_expires_at=timezone.now() + timedelta(days=30),
            data_access_expires_at=timezone.now() + timedelta(days=20),
        )
        account = SocialAccount.objects.create(
            organization=self.organization,
            connection=connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=page_id,
            status=account_status,
            is_valid=account_valid,
            is_deleted=is_deleted,
            deleted_at=timezone.now() if is_deleted else None,
        )
        if with_page_credential:
            MetaAccountCredential.objects.create(
                social_account=account,
                credential_type=MetaCredentialType.PAGE,
                access_token="encrypted::page-token",
                status=page_credential_status,
            )
        return account

    @override_settings(
        META_APP_ID="test-app-id",
        META_APP_SECRET="test-app-secret",
        META_OAUTH_REDIRECT_URI="https://example.test/meta/callback",
    )
    def test_one_eligible_page_still_creates_selection_session(self):
        service = MetaOAuthService()
        service.client.exchange_code_for_access_token = lambda **kwargs: {
            "access_token": "meta-user-token"
        }
        service._log_token_diagnostics = lambda **kwargs: None
        discovery = MetaDiscoveryResult(
            provider_user_id="meta-user-one",
            accounts=[self.page("only-page")],
        )

        with patch(
            "apps.integrations.meta.services.MetaAccountDiscoveryService"
        ) as discovery_service:
            discovery_service.return_value.discover_accounts.return_value = discovery
            with patch.object(service, "create_selection_session", return_value="session") as create_session:
                result = service.prepare_oauth(
                    code="oauth-code",
                    organization=self.organization,
                    user=self.user,
                )

        self.assertEqual(result["status"], "selection_required")
        self.assertEqual(result["session"], "session")
        create_session.assert_called_once()
        self.assertFalse(SocialAccount.objects.filter(organization=self.organization).exists())

    @override_settings(
        META_APP_ID="test-app-id",
        META_APP_SECRET="test-app-secret",
        META_OAUTH_REDIRECT_URI="https://example.test/meta/callback",
    )
    def test_zero_eligible_pages_create_an_empty_selection_session(self):
        service = MetaOAuthService()
        service.client.exchange_code_for_access_token = lambda **kwargs: {
            "access_token": "meta-user-token"
        }
        service._log_token_diagnostics = lambda **kwargs: None
        discovery = MetaDiscoveryResult(provider_user_id="meta-user-empty", accounts=[])

        with patch(
            "apps.integrations.meta.services.MetaAccountDiscoveryService"
        ) as discovery_service:
            discovery_service.return_value.discover_accounts.return_value = discovery
            result = service.prepare_oauth(
                code="oauth-code",
                organization=self.organization,
                user=self.user,
            )

        self.assertEqual(result["status"], "selection_required")
        self.assertEqual(result["session"].organization_id, self.organization.pk)
        self.assertEqual(result["session"].user_id, self.user.id)
        selection = service.get_selection_data(
            session=result["session"],
            organization=self.organization,
            user=self.user,
        )
        self.assertEqual(selection["pages"], [])
        with self.assertRaises(MetaAPIError):
            service.confirm_selection(
                session=result["session"],
                organization=self.organization,
                user=self.user,
                page_id="unselected-page",
            )
        self.assertFalse(SocialAccount.objects.filter(organization=self.organization).exists())

    def test_no_eligible_pages_return_empty_selection_data(self):
        session = self.make_session([])

        selection = MetaOAuthService().get_selection_data(
            session=session,
            organization=self.organization,
            user=self.user,
        )

        self.assertEqual(selection["pages"], [])

    def test_selection_marks_only_healthy_connected_pages_as_connected(self):
        self.make_existing_page("active-page")
        self.make_existing_page(
            "disconnected-page",
            account_status=SocialAccountStatus.DISCONNECTED,
            account_valid=False,
            page_credential_status=MetaCredentialStatus.REVOKED,
        )
        self.make_existing_page(
            "revoked-page",
            page_credential_status=MetaCredentialStatus.REVOKED,
        )
        self.make_existing_page(
            "invalid-page",
            page_credential_status=MetaCredentialStatus.INVALID,
        )
        self.make_existing_page("deleted-page", is_deleted=True)
        self.make_existing_page(
            "parent-revoked-page",
            user_credential_status=MetaCredentialStatus.REVOKED,
        )
        self.make_existing_page(
            "connection-revoked-page",
            connection_status=SocialConnectionStatus.REVOKED,
        )
        self.make_existing_page("missing-credential-page", with_page_credential=False)

        page_ids = [
            "active-page",
            "disconnected-page",
            "revoked-page",
            "invalid-page",
            "deleted-page",
            "parent-revoked-page",
            "connection-revoked-page",
            "missing-credential-page",
        ]
        session = self.make_session([self.page(page_id) for page_id in page_ids])

        selection = MetaOAuthService().get_selection_data(
            session=session,
            organization=self.organization,
            user=self.user,
        )

        connected = {page["id"] for page in selection["pages"] if page["connected"]}
        self.assertEqual(connected, {"active-page"})

    def test_user_expiry_states_gate_page_connection_selection(self):
        account = self.make_existing_page("expiry-state-page")
        user_credential = MetaAccountCredential.objects.get(
            social_connection=account.connection,
            credential_type=MetaCredentialType.USER,
        )
        now = timezone.now()

        def connected_page_ids():
            return MetaOAuthService._get_connected_page_ids(
                organization=self.organization,
                page_ids=["expiry-state-page"],
            )

        self.assertEqual(connected_page_ids(), {"expiry-state-page"})
        self.assertEqual(
            get_meta_connection_credential(social_connection=account.connection).pk,
            user_credential.pk,
        )

        MetaAccountCredential.objects.filter(pk=user_credential.pk).update(
            provider_expiry_state=MetaProviderExpiryState.NO_FINITE_EXPIRY,
            provider_is_valid=True,
            provider_expires_at=None,
            data_access_expires_at=now + timedelta(days=2),
        )
        self.assertEqual(connected_page_ids(), {"expiry-state-page"})

        MetaAccountCredential.objects.filter(pk=user_credential.pk).update(
            provider_is_valid=None,
        )
        self.assertEqual(connected_page_ids(), set())

        MetaAccountCredential.objects.filter(pk=user_credential.pk).update(
            provider_expiry_state=MetaProviderExpiryState.UNKNOWN,
            provider_is_valid=True,
            provider_expires_at=now + timedelta(days=2),
        )
        self.assertEqual(connected_page_ids(), set())
        user_credential.refresh_from_db()
        self.assertEqual(user_credential.status, MetaCredentialStatus.ACTIVE)
        self.assertFalse(user_credential.is_deleted)
        self.assertIsNone(
            get_meta_connection_credential(social_connection=account.connection)
        )

        MetaAccountCredential.objects.filter(pk=user_credential.pk).update(
            provider_expiry_state=MetaProviderExpiryState.FINITE,
            provider_expires_at=now - timedelta(seconds=1),
            data_access_expires_at=now + timedelta(days=2),
        )
        self.assertEqual(connected_page_ids(), set())

        MetaAccountCredential.objects.filter(pk=user_credential.pk).update(
            provider_expires_at=now + timedelta(days=2),
            data_access_expires_at=now - timedelta(seconds=1),
        )
        self.assertEqual(connected_page_ids(), set())

        # The associated PAGE credential has token_expires_at=NULL; preserve
        # the legacy behavior that treats that PAGE token as usable.
        MetaAccountCredential.objects.filter(pk=user_credential.pk).update(
            provider_expiry_state=MetaProviderExpiryState.FINITE,
            provider_expires_at=now + timedelta(days=2),
            data_access_expires_at=now + timedelta(days=2),
        )
        self.assertEqual(connected_page_ids(), {"expiry-state-page"})

    def test_disconnected_page_reconnect_reuses_existing_account(self):
        account = self.make_existing_page(
            "page-reconnect",
            account_status=SocialAccountStatus.DISCONNECTED,
            account_valid=False,
            page_credential_status=MetaCredentialStatus.REVOKED,
        )
        session = self.make_session([self.page("page-reconnect")])
        service = MetaOAuthService()
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="facebook-page",
            subject_id=account.pk,
            platform="facebook",
            account_name=account.account_name,
        )
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="meta-connection",
            subject_id=account.connection_id,
            platform="facebook",
        )

        before = service.get_selection_data(
            session=session,
            organization=self.organization,
            user=self.user,
        )
        self.assertFalse(before["pages"][0]["connected"])

        health_api = MagicMock()
        health_api.diagnose_token.return_value = {
            "type": "USER",
            "is_valid": True,
            "expires_at": int((timezone.now() + timedelta(days=30)).timestamp()),
            "data_access_expires_at": int(
                (timezone.now() + timedelta(days=20)).timestamp()
            ),
        }
        health_api.get_user_permissions.return_value = {
            "data": [{"permission": "pages_show_list", "status": "granted"}]
        }
        with (
            patch(
                "apps.integrations.meta.lifecycle.MetaAPIClient",
                return_value=health_api,
            ),
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-reconnect-user-token",
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            result = service.confirm_selection(
                session=session,
                organization=self.organization,
                user=self.user,
                page_id="page-reconnect",
            )

        account.refresh_from_db()
        self.assertFalse(result["already_connected"])
        self.assertEqual(result["accounts"][0].id, account.id)
        self.assertEqual(account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(account.is_valid)
        self.assertEqual(
            UserNotification.objects.filter(
                organization=self.organization,
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
                resolved_at__isnull=True,
            ).count(),
            0,
        )
        self.assertEqual(
            account.meta_credential.status,
            MetaCredentialStatus.ACTIVE,
        )
        user_credential = MetaAccountCredential.objects.get(
            social_connection__provider_user_id="meta-user-multi",
            credential_type=MetaCredentialType.USER,
        )
        self.assertEqual(user_credential.provider_token_type, "USER")
        self.assertTrue(user_credential.provider_is_valid)
        self.assertIsNotNone(user_credential.provider_expires_at)
        self.assertIsNotNone(user_credential.data_access_expires_at)
        self.assertIsNotNone(user_credential.last_health_check_at)
        reconnected_credential = MetaAccountCredential.objects.get(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
        )
        self.assertEqual(
            reconnected_credential.access_token,
            "encrypted::page-token-page-reconnect",
        )
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=self.organization,
                platform=SocialPlatform.FACEBOOK,
                platform_account_id="page-reconnect",
            ).count(),
            1,
        )

        repeated = service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-reconnect",
        )
        self.assertTrue(repeated["already_connected"])
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=self.organization,
                platform=SocialPlatform.FACEBOOK,
                platform_account_id="page-reconnect",
                is_deleted=False,
            ).count(),
            1,
        )

    def test_initial_page_selection_persists_user_debug_metadata(self):
        session = self.make_session([self.page("page-health")])
        service = MetaOAuthService()
        provider_expiry = timezone.now() + timedelta(days=30)
        data_access_expiry = timezone.now() + timedelta(days=24)
        health_api = MagicMock()
        health_api.diagnose_token.return_value = {
            "type": "SYSTEM_USER",
            "is_valid": True,
            "expires_at": int(provider_expiry.timestamp()),
            "data_access_expires_at": int(data_access_expiry.timestamp()),
        }
        health_api.get_user_permissions.return_value = {
            "data": [{"permission": "pages_show_list", "status": "granted"}]
        }

        with (
            patch(
                "apps.integrations.meta.lifecycle.MetaAPIClient",
                return_value=health_api,
            ),
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-initial-user-token",
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            service.confirm_selection(
                session=session,
                organization=self.organization,
                user=self.user,
                page_id="page-health",
            )

        user_credential = MetaAccountCredential.objects.get(
            social_connection__provider_user_id="meta-user-multi",
            credential_type=MetaCredentialType.USER,
        )
        self.assertIsNone(user_credential.token_expires_at)
        self.assertEqual(user_credential.provider_token_type, "SYSTEM_USER")
        self.assertTrue(user_credential.provider_is_valid)
        self.assertAlmostEqual(
            user_credential.provider_expires_at.timestamp(),
            int(provider_expiry.timestamp()),
            delta=1,
        )
        self.assertAlmostEqual(
            user_credential.data_access_expires_at.timestamp(),
            int(data_access_expiry.timestamp()),
            delta=1,
        )
        self.assertIsNotNone(user_credential.last_health_check_at)
        self.assertEqual(
            user_credential.granted_permissions,
            [{"permission": "pages_show_list", "status": "granted"}],
        )

    def test_soft_deleted_page_is_not_connected_and_is_restored_on_add(self):
        account = self.make_existing_page("page-restore", is_deleted=True)
        session = self.make_session([self.page("page-restore")])
        service = MetaOAuthService()

        selection = service.get_selection_data(
            session=session,
            organization=self.organization,
            user=self.user,
        )
        self.assertFalse(selection["pages"][0]["connected"])

        result = service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-restore",
        )

        account.refresh_from_db()
        self.assertFalse(result["already_connected"])
        self.assertEqual(result["accounts"][0].id, account.id)
        self.assertFalse(account.is_deleted)
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=self.organization,
                platform=SocialPlatform.FACEBOOK,
                platform_account_id="page-restore",
            ).count(),
            1,
        )

    def test_page_a_and_page_b_can_be_added_before_finishing(self):
        session = self.make_session()
        service = MetaOAuthService()

        first = service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-a",
        )
        session.refresh_from_db()
        self.assertIsNone(session.consumed_at)

        second = service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-b",
        )
        self.assertFalse(first["already_connected"])
        self.assertFalse(second["already_connected"])
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=self.organization,
                platform=SocialPlatform.FACEBOOK,
                is_deleted=False,
            ).count(),
            2,
        )

        selection = service.get_selection_data(
            session=session,
            organization=self.organization,
            user=self.user,
        )
        self.assertEqual([page["id"] for page in selection["pages"]], ["page-a", "page-b"])
        self.assertTrue(all(page["connected"] for page in selection["pages"]))

    def test_repeated_addition_returns_connected_without_duplicate(self):
        session = self.make_session([self.page("page-a")])
        service = MetaOAuthService()
        service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-a",
        )

        repeated = service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-a",
        )

        self.assertTrue(repeated["already_connected"])
        self.assertEqual(
            SocialAccount.objects.filter(
                organization=self.organization,
                platform_account_id="page-a",
                is_deleted=False,
            ).count(),
            1,
        )

    def test_finish_consumes_session_and_later_add_is_rejected(self):
        session = self.make_session()
        service = MetaOAuthService()
        service.finish_selection(
            session=session,
            organization=self.organization,
            user=self.user,
        )
        session.refresh_from_db()
        self.assertIsNotNone(session.consumed_at)

        with self.assertRaises(MetaAPIError):
            service.confirm_selection(
                session=session,
                organization=self.organization,
                user=self.user,
                page_id="page-a",
            )

    def test_finish_endpoint_consumes_session_for_authenticated_owner(self):
        session = self.make_session()
        request = APIRequestFactory().post(
            "/meta/oauth/selection/finish/",
            {
                "selection_key": str(session.selection_key),
                "organization_id": self.organization.organization_id,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = MetaOAuthSelectionFinishAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertIsNotNone(session.consumed_at)

    def test_finish_endpoint_reports_expired_or_consumed_sessions_as_gone(self):
        expired = self.make_session()
        expired.expires_at = timezone.now() - timedelta(seconds=1)
        expired.save(update_fields=["expires_at"])

        consumed = self.make_session()
        consumed.consumed_at = timezone.now()
        consumed.save(update_fields=["consumed_at"])

        for session, expected_code in (
            (expired, "selection_session_expired"),
            (consumed, "selection_session_consumed"),
        ):
            request = APIRequestFactory().post(
                "/meta/oauth/selection/finish/",
                {
                    "selection_key": str(session.selection_key),
                    "organization_id": self.organization.organization_id,
                },
                format="json",
            )
            force_authenticate(request, user=self.user)

            with self.subTest(code=expected_code):
                response = MetaOAuthSelectionFinishAPIView.as_view()(request)

            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.data["code"], expected_code)

    def test_invalid_page_wrong_user_and_wrong_organization_are_rejected(self):
        session = self.make_session()
        service = MetaOAuthService()

        for kwargs in (
            {"organization": self.organization, "user": self.user, "page_id": "outside-page"},
            {"organization": self.organization, "user": self.other_user, "page_id": "page-a"},
            {"organization": self.other_organization, "user": self.user, "page_id": "page-a"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(MetaAPIError):
                service.confirm_selection(session=session, **kwargs)

        self.assertFalse(SocialAccount.objects.filter(organization=self.organization).exists())

    def test_expired_and_consumed_sessions_are_rejected(self):
        service = MetaOAuthService()
        expired = self.make_session([self.page("page-expired")])
        expired.expires_at = timezone.now() - timedelta(seconds=1)
        expired.save(update_fields=["expires_at"])
        with self.assertRaises(MetaAPIError):
            service.confirm_selection(
                session=expired,
                organization=self.organization,
                user=self.user,
                page_id="page-expired",
            )

        consumed = self.make_session([self.page("page-consumed")])
        consumed.consumed_at = timezone.now()
        consumed.save(update_fields=["consumed_at"])
        with self.assertRaises(MetaAPIError):
            service.confirm_selection(
                session=consumed,
                organization=self.organization,
                user=self.user,
                page_id="page-consumed",
            )

    def test_failed_addition_leaves_page_unconnected_and_session_retryable(self):
        session = self.make_session([self.page("page-retry")])
        service = MetaOAuthService()

        with patch.object(
            MetaSocialAccountService,
            "sync_connection_and_accounts",
            side_effect=MetaAPIError("provider failure"),
        ):
            with self.assertRaises(MetaAPIError):
                service.confirm_selection(
                    session=session,
                    organization=self.organization,
                    user=self.user,
                    page_id="page-retry",
                )

        session.refresh_from_db()
        self.assertIsNone(session.consumed_at)
        self.assertFalse(SocialAccount.objects.filter(organization=self.organization).exists())

        result = service.confirm_selection(
            session=session,
            organization=self.organization,
            user=self.user,
            page_id="page-retry",
        )
        self.assertFalse(result["already_connected"])


class MetaSocialConnectionConcurrentCreateTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="meta-connection-race@example.test",
            password="unused-test-password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORGMETARACE001",
            name="Meta Connection Race",
            slug="meta-connection-race",
            industry="Testing",
            created_by=self.user,
        )

    def test_concurrent_same_provider_connection_reuses_unique_winner(self):
        if connection.vendor != "postgresql":
            self.skipTest("This race test requires PostgreSQL unique-index behavior.")

        barrier = Barrier(2)
        original_create = SocialConnection.objects.create

        def synchronized_create(**kwargs):
            barrier.wait(timeout=10)
            return original_create(**kwargs)

        def get_or_create_connection():
            close_old_connections()
            try:
                with transaction.atomic():
                    service = MetaSocialAccountService(
                        organization=self.organization,
                        user=self.user,
                    )
                    return service._get_or_create_connection(
                        provider_user_id="same-meta-user",
                    ).pk
            finally:
                close_old_connections()

        with patch.object(SocialConnection.objects, "create", side_effect=synchronized_create):
            with ThreadPoolExecutor(max_workers=2) as executor:
                connection_ids = list(executor.map(lambda _: get_or_create_connection(), range(2)))

        self.assertEqual(connection_ids[0], connection_ids[1])
        self.assertEqual(
            SocialConnection.objects.filter(
                organization=self.organization,
                provider=SocialConnectionProvider.META,
                provider_user_id="same-meta-user",
                is_deleted=False,
            ).count(),
            1,
        )

    def test_unrelated_integrity_error_is_not_treated_as_a_connection_race(self):
        if connection.vendor != "postgresql":
            self.skipTest("This test inspects PostgreSQL integrity-error handling.")

        service = MetaSocialAccountService(
            organization=self.organization,
            user=self.user,
        )
        with patch.object(
            SocialConnection.objects,
            "create",
            side_effect=IntegrityError("unrelated database constraint"),
        ):
            with transaction.atomic(), self.assertRaises(IntegrityError):
                service._get_or_create_connection(provider_user_id="same-meta-user")


class MetaPageSelectionErrorResponseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="meta-selection-error-test@example.test",
            password="unused-test-password",
        )

    def _stub_selection_lookups(self):
        organization_query = patch(
            "apps.integrations.meta.views.Organization.objects.filter",
        )
        session_query = patch(
            "apps.integrations.meta.views.MetaOAuthSession.objects.filter",
        )
        organization_mock = organization_query.start()
        session_mock = session_query.start()
        self.addCleanup(organization_query.stop)
        self.addCleanup(session_query.stop)
        organization_mock.return_value.first.return_value = object()
        session_mock.return_value.first.return_value = object()

    def test_page_list_endpoint_hides_raw_provider_exception_text(self):
        self._stub_selection_lookups()
        request = APIRequestFactory().get(
            "/meta/pages/selection/",
            {"selection_key": "selection-test", "organization_id": "ORGTEST001"},
        )
        force_authenticate(request, user=self.user)
        provider_error = MetaAPIError("provider echoed sensitive-canary")

        with patch(
            "apps.integrations.meta.views.MetaOAuthService.get_selection_data",
            side_effect=provider_error,
        ):
            response = MetaOAuthSelectionAPIView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Unable to load Facebook Pages.")
        self.assertNotIn("sensitive-canary", response.data["message"])

    def test_page_confirm_endpoint_hides_raw_provider_exception_text(self):
        self._stub_selection_lookups()
        request = APIRequestFactory().post(
            "/meta/pages/selection/confirm/",
            {
                "selection_key": "selection-test",
                "organization_id": "ORGTEST001",
                "page_id": "page-test",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        provider_error = MetaAPIError("provider echoed sensitive-canary")

        with patch(
            "apps.integrations.meta.views.MetaOAuthService.confirm_selection",
            side_effect=provider_error,
        ):
            response = MetaOAuthSelectionConfirmAPIView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Unable to connect Facebook Page.")
        self.assertNotIn("sensitive-canary", response.data["message"])


class MetaParentCredentialLifecycleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="meta-lifecycle-test@example.test",
            password="unused-test-password",
            first_name="Meta Test",
        )
        self.organization = Organization.objects.create(
            organization_id="ORGTEST001",
            name="Meta Lifecycle Test",
            slug="meta-lifecycle-test",
            industry="Testing",
            created_by=self.user,
        )
        self.connection = SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id="provider-user-test",
        )
        self.parent = MetaAccountCredential.objects.create(
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="encrypted-parent-placeholder",
            token_expires_at=timezone.now() + timedelta(days=4),
            status=MetaCredentialStatus.ACTIVE,
        )
        self.page_credentials = [self.create_page("page-1", "Test Page 1")]
        self.api = MetaAPIClient()
        self.api.diagnose_token = lambda **kwargs: {
            "type": "USER",
            "is_valid": True,
            "expires_at": int((timezone.now() + timedelta(days=10)).timestamp()),
            "data_access_expires_at": int((timezone.now() + timedelta(days=10)).timestamp()),
        }
        self.api.get_user_permissions = lambda **kwargs: {
            "data": [{"permission": "pages_show_list", "status": "granted"}]
        }
        self.service = MetaTokenLifecycleService(api_client=self.api)
        self.service._acquire_lock = lambda credential_id: "test-lock"
        self.service._release_lock = lambda *args: None
        self.service._validate_page_token = lambda **kwargs: {"id": "page-1"}

    def create_page(self, page_id, name):
        account = SocialAccount.objects.create(
            organization=self.organization,
            connection=self.connection,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=page_id,
            account_name=name,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        return MetaAccountCredential.objects.create(
            social_account=account,
            credential_type=MetaCredentialType.PAGE,
            access_token=f"encrypted-{page_id}-placeholder",
            token_expires_at=timezone.now() + timedelta(days=2),
            status=MetaCredentialStatus.ACTIVE,
        )

    def run_lifecycle(self):
        with patch(
            "apps.integrations.meta.lifecycle.decrypt_token",
            return_value="PARENT_TOKEN_CANARY_DO_NOT_LOG",
        ):
            return self.service.refresh_due_credentials()

    def save_user_credential_with_health_check(
        self,
        *,
        connection,
        user_access_token,
        token_expires_at,
        debug_response=None,
        permissions_response=None,
        debug_error=None,
    ):
        social_service = MetaSocialAccountService(
            organization=self.organization,
            user=self.user,
        )
        self.api.diagnose_token = MagicMock(
            return_value=debug_response,
            side_effect=debug_error,
        )
        self.api.get_user_permissions = MagicMock(
            return_value=permissions_response
        )

        with (
            patch(
                "apps.integrations.meta.services.encrypt_token",
                return_value="encrypted-new-user-token",
            ),
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-user-token-for-test",
            ),
            patch(
                "apps.integrations.meta.lifecycle.MetaAPIClient",
                return_value=self.api,
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            with transaction.atomic():
                credential = social_service._save_user_credential(
                    connection=connection,
                    user_access_token=user_access_token,
                    token_expires_at=token_expires_at,
                )

        credential.refresh_from_db()
        return credential

    def test_page_lock_release_atomically_deletes_only_its_own_lock(self):
        from django.core.cache import cache

        class FakeRedisClient:
            def __init__(self):
                self.values = {}
                self.eval_calls = []

            def eval(self, script, key_count, key, expected_value):
                self.script = script
                self.key_count = key_count
                stored_value_before = self.values.get(key)
                deleted = stored_value_before == expected_value
                self.eval_calls.append(
                    {
                        "script": script,
                        "key_count": key_count,
                        "key": key,
                        "serialized_owner_token": expected_value,
                        "stored_value_before": stored_value_before,
                        "deleted": deleted,
                    }
                )
                if deleted:
                    del self.values[key]
                    return 1
                return 0

        redis_client = FakeRedisClient()
        lock_key = cache.make_key("meta:page-token-lifecycle:page-1")
        expected_owner = cache._cache._serializer.dumps("owner-a")
        other_owner = cache._cache._serializer.dumps("owner-b")
        redis_client.values[lock_key] = other_owner
        release_lock = MetaTokenLifecycleService._release_lock.__get__(
            self.service,
            type(self.service),
        )

        with (
            patch(
                "apps.integrations.meta.lifecycle.cache._cache.get_client",
                return_value=redis_client,
            ),
            patch("apps.integrations.meta.lifecycle.logger.error") as release_error_log,
        ):
            release_lock("page-1", "owner-a")
            self.assertEqual(redis_client.values[lock_key], other_owner)

            redis_client.values[lock_key] = expected_owner
            release_lock("page-1", "owner-a")

        self.assertFalse(release_error_log.called, release_error_log.call_args_list)
        self.assertEqual(
            [
                (
                    call["key"],
                    call["serialized_owner_token"],
                    call["stored_value_before"],
                    call["deleted"],
                )
                for call in redis_client.eval_calls
            ],
            [
                (lock_key, expected_owner, other_owner, False),
                (lock_key, expected_owner, expected_owner, True),
            ],
        )
        self.assertEqual(len(redis_client.eval_calls), 2)
        self.assertNotIn(lock_key, redis_client.values)
        self.assertEqual(redis_client.key_count, 1)
        self.assertIn("redis.call('GET'", redis_client.script)
        self.assertIn("redis.call('DEL'", redis_client.script)

    def test_shared_parent_is_health_checked_once_for_multiple_pages(self):
        self.page_credentials.append(self.create_page("page-2", "Test Page 2"))
        with (
            patch.object(self.api, "diagnose_token", wraps=self.api.diagnose_token) as debug,
            patch.object(
                self.service,
                "_get_parent_user_credential",
                wraps=self.service._get_parent_user_credential,
            ) as parent_lookup,
            patch.object(
                self.service,
                "process_page_credential",
                wraps=self.service.process_page_credential,
            ) as page_refresh,
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="token-canary"),
        ):
            result = self.service.refresh_due_credentials()
        self.assertEqual(debug.call_count, 1)
        self.assertEqual(parent_lookup.call_count, 2)
        self.assertEqual(page_refresh.call_count, 2)
        self.assertEqual(result["parent_checked"], 1)
        self.assertEqual(result["valid"], 3)
        self.assertEqual(result["checked"], 3)

    def test_valid_parent_records_provider_health_without_changing_legacy_expiry(self):
        old_expiry = self.parent.token_expires_at
        result = self.run_lifecycle()
        self.parent.refresh_from_db()
        self.assertEqual(result["parent_valid"], 1)
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(self.parent.provider_token_type, "USER")
        self.assertTrue(self.parent.provider_is_valid)
        self.assertIsNotNone(self.parent.provider_expires_at)
        self.assertIsNotNone(self.parent.data_access_expires_at)
        self.assertIsNotNone(self.parent.last_health_check_at)
        self.assertEqual(self.parent.granted_permissions, [
            {"permission": "pages_show_list", "status": "granted"}
        ])
        self.assertEqual(self.parent.token_expires_at, old_expiry)

    def test_invalid_parent_requires_reconnect_without_invalidating_page(self):
        self.page_credentials.append(self.create_page("page-2", "Test Page 2"))
        self.parent.provider_token_type = "USER"
        self.parent.provider_is_valid = True
        self.parent.provider_expiry_state = MetaProviderExpiryState.FINITE
        self.parent.provider_expires_at = timezone.now() + timedelta(days=10)
        self.parent.data_access_expires_at = timezone.now() + timedelta(days=10)
        self.parent.save(
            update_fields=[
                "provider_token_type",
                "provider_is_valid",
                "provider_expiry_state",
                "provider_expires_at",
                "data_access_expires_at",
            ]
        )
        self.api.diagnose_token = lambda **kwargs: {"type": "USER", "is_valid": False}
        result = self.run_lifecycle()
        self.parent.refresh_from_db()
        self.connection.refresh_from_db()
        self.page_credentials[0].refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.INVALID)
        self.assertEqual(self.connection.status, SocialConnectionStatus.ACTIVE)
        self.assertEqual(self.page_credentials[0].status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(result["reconnect_needed"], 1)
        self.assertTrue(
            SocialAccountLifecycleStatus.needs_reconnect(
                social_account=self.page_credentials[0].social_account,
                credential_status=MetaCredentialStatus.ACTIVE.lower(),
            )
        )
        notice = UserNotification.objects.get(
            organization=self.organization,
            event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
        )
        self.assertEqual(
            notice.event_key,
            f"social-reconnect:meta-connection:{self.connection.pk}",
        )
        self.assertIn("shared Meta connection", notice.message)
        self.assertEqual(
            UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED
            ).count(),
            1,
        )
        self.run_lifecycle()
        self.assertEqual(
            UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED
            ).count(),
            1,
        )
        self.assertFalse(
            UserNotification.objects.filter(
                event_key__startswith="social-reconnect:facebook-page:"
            ).exists()
        )

    def test_permission_loss_sets_parent_reconnect_state_only(self):
        self.parent.granted_permissions = [
            {"permission": "pages_show_list", "status": "granted"},
            {"permission": "read_insights", "status": "granted"},
        ]
        self.parent.save(update_fields=["granted_permissions"])
        self.api.get_user_permissions = lambda **kwargs: {
            "data": [{"permission": "read_insights", "status": "granted"}]
        }
        self.run_lifecycle()
        self.parent.refresh_from_db()
        self.page_credentials[0].refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.ERROR)
        self.assertEqual(self.page_credentials[0].status, MetaCredentialStatus.ACTIVE)

    def test_optional_business_management_loss_does_not_require_reconnect(self):
        self.parent.granted_permissions = [
            {"permission": "pages_show_list", "status": "granted"},
            {"permission": "business_management", "status": "granted"},
        ]
        self.parent.save(update_fields=["granted_permissions"])
        self.api.get_user_permissions = lambda **kwargs: {
            "data": [{"permission": "pages_show_list", "status": "granted"}]
        }
        self.run_lifecycle()
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)

    def test_expired_data_access_is_tracked_separately(self):
        self.api.diagnose_token = lambda **kwargs: {
            "type": "USER",
            "is_valid": True,
            "expires_at": int((timezone.now() + timedelta(days=10)).timestamp()),
            "data_access_expires_at": int((timezone.now() - timedelta(minutes=1)).timestamp()),
        }
        legacy_expiry = self.parent.token_expires_at
        self.run_lifecycle()
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.EXPIRED)
        self.assertEqual(self.parent.token_expires_at, legacy_expiry)
        self.assertLess(self.parent.data_access_expires_at, timezone.now())

    def test_transient_parent_error_does_not_invalidate_or_clear_health(self):
        self.parent.granted_permissions = [{"permission": "pages_show_list", "status": "granted"}]
        self.parent.save(update_fields=["granted_permissions"])
        for status_code in (429, 503, None):
            with self.subTest(status_code=status_code):
                self.api.diagnose_token = lambda **kwargs: _raise(
                    MetaAPIError("temporary failure", status_code=status_code)
                )
                result = self.run_lifecycle()
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(self.parent.granted_permissions, [
            {"permission": "pages_show_list", "status": "granted"}
        ])
        self.assertEqual(result["parent_retry"], 1)
        self.assertFalse(
            UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED
            ).exists()
        )

    def test_page_invalidation_notification_is_deduplicated_and_page_scoped(self):
        credential = self.page_credentials[0]
        self.service._mark_page_invalid(credential_id=credential.pk)
        self.service._mark_page_invalid(credential_id=credential.pk)

        notice = UserNotification.objects.get(
            event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
        )
        self.assertEqual(
            notice.event_key,
            f"social-reconnect:facebook-page:{credential.social_account_id}",
        )
        self.assertIn("Test Page 1", notice.message)
        self.assertEqual(
            UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED
            ).count(),
            1,
        )

    def test_page_recovery_resolves_page_notice_but_retains_shared_notice(self):
        credential = self.page_credentials[0]
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="facebook-page",
            subject_id=credential.social_account_id,
            platform="facebook",
            account_name="Test Page 1",
        )
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="meta-connection",
            subject_id=self.connection.pk,
            platform="facebook",
        )
        with patch(
            "apps.integrations.meta.lifecycle.encrypt_token",
            return_value="encrypted-new-page",
        ):
            self.service._save_verified_page_token(
                credential_id=credential.pk,
                page_access_token="synthetic-new-page-token",
            )

        notices = {
            notice.event_key: notice
            for notice in UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED
            )
        }
        page_notice = notices[
            f"social-reconnect:facebook-page:{credential.social_account_id}"
        ]
        shared_notice = notices[
            f"social-reconnect:meta-connection:{self.connection.pk}"
        ]
        self.assertIsNotNone(page_notice.resolved_at)
        self.assertIsNone(shared_notice.resolved_at)

    def test_invalid_parent_and_valid_page_resolve_only_page_notice(self):
        credential = self.page_credentials[0]
        self.parent.status = MetaCredentialStatus.INVALID
        self.parent.save(update_fields=["status"])
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="facebook-page",
            subject_id=credential.social_account_id,
            platform="facebook",
            account_name="Test Page 1",
        )
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="meta-connection",
            subject_id=self.connection.pk,
            platform="facebook",
        )

        with patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="page-token"):
            outcome = self.service.process_page_credential(credential)

        credential.refresh_from_db()
        credential.social_account.refresh_from_db()
        self.parent.refresh_from_db()
        notices = {
            notice.event_key: notice
            for notice in UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
            )
        }
        page_notice = notices[
            f"social-reconnect:facebook-page:{credential.social_account_id}"
        ]
        parent_notice = notices[
            f"social-reconnect:meta-connection:{self.connection.pk}"
        ]

        self.assertEqual(outcome, "verified")
        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(credential.social_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(credential.social_account.is_valid)
        self.assertEqual(self.parent.status, MetaCredentialStatus.INVALID)
        self.assertIsNotNone(page_notice.resolved_at)
        self.assertIsNone(parent_notice.resolved_at)

    def test_invalid_parent_and_rejected_page_invalidate_only_that_page(self):
        self.parent.status = MetaCredentialStatus.INVALID
        self.parent.save(update_fields=["status"])
        credential = self.page_credentials[0]
        sibling = self.create_page("page-sibling", "Sibling Page")
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="meta-connection",
            subject_id=self.connection.pk,
            platform="facebook",
        )
        auth_error = MetaAPIError(
            "Synthetic Page authentication rejection",
            status_code=400,
            error_payload={"error": {"code": 190}},
        )

        def validate_page(*, page_id, page_access_token):
            if page_id == "page-1":
                raise auth_error
            return {"id": page_id}

        self.service._validate_page_token = validate_page
        with patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="page-token"):
            result = self.service.refresh_due_credentials()

        credential.refresh_from_db()
        credential.social_account.refresh_from_db()
        sibling.refresh_from_db()
        sibling.social_account.refresh_from_db()
        self.parent.refresh_from_db()
        notices = {
            notice.event_key: notice
            for notice in UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
            )
        }

        self.assertEqual(result["invalid"], 2)
        self.assertEqual(result["reconnect_needed"], 1)
        self.assertEqual(credential.status, MetaCredentialStatus.INVALID)
        self.assertEqual(credential.access_token, "encrypted-page-1-placeholder")
        self.assertEqual(credential.social_account.status, SocialAccountStatus.ERROR)
        self.assertFalse(credential.social_account.is_valid)
        self.assertEqual(sibling.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(sibling.access_token, "encrypted-page-sibling-placeholder")
        self.assertEqual(sibling.social_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(sibling.social_account.is_valid)
        self.assertEqual(self.parent.status, MetaCredentialStatus.INVALID)
        self.assertIsNone(
            notices[
                f"social-reconnect:facebook-page:{credential.social_account_id}"
            ].resolved_at
        )
        self.assertIsNone(
            notices[f"social-reconnect:meta-connection:{self.connection.pk}"].resolved_at
        )
        self.assertEqual(len(notices), 2)

    def test_active_parent_successful_recovery_does_not_create_transient_notice(self):
        credential = self.page_credentials[0]
        auth_error = MetaAPIError(
            "Synthetic Page authentication rejection",
            status_code=400,
            error_payload={"error": {"code": 190}},
        )
        validation_results = [auth_error, {"id": "page-1"}]

        def validate_page(**kwargs):
            result = validation_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        self.service._validate_page_token = validate_page
        self.service._reissue_page_token = lambda **kwargs: "replacement-page-token"
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="meta-connection",
            subject_id=self.connection.pk,
            platform="facebook",
        )

        with (
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="old-page-token"),
            patch("apps.integrations.meta.lifecycle.encrypt_token", return_value="encrypted-replacement-page"),
            patch.object(self.service, "_get_parent_user_credential", return_value=self.parent),
        ):
            outcome = self.service.process_page_credential(credential)

        credential.refresh_from_db()
        credential.social_account.refresh_from_db()
        self.parent.refresh_from_db()
        self.assertEqual(outcome, "refreshed")
        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(credential.access_token, "encrypted-replacement-page")
        self.assertEqual(credential.social_account.status, SocialAccountStatus.CONNECTED)
        self.assertTrue(credential.social_account.is_valid)
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        page_notice = UserNotification.objects.filter(
            event_key=f"social-reconnect:facebook-page:{credential.social_account_id}",
            is_deleted=False,
        ).first()
        parent_notice = UserNotification.objects.get(
            event_key=f"social-reconnect:meta-connection:{self.connection.pk}",
            is_deleted=False,
        )
        self.assertIsNone(page_notice)
        self.assertIsNone(parent_notice.resolved_at)

    def test_active_parent_failed_page_recovery_invalidates_only_page(self):
        credential = self.page_credentials[0]
        auth_error = MetaAPIError(
            "Synthetic Page authentication rejection",
            status_code=400,
            error_payload={"error": {"code": 190}},
        )
        validation_results = [auth_error, auth_error]

        def validate_page(**kwargs):
            result = validation_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        self.service._validate_page_token = validate_page
        self.service._reissue_page_token = lambda **kwargs: "rejected-replacement-token"
        with (
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="page-token"),
            patch.object(self.service, "_get_parent_user_credential", return_value=self.parent),
        ):
            outcome = self.service.process_page_credential(credential)

        credential.refresh_from_db()
        credential.social_account.refresh_from_db()
        self.parent.refresh_from_db()
        notice = UserNotification.objects.get(
            event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
            event_key=f"social-reconnect:facebook-page:{credential.social_account_id}",
        )
        self.assertEqual(outcome, "invalid")
        self.assertEqual(credential.status, MetaCredentialStatus.INVALID)
        self.assertEqual(credential.social_account.status, SocialAccountStatus.ERROR)
        self.assertFalse(credential.social_account.is_valid)
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(
            notice.event_key,
            f"social-reconnect:facebook-page:{credential.social_account_id}",
        )

    def test_transient_page_validation_errors_do_not_invalidate_or_recover(self):
        credential = self.page_credentials[0]
        temporary_errors = (
            MetaAPIError("Synthetic rate limit", status_code=429),
            MetaAPIError("Synthetic server error", status_code=503),
            MetaAPIError("Synthetic timeout/network error"),
        )

        for error in temporary_errors:
            with self.subTest(error=error.message if hasattr(error, "message") else str(error)):
                self.service._validate_page_token = lambda **kwargs: _raise(error)
                with (
                    patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="page-token"),
                    patch.object(self.service, "_reissue_page_token") as reissue,
                ):
                    outcome = self.service.process_page_credential(credential)
                credential.refresh_from_db()
                credential.social_account.refresh_from_db()
                self.assertEqual(outcome, "retry")
                self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
                self.assertEqual(credential.social_account.status, SocialAccountStatus.CONNECTED)
                self.assertTrue(credential.social_account.is_valid)
                reissue.assert_not_called()

        self.assertFalse(
            UserNotification.objects.filter(
                event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
            ).exists()
        )

    def test_stale_parent_health_check_cannot_overwrite_reconnected_credential(self):
        replacement_verified_at = timezone.now() + timedelta(seconds=1)

        def reconnect_during_diagnostic(**kwargs):
            MetaAccountCredential.objects.filter(pk=self.parent.pk).update(
                access_token="encrypted-replacement-placeholder",
                status=MetaCredentialStatus.ACTIVE,
                provider_token_type="",
                provider_is_valid=None,
                provider_expires_at=None,
                data_access_expires_at=None,
                last_health_check_at=None,
                granted_permissions=[],
                last_verified_at=replacement_verified_at,
                updated_at=replacement_verified_at,
            )
            return {
                "type": "USER",
                "is_valid": True,
                "expires_at": int((timezone.now() + timedelta(days=10)).timestamp()),
                "data_access_expires_at": int(
                    (timezone.now() + timedelta(days=10)).timestamp()
                ),
            }

        self.api.diagnose_token = reconnect_during_diagnostic
        with (
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="old-token"),
            patch.object(self.api, "get_user_permissions") as get_permissions,
        ):
            outcome = self.service._check_parent_user_credential(self.parent)

        self.parent.refresh_from_db()
        self.assertEqual(outcome, "retry")
        self.assertEqual(self.parent.access_token, "encrypted-replacement-placeholder")
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(self.parent.provider_token_type, "")
        self.assertIsNone(self.parent.provider_is_valid)
        self.assertIsNone(self.parent.provider_expires_at)
        self.assertIsNone(self.parent.data_access_expires_at)
        self.assertIsNone(self.parent.last_health_check_at)
        self.assertEqual(self.parent.granted_permissions, [])
        get_permissions.assert_not_called()

    def test_permission_snapshot_excludes_credential_shaped_names(self):
        self.api.get_user_permissions = lambda **kwargs: {
            "data": [
                {"permission": "tokenvalue123", "status": "granted"},
                {"permission": "pages_show_list", "status": "granted"},
            ]
        }
        with patch(
            "apps.integrations.meta.lifecycle.decrypt_token",
            return_value="tokenvalue123",
        ):
            self.service._check_parent_user_credential(self.parent)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.granted_permissions, [
            {"permission": "pages_show_list", "status": "granted"}
        ])

    def test_invalid_parent_and_rejected_page_are_invalidated_without_recovery(self):
        self.parent.status = MetaCredentialStatus.INVALID
        self.parent.save(update_fields=["status"])
        record_social_credential_reconnect_required(
            organization=self.organization,
            scope="meta-connection",
            subject_id=self.connection.pk,
            platform="facebook",
        )
        self.service._validate_page_token = lambda **kwargs: _raise(
            MetaAPIError(
                "invalid page token",
                status_code=400,
                error_payload={"error": {"code": 190}},
            )
        )
        with (
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="token-canary"),
            patch.object(self.service, "_save_verified_page_token") as save_token,
        ):
            outcome = self.service.process_page_credential(self.page_credentials[0])
        self.assertEqual(outcome, "invalid")
        save_token.assert_not_called()
        self.page_credentials[0].refresh_from_db()
        self.page_credentials[0].social_account.refresh_from_db()
        self.assertEqual(self.page_credentials[0].status, MetaCredentialStatus.INVALID)
        self.assertEqual(
            self.page_credentials[0].social_account.status,
            SocialAccountStatus.ERROR,
        )
        notice = UserNotification.objects.get(
            event_type=UserNotificationType.SOCIAL_ACCOUNT_RECONNECT_REQUIRED,
            event_key=f"social-reconnect:facebook-page:{self.page_credentials[0].social_account_id}",
        )
        self.assertEqual(
            notice.event_key,
            f"social-reconnect:facebook-page:{self.page_credentials[0].social_account_id}",
        )
        self.assertIsNone(notice.resolved_at)
        self.assertTrue(
            UserNotification.objects.filter(
                event_key=f"social-reconnect:meta-connection:{self.connection.pk}",
                resolved_at__isnull=True,
                is_deleted=False,
            ).exists()
        )

    def test_parent_permission_diagnostic_transient_failure_preserves_state(self):
        self.parent.granted_permissions = [{"permission": "pages_show_list", "status": "granted"}]
        self.parent.save(update_fields=["granted_permissions"])
        self.api.get_user_permissions = lambda **kwargs: _raise(
            MetaAPIError("rate limited", status_code=429)
        )
        result = self.run_lifecycle()
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(result["parent_retry"], 1)

    def test_duplicate_user_selection_is_deterministic(self):
        lower_id, higher_id = sorted([uuid.uuid4(), uuid.uuid4()])
        created = timezone.now()
        older = MetaAccountCredential.objects.create(
            id=lower_id,
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="older-placeholder",
        )
        newer = MetaAccountCredential.objects.create(
            id=higher_id,
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="newer-placeholder",
        )
        MetaAccountCredential.objects.filter(
            id__in=[lower_id, higher_id],
        ).update(created_at=created)
        self.assertEqual(
            get_meta_connection_credential(social_connection=self.connection).id,
            higher_id,
        )
        self.assertNotEqual(older.id, newer.id)

    def test_active_user_credential_wins_over_newer_revoked_duplicate(self):
        revoked = MetaAccountCredential.objects.create(
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="newer-revoked-placeholder",
            status=MetaCredentialStatus.REVOKED,
        )
        errored = MetaAccountCredential.objects.create(
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="newer-error-placeholder",
            status=MetaCredentialStatus.ERROR,
        )
        MetaAccountCredential.objects.filter(pk=revoked.pk).update(
            created_at=timezone.now() + timedelta(seconds=1),
        )
        MetaAccountCredential.objects.filter(pk=errored.pk).update(
            created_at=timezone.now() + timedelta(seconds=2),
        )

        self.assertEqual(
            get_meta_connection_credential(social_connection=self.connection).pk,
            self.parent.pk,
        )
        self.assertEqual(
            self.service._get_parent_user_credential(
                page_credential=self.page_credentials[0],
            ).pk,
            self.parent.pk,
        )

        service = MetaSocialAccountService(
            organization=self.organization,
            user=self.user,
        )
        with patch(
            "apps.integrations.meta.services.encrypt_token",
            return_value="encrypted-replacement-placeholder",
        ):
            updated = service._save_user_credential(
                connection=self.connection,
                user_access_token="replacement-placeholder",
                token_expires_at=None,
            )

        self.assertEqual(updated.pk, self.parent.pk)
        revoked.refresh_from_db()
        errored.refresh_from_db()
        self.assertEqual(revoked.status, MetaCredentialStatus.REVOKED)
        self.assertEqual(revoked.access_token, "newer-revoked-placeholder")
        self.assertEqual(errored.status, MetaCredentialStatus.ERROR)
        self.assertEqual(errored.access_token, "newer-error-placeholder")

    def test_save_user_credential_updates_selected_active_duplicate(self):
        self.parent.is_deleted = True
        self.parent.deleted_at = timezone.now()
        self.parent.save(update_fields=["is_deleted", "deleted_at"])

        lower_id, higher_id = sorted([uuid.uuid4(), uuid.uuid4()])
        created = timezone.now()
        older = MetaAccountCredential.objects.create(
            id=lower_id,
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="older-placeholder",
        )
        selected = MetaAccountCredential.objects.create(
            id=higher_id,
            social_connection=self.connection,
            credential_type=MetaCredentialType.USER,
            access_token="selected-placeholder",
        )
        MetaAccountCredential.objects.filter(
            id__in=[lower_id, higher_id],
        ).update(created_at=created)

        service = MetaSocialAccountService(
            organization=self.organization,
            user=self.user,
        )
        new_expiry = timezone.now() + timedelta(days=12)
        with patch(
            "apps.integrations.meta.services.encrypt_token",
            return_value="encrypted-replacement-token",
        ) as encrypt:
            result = service._save_user_credential(
                connection=self.connection,
                user_access_token="replacement-token",
                token_expires_at=new_expiry,
            )

        self.assertEqual(result.pk, higher_id)
        self.assertEqual(
            MetaAccountCredential.objects.filter(
                social_connection=self.connection,
                credential_type=MetaCredentialType.USER,
                is_deleted=False,
            ).count(),
            2,
        )
        older.refresh_from_db()
        selected.refresh_from_db()
        self.assertEqual(older.access_token, "older-placeholder")
        self.assertEqual(selected.access_token, "encrypted-replacement-token")
        self.assertEqual(selected.token_expires_at, new_expiry)
        encrypt.assert_called_once_with("replacement-token")

    def test_save_user_credential_creates_new_when_only_deleted_exists(self):
        deleted_token = self.parent.access_token
        self.parent.is_deleted = True
        self.parent.deleted_at = timezone.now()
        self.parent.save(update_fields=["is_deleted", "deleted_at"])

        service = MetaSocialAccountService(
            organization=self.organization,
            user=self.user,
        )
        with patch(
            "apps.integrations.meta.services.encrypt_token",
            return_value="encrypted-replacement-token",
        ):
            result = service._save_user_credential(
                connection=self.connection,
                user_access_token="replacement-token",
                token_expires_at=None,
            )

        self.parent.refresh_from_db()
        self.assertNotEqual(result.pk, self.parent.pk)
        self.assertFalse(result.is_deleted)
        self.assertEqual(result.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(result.access_token, "encrypted-replacement-token")
        self.assertTrue(self.parent.is_deleted)
        self.assertIsNotNone(self.parent.deleted_at)
        self.assertEqual(self.parent.access_token, deleted_token)

    def test_save_user_credential_preserves_health_until_new_check_finishes(self):
        previous_expiry = self.parent.token_expires_at
        previous_verified_at = timezone.now() - timedelta(days=2)
        previous_provider_expiry = timezone.now() + timedelta(days=20)
        previous_data_access_expiry = timezone.now() + timedelta(days=15)
        previous_health_check = timezone.now() - timedelta(days=1)
        self.parent.last_verified_at = previous_verified_at
        self.parent.provider_token_type = "USER"
        self.parent.provider_is_valid = True
        self.parent.provider_expires_at = previous_provider_expiry
        self.parent.data_access_expires_at = previous_data_access_expiry
        self.parent.last_health_check_at = previous_health_check
        self.parent.granted_permissions = [
            {"permission": "pages_show_list", "status": "granted"}
        ]
        self.parent.status = MetaCredentialStatus.INVALID
        self.parent.save()

        new_expiry = timezone.now() + timedelta(days=30)
        service = MetaSocialAccountService(
            organization=self.organization,
            user=self.user,
        )
        with patch(
            "apps.integrations.meta.services.encrypt_token",
            return_value="encrypted-replacement-token",
        ):
            result = service._save_user_credential(
                connection=self.connection,
                user_access_token="replacement-token",
                token_expires_at=new_expiry,
            )

        result.refresh_from_db()
        self.assertEqual(result.access_token, "encrypted-replacement-token")
        self.assertEqual(result.token_expires_at, new_expiry)
        self.assertNotEqual(result.token_expires_at, previous_expiry)
        self.assertEqual(result.status, MetaCredentialStatus.ACTIVE)
        self.assertGreater(result.last_verified_at, previous_verified_at)
        self.assertEqual(result.provider_token_type, "USER")
        self.assertTrue(result.provider_is_valid)
        self.assertEqual(result.provider_expires_at, previous_provider_expiry)
        self.assertEqual(result.data_access_expires_at, previous_data_access_expiry)
        self.assertEqual(result.last_health_check_at, previous_health_check)
        self.assertEqual(
            result.granted_permissions,
            [{"permission": "pages_show_list", "status": "granted"}],
        )

    def test_new_user_credential_persists_successful_debug_metadata(self):
        connection = SocialConnection.objects.create(
            organization=self.organization,
            provider=SocialConnectionProvider.META,
            provider_user_id="provider-user-new-oauth",
        )
        data_access_expiry = timezone.now() + timedelta(days=25)
        credential = self.save_user_credential_with_health_check(
            connection=connection,
            user_access_token="synthetic-new-user-token",
            token_expires_at=None,
            debug_response={
                "type": "USER",
                "is_valid": True,
                "data_access_expires_at": int(data_access_expiry.timestamp()),
            },
            permissions_response={
                "data": [
                    {"permission": "pages_show_list", "status": "granted"}
                ]
            },
        )

        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertIsNone(credential.token_expires_at)
        self.assertEqual(credential.provider_token_type, "USER")
        self.assertTrue(credential.provider_is_valid)
        self.assertIsNone(credential.provider_expires_at)
        self.assertAlmostEqual(
            credential.data_access_expires_at.timestamp(),
            int(data_access_expiry.timestamp()),
            delta=1,
        )
        self.assertIsNotNone(credential.last_health_check_at)
        self.assertEqual(
            credential.granted_permissions,
            [{"permission": "pages_show_list", "status": "granted"}],
        )

    def test_reconnected_user_credential_persists_new_debug_metadata(self):
        prior_provider_expiry = timezone.now() + timedelta(days=1)
        self.parent.provider_token_type = "USER"
        self.parent.provider_is_valid = True
        self.parent.provider_expires_at = prior_provider_expiry
        self.parent.data_access_expires_at = prior_provider_expiry
        self.parent.last_health_check_at = timezone.now() - timedelta(days=1)
        self.parent.granted_permissions = [
            {"permission": "pages_show_list", "status": "granted"}
        ]
        self.parent.save()

        new_token_expiry = timezone.now() + timedelta(days=30)
        provider_expiry = timezone.now() + timedelta(days=40)
        data_access_expiry = timezone.now() + timedelta(days=35)
        credential = self.save_user_credential_with_health_check(
            connection=self.connection,
            user_access_token="synthetic-reconnected-user-token",
            token_expires_at=new_token_expiry,
            debug_response={
                "type": "SYSTEM_USER",
                "is_valid": True,
                "expires_at": int(provider_expiry.timestamp()),
                "data_access_expires_at": int(data_access_expiry.timestamp()),
            },
            permissions_response={
                "data": [
                    {"permission": "pages_show_list", "status": "granted"}
                ]
            },
        )

        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(credential.token_expires_at, new_token_expiry)
        self.assertEqual(credential.provider_token_type, "SYSTEM_USER")
        self.assertTrue(credential.provider_is_valid)
        self.assertNotEqual(credential.provider_expires_at, prior_provider_expiry)
        self.assertNotEqual(
            credential.data_access_expires_at,
            prior_provider_expiry,
        )
        self.assertNotEqual(
            credential.token_expires_at,
            credential.data_access_expires_at,
        )
        self.assertIsNotNone(credential.last_health_check_at)

    def test_temporary_debug_token_failure_preserves_oauth_and_prior_metadata(self):
        self.parent.provider_token_type = "USER"
        self.parent.provider_is_valid = True
        self.parent.provider_expires_at = timezone.now() + timedelta(days=12)
        self.parent.data_access_expires_at = timezone.now() + timedelta(days=9)
        self.parent.last_health_check_at = timezone.now() - timedelta(days=1)
        self.parent.save()
        previous_provider_expiry = self.parent.provider_expires_at
        previous_data_access_expiry = self.parent.data_access_expires_at

        with self.assertLogs(
            "apps.integrations.meta.lifecycle",
            level="WARNING",
        ) as logs:
            credential = self.save_user_credential_with_health_check(
                connection=self.connection,
                user_access_token="synthetic-temporary-failure-token",
                token_expires_at=None,
                debug_error=MetaAPIError("temporary diagnostic failure", status_code=503),
            )

        output = "\n".join(logs.output)
        self.assertNotIn("synthetic-user-token-for-test", output)
        self.assertNotIn("synthetic-temporary-failure-token", output)
        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertIsNone(credential.token_expires_at)
        self.assertEqual(credential.provider_token_type, "USER")
        self.assertTrue(credential.provider_is_valid)
        self.assertEqual(credential.provider_expires_at, previous_provider_expiry)
        self.assertEqual(
            credential.data_access_expires_at,
            previous_data_access_expiry,
        )

    def test_incomplete_debug_token_response_does_not_invalidate_or_clear_metadata(self):
        self.parent.provider_token_type = "USER"
        self.parent.provider_is_valid = True
        self.parent.provider_expires_at = timezone.now() + timedelta(days=12)
        self.parent.data_access_expires_at = timezone.now() + timedelta(days=9)
        self.parent.save()
        previous_provider_expiry = self.parent.provider_expires_at
        previous_data_access_expiry = self.parent.data_access_expires_at

        credential = self.save_user_credential_with_health_check(
            connection=self.connection,
            user_access_token="synthetic-incomplete-diagnostic-token",
            token_expires_at=None,
            debug_response={"type": "USER"},
            permissions_response=None,
        )

        self.assertEqual(credential.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(credential.provider_token_type, "USER")
        self.assertTrue(credential.provider_is_valid)
        self.assertEqual(credential.provider_expires_at, previous_provider_expiry)
        self.assertEqual(
            credential.data_access_expires_at,
            previous_data_access_expiry,
        )

    def test_missing_oauth_expires_in_stays_null_and_missing_provider_expiry_stays_null(self):
        self.assertIsNone(MetaOAuthService._get_token_expiry({}))
        self.assertIsNone(MetaOAuthService._get_token_expiry({"expires_in": 0}))
        self.assertIsNone(
            MetaOAuthService._get_token_expiry({"expires_in": "invalid"})
        )

        legacy_expiry = self.parent.token_expires_at
        self.api.diagnose_token = lambda **kwargs: {
            "type": "USER",
            "is_valid": True,
            "data_access_expires_at": int(
                (timezone.now() + timedelta(days=18)).timestamp()
            ),
        }
        with patch(
            "apps.integrations.meta.lifecycle.decrypt_token",
            return_value="synthetic-user-token-for-test",
        ):
            outcome = self.service.check_user_credential_health_after_oauth(
                self.parent.pk,
            )

        self.parent.refresh_from_db()
        self.assertEqual(outcome, "valid")
        self.assertIsNone(self.parent.provider_expires_at)
        self.assertIsNotNone(self.parent.data_access_expires_at)
        self.assertEqual(self.parent.token_expires_at, legacy_expiry)

    def test_page_recovery_remains_available_with_healthy_parent(self):
        validation_results = [
            MetaAPIError(
                "invalid page token",
                status_code=400,
                error_payload={"error": {"code": 190}},
            ),
            {"id": "page-1"},
        ]

        def validate(**kwargs):
            outcome = validation_results.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        self.service._validate_page_token = validate
        with (
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="token-canary"),
            patch.object(
                self.service,
                "_reissue_page_token",
                return_value="replacement-page-token",
            ),
            patch.object(self.service, "_save_verified_page_token") as save_token,
        ):
            result = self.run_lifecycle()
        self.assertEqual(result["refreshed"], 1)
        save_token.assert_called_once()


class MetaTokenMaintenanceTaskTests(TestCase):
    def test_instagram_and_meta_maintenance_schedules_are_hourly(self):
        self.assertEqual(
            settings.CELERY_BEAT_SCHEDULE["maintain-instagram-tokens"]["schedule"],
            3600.0,
        )
        self.assertEqual(
            settings.CELERY_BEAT_SCHEDULE["maintain-meta-tokens"]["schedule"],
            3600.0,
        )

    def test_run_record_creation_failure_is_terminal_and_safe(self):
        from apps.integrations.meta.tasks import (
            MetaTokenMaintenanceRunPersistenceError,
            maintain_meta_tokens_task,
        )

        with (
            patch(
                "apps.integrations.meta.tasks.MetaTokenMaintenanceRun.objects.create",
                side_effect=RuntimeError("sensitive persistence detail"),
            ),
            patch(
                "apps.integrations.meta.tasks.MetaTokenLifecycleService.refresh_due_credentials",
            ) as refresh,
            self.assertLogs("apps.integrations.meta.tasks", level="ERROR") as logs,
        ):
            with self.assertRaises(MetaTokenMaintenanceRunPersistenceError):
                maintain_meta_tokens_task.run()

        refresh.assert_not_called()
        self.assertIn(MetaTokenMaintenanceRunPersistenceError,
                      maintain_meta_tokens_task.dont_autoretry_for)
        output = "\n".join(logs.output)
        self.assertIn("error_type=RuntimeError", output)
        self.assertNotIn("sensitive persistence detail", output)

    def test_run_record_finalization_failure_does_not_retry_maintenance(self):
        from apps.integrations.meta.tasks import (
            MetaTokenMaintenanceRunPersistenceError,
            maintain_meta_tokens_task,
        )

        original_save = MetaTokenMaintenanceRun.save

        def fail_run_update(instance, *args, **kwargs):
            if kwargs.get("update_fields"):
                raise RuntimeError("sensitive persistence detail")
            return original_save(instance, *args, **kwargs)

        with (
            patch(
                "apps.integrations.meta.tasks.MetaTokenLifecycleService.refresh_due_credentials",
                return_value={"checked": 0},
            ) as refresh,
            patch.object(MetaTokenMaintenanceRun, "save", autospec=True,
                         side_effect=fail_run_update),
            self.assertLogs("apps.integrations.meta.tasks", level="ERROR") as logs,
        ):
            with self.assertRaises(MetaTokenMaintenanceRunPersistenceError):
                maintain_meta_tokens_task.run()

        refresh.assert_called_once()
        self.assertEqual(
            MetaTokenMaintenanceRun.objects.get().outcome,
            MetaTokenMaintenanceRun.Outcome.RUNNING,
        )
        output = "\n".join(logs.output)
        self.assertIn("error_type=RuntimeError", output)
        self.assertNotIn("sensitive persistence detail", output)

    def test_partial_run_is_persisted_with_safe_counters_and_logs(self):
        from apps.integrations.meta.tasks import maintain_meta_tokens_task

        result = {
            "checked": 3,
            "verified": 2,
            "valid": 2,
            "invalid": 0,
            "retry": 1,
            "reconnect_needed": 0,
        }
        with (
            patch(
                "apps.integrations.meta.tasks.MetaTokenLifecycleService.refresh_due_credentials",
                return_value=result,
            ),
            self.assertLogs("apps.integrations.meta.tasks", level="INFO") as logs,
        ):
            task_result = maintain_meta_tokens_task.run()
        run = MetaTokenMaintenanceRun.objects.get(run_id=task_result["run_id"])
        self.assertEqual(run.outcome, MetaTokenMaintenanceRun.Outcome.PARTIAL)
        self.assertEqual((run.checked, run.valid, run.invalid, run.retry), (3, 2, 0, 1))
        output = "\n".join(logs.output)
        self.assertIn("outcome=PARTIAL", output)
        self.assertNotIn("PARENT_TOKEN_CANARY", output)
        self.assertNotIn("ACCESS_TOKEN_CANARY", output)
        self.assertNotIn("APP_SECRET_CANARY", output)
        self.assertNotIn("OAUTH_CODE_CANARY", output)
        for field in ("access_token", "app_secret", "oauth_code"):
            self.assertNotIn(field, [model_field.name for model_field in run._meta.fields])


class MetaUserRenewalTaskIntegrationTests(SimpleTestCase):
    def _run_task(self, *, enabled, service, logs=False):
        from apps.integrations.meta.tasks import maintain_meta_tokens_task

        run_record = SimpleNamespace(save=MagicMock())
        log_context = (
            self.assertLogs("apps.integrations.meta.tasks", level="INFO")
            if logs
            else nullcontext()
        )
        with (
            override_settings(META_USER_TOKEN_AUTO_RENEWAL_ENABLED=enabled),
            patch(
                "apps.integrations.meta.tasks.MetaTokenMaintenanceRun.objects.create",
                return_value=run_record,
            ),
            patch(
                "apps.integrations.meta.tasks.MetaTokenLifecycleService",
                return_value=service,
            ),
            log_context as captured_logs,
        ):
            task_result = maintain_meta_tokens_task.run()
        return task_result, run_record, captured_logs

    def test_disabled_flag_skips_user_renewal_and_preserves_page_result(self):
        service = MagicMock()
        page_result = {
            "checked": 2,
            "valid": 2,
            "invalid": 0,
            "retry": 0,
            "reconnect_needed": 0,
        }
        service.refresh_due_credentials.return_value = page_result

        task_result, _run_record, _logs = self._run_task(
            enabled=False,
            service=service,
        )

        service.renew_due_user_credentials.assert_not_called()
        service.refresh_due_credentials.assert_called_once_with()
        self.assertEqual(
            {key: task_result[key] for key in page_result},
            page_result,
        )
        self.assertEqual(
            task_result["user_renewal"],
            {"renewed": 0, "skipped": 0, "locked": 0, "stale": 0, "retry": 0},
        )

    def test_enabled_flag_runs_user_renewal_before_page_maintenance_and_reports_counts(self):
        service = MagicMock()
        execution_order = []
        service.renew_due_user_credentials.side_effect = lambda: (
            execution_order.append("user")
            or {"renewed": 2, "skipped": 3, "locked": 1, "stale": 1, "retry": 1}
        )
        service.refresh_due_credentials.side_effect = lambda: (
            execution_order.append("page")
            or {
                "checked": 4,
                "valid": 4,
                "invalid": 0,
                "retry": 0,
                "reconnect_needed": 0,
            }
        )

        task_result, run_record, logs = self._run_task(
            enabled=True,
            service=service,
            logs=True,
        )

        self.assertEqual(execution_order, ["user", "page"])
        self.assertEqual(
            task_result["user_renewal"],
            {"renewed": 2, "skipped": 3, "locked": 1, "stale": 1, "retry": 1},
        )
        self.assertEqual(task_result["retry"], 1)
        self.assertEqual(run_record.outcome, MetaTokenMaintenanceRun.Outcome.PARTIAL)
        output = "\n".join(logs.output)
        for count in (
            "user_renewal_enabled=True",
            "user_renewed=2",
            "user_skipped=3",
            "user_locked=1",
            "user_stale=1",
            "user_retry=1",
        ):
            self.assertIn(count, output)

    def test_user_and_page_counters_are_saved_to_maintenance_run_record(self):
        service = MagicMock()
        user_counts = {
            "renewed": 11,
            "skipped": 12,
            "locked": 13,
            "stale": 14,
            "retry": 5,
        }
        page_counts = {
            "checked": 23,
            "valid": 19,
            "invalid": 2,
            "retry": 7,
            "reconnect_needed": 3,
        }
        service.renew_due_user_credentials.return_value = user_counts
        service.refresh_due_credentials.return_value = page_counts

        task_result, run_record, _logs = self._run_task(
            enabled=True,
            service=service,
        )

        self.assertEqual(
            {
                "user_renewed": run_record.user_renewed,
                "user_skipped": run_record.user_skipped,
                "user_locked": run_record.user_locked,
                "user_stale": run_record.user_stale,
                "user_retry": run_record.user_retry,
            },
            {
                "user_renewed": 11,
                "user_skipped": 12,
                "user_locked": 13,
                "user_stale": 14,
                "user_retry": 5,
            },
        )
        self.assertEqual(
            {
                "checked": run_record.checked,
                "valid": run_record.valid,
                "invalid": run_record.invalid,
                "reconnect_needed": run_record.reconnect_needed,
            },
            {
                "checked": 23,
                "valid": 19,
                "invalid": 2,
                "reconnect_needed": 3,
            },
        )
        self.assertEqual(run_record.retry, 12)
        self.assertEqual(task_result["retry"], 12)

        run_record.save.assert_called_once()
        saved_fields = set(run_record.save.call_args.kwargs["update_fields"])
        self.assertTrue(
            {
                "user_renewed",
                "user_skipped",
                "user_locked",
                "user_stale",
                "user_retry",
            }.issubset(saved_fields)
        )
        self.assertTrue(
            {
                "checked",
                "valid",
                "invalid",
                "retry",
                "reconnect_needed",
            }.issubset(saved_fields)
        )

    def test_user_renewal_exception_does_not_block_page_maintenance_or_leak_details(self):
        service = MagicMock()
        service.renew_due_user_credentials.side_effect = RuntimeError(
            "synthetic secret-bearing provider detail"
        )
        service.refresh_due_credentials.return_value = {
            "checked": 1,
            "valid": 1,
            "invalid": 0,
            "retry": 0,
            "reconnect_needed": 0,
        }

        from apps.integrations.meta.tasks import maintain_meta_tokens_task

        run_record = SimpleNamespace(save=MagicMock())
        with (
            override_settings(META_USER_TOKEN_AUTO_RENEWAL_ENABLED=True),
            patch(
                "apps.integrations.meta.tasks.MetaTokenMaintenanceRun.objects.create",
                return_value=run_record,
            ),
            patch(
                "apps.integrations.meta.tasks.MetaTokenLifecycleService",
                return_value=service,
            ),
            self.assertLogs("apps.integrations.meta.tasks", level="WARNING") as logs,
        ):
            task_result = maintain_meta_tokens_task.run()

        service.refresh_due_credentials.assert_called_once_with()
        self.assertEqual(task_result["user_renewal"]["retry"], 1)
        self.assertEqual(task_result["retry"], 1)
        self.assertNotIn(
            "synthetic secret-bearing provider detail",
            "\n".join(logs.output),
        )

    def test_existing_hourly_schedule_and_celery_retry_configuration_remain(self):
        from apps.integrations.meta.tasks import (
            MetaTokenMaintenanceRunPersistenceError,
            maintain_meta_tokens_task,
        )

        self.assertEqual(
            settings.CELERY_BEAT_SCHEDULE["maintain-meta-tokens"]["schedule"],
            3600.0,
        )
        self.assertEqual(maintain_meta_tokens_task.autoretry_for, (Exception,))
        self.assertIn(
            MetaTokenMaintenanceRunPersistenceError,
            maintain_meta_tokens_task.dont_autoretry_for,
        )
        self.assertTrue(maintain_meta_tokens_task.retry_backoff)
        self.assertEqual(maintain_meta_tokens_task.retry_kwargs["max_retries"], 3)


@override_settings(
    META_APP_ID="meta-test-app-id",
    META_APP_SECRET=APP_SECRET_CANARY,
)
class MetaUserTokenExchangeClientTests(SimpleTestCase):
    def setUp(self):
        self.client = MetaAPIClient()
        self.source_token = "SYNTHETIC_SOURCE_USER_TOKEN_CANARY"
        self.exchanged_token = "SYNTHETIC_EXCHANGED_USER_TOKEN_CANARY"
        self.valid_diagnostics = {
            "app_id": "meta-test-app-id",
            "type": "USER",
            "is_valid": True,
            "expires_at": int((timezone.now() + timedelta(days=30)).timestamp()),
            "data_access_expires_at": int(
                (timezone.now() + timedelta(days=20)).timestamp()
            ),
        }
        self.valid_permissions = {
            "data": [{"permission": "pages_show_list", "status": "granted"}]
        }

    def _mock_exchange_response(self, payload, *, ok=True, status_code=200):
        response = MagicMock()
        response.ok = ok
        response.status_code = status_code
        response.json.return_value = payload
        return response

    @staticmethod
    def _exchange_diagnostics(logs):
        return [record.meta_user_token_exchange for record in logs.records]

    def test_empty_access_token_preflight_is_diagnosed_without_request(self):
        with (
            patch("apps.integrations.meta.client.requests.get") as get,
            self.assertLogs("apps.integrations.meta.client", level="WARNING") as logs,
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(access_token="  ")

        get.assert_not_called()
        self.assertEqual(
            self._exchange_diagnostics(logs),
            [{
                "failure_stage": "exchange_preflight_failure",
                "validation_failure_reason": "access_token_missing",
            }],
        )
        output = "\n".join(logs.output)
        self.assertNotIn(self.source_token, output)
        self.assertNotIn(APP_SECRET_CANARY, output)

    def test_missing_app_credentials_preflight_is_diagnosed_without_request(self):
        with (
            override_settings(META_APP_ID="", META_APP_SECRET=""),
            patch("apps.integrations.meta.client.requests.get") as get,
            self.assertLogs("apps.integrations.meta.client", level="WARNING") as logs,
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(
                access_token=self.source_token
            )

        get.assert_not_called()
        self.assertEqual(
            self._exchange_diagnostics(logs),
            [{
                "failure_stage": "exchange_preflight_failure",
                "validation_failure_reason": "meta_app_credentials_missing",
            }],
        )
        output = "\n".join(logs.output)
        self.assertNotIn(self.source_token, output)
        self.assertNotIn(APP_SECRET_CANARY, output)

    def test_invalid_validation_arguments_are_diagnosed_without_provider_calls(self):
        invalid_cases = (
            ("missing_app_id", "synthetic-token", ("pages_show_list",), "app_id_or_access_token_missing_or_invalid"),
            ("missing_token", "", ("pages_show_list",), "app_id_or_access_token_missing_or_invalid"),
            ("string_permissions", "synthetic-token", "pages_show_list", "required_permissions_invalid_type"),
            ("non_iterable_permissions", "synthetic-token", None, "required_permissions_not_iterable"),
            ("empty_permissions", "synthetic-token", (), "required_permissions_empty"),
        )
        for case, token, permissions, reason in invalid_cases:
            with self.subTest(case=case):
                settings_context = (
                    override_settings(META_APP_ID="")
                    if case == "missing_app_id"
                    else override_settings()
                )
                with (
                    settings_context,
                    patch.object(self.client, "diagnose_token") as diagnose,
                    patch.object(self.client, "get_user_permissions") as get_permissions,
                    self.assertLogs(
                        "apps.integrations.meta.client", level="WARNING"
                    ) as logs,
                    self.assertRaises(MetaAPIError),
                ):
                    self.client.validate_user_token_for_exchange(
                        access_token=token,
                        required_permissions=permissions,
                    )

                diagnose.assert_not_called()
                get_permissions.assert_not_called()
                self.assertEqual(
                    self._exchange_diagnostics(logs),
                    [{
                        "failure_stage": "returned_token_validation_preflight_failure",
                        "validation_failure_reason": reason,
                    }],
                )
                output = "\n".join(logs.output)
                self.assertNotIn(self.source_token, output)
                self.assertNotIn(self.exchanged_token, output)
                self.assertNotIn(APP_SECRET_CANARY, output)

    def test_successful_exchange_returns_validated_expiry_metadata_in_memory(self):
        response = self._mock_exchange_response(
            {"access_token": self.exchanged_token, "expires_in": "3600"}
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response) as get,
            patch.object(
                self.client,
                "diagnose_token",
                return_value=self.valid_diagnostics,
            ) as diagnose,
            patch.object(
                self.client,
                "get_user_permissions",
                return_value=self.valid_permissions,
            ) as permissions,
            self.assertLogs("apps.integrations.meta.client", level="INFO") as logs,
        ):
            result = self.client.exchange_user_access_token(
                access_token=self.source_token,
            )

        self.assertEqual(
            result,
            {
                "access_token": self.exchanged_token,
                "expires_in": 3600,
                "provider_expiry_state": "FINITE",
                "provider_expires_at": datetime.fromtimestamp(
                    self.valid_diagnostics["expires_at"], tz=datetime_timezone.utc
                ),
                "data_access_expires_at": datetime.fromtimestamp(
                    self.valid_diagnostics["data_access_expires_at"],
                    tz=datetime_timezone.utc,
                ),
            },
        )
        request_params = get.call_args.kwargs["params"]
        self.assertEqual(request_params["grant_type"], "fb_exchange_token")
        self.assertEqual(request_params["fb_exchange_token"], self.source_token)
        self.assertEqual(request_params["client_id"], "meta-test-app-id")
        self.assertEqual(request_params["client_secret"], APP_SECRET_CANARY)
        diagnose.assert_called_once_with(access_token=self.exchanged_token)
        permissions.assert_called_once_with(access_token=self.exchanged_token)
        self.assertIn(
            {
                "failure_stage": "returned_token_validation_success",
            },
            self._exchange_diagnostics(logs),
        )

    def test_invalid_exchange_response_is_rejected_without_validation_request(self):
        response = self._mock_exchange_response({"expires_in": 3600})
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            patch.object(self.client, "diagnose_token") as diagnose,
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)
        diagnose.assert_not_called()

    def test_provider_error_is_sanitized(self):
        response = self._mock_exchange_response(
            {
                "error": {
                    "message": f"{APP_SECRET_CANARY} {self.source_token}",
                    "code": 190,
                    "error_subcode": 463,
                    "type": "OAuthException",
                }
            },
            ok=False,
            status_code=400,
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            self.assertLogs("apps.integrations.meta.client", level="WARNING") as logs,
            self.assertRaises(MetaAPIError) as raised,
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)

        self.assertEqual(str(raised.exception), "Meta USER token exchange failed.")
        self.assertEqual(
            raised.exception.error_payload,
            {"error": {"code": 190, "error_subcode": 463}},
        )
        self.assertNotIn(self.source_token, str(raised.exception.error_payload))
        self.assertNotIn(APP_SECRET_CANARY, str(raised.exception.error_payload))
        diagnostic = self._exchange_diagnostics(logs)[0]
        self.assertEqual(diagnostic["failure_stage"], "non_success_http_response")
        self.assertEqual(diagnostic["http_status_code"], 400)
        self.assertEqual(diagnostic["meta_error_code"], 190)
        self.assertEqual(diagnostic["meta_error_type"], "OAuthException")
        self.assertNotIn(self.source_token, str(diagnostic))
        self.assertNotIn(APP_SECRET_CANARY, str(diagnostic))

    def test_invalid_json_response_is_diagnosed_without_logging_body(self):
        response = self._mock_exchange_response({})
        response.json.side_effect = ValueError(
            f"invalid response {self.source_token} {APP_SECRET_CANARY}"
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            self.assertLogs("apps.integrations.meta.client", level="WARNING") as logs,
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)

        diagnostic = self._exchange_diagnostics(logs)[0]
        self.assertEqual(diagnostic["failure_stage"], "invalid_json_response")
        self.assertEqual(diagnostic["http_status_code"], 200)
        self.assertNotIn(self.source_token, str(diagnostic))
        self.assertNotIn(APP_SECRET_CANARY, str(diagnostic))

    def test_missing_access_token_is_diagnosed(self):
        response = self._mock_exchange_response({"expires_in": 3600})
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            self.assertLogs("apps.integrations.meta.client", level="WARNING") as logs,
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)

        diagnostic = self._exchange_diagnostics(logs)[0]
        self.assertEqual(diagnostic["failure_stage"], "missing_access_token")
        self.assertEqual(diagnostic["http_status_code"], 200)

    def test_invalid_expires_in_diagnostic_reports_only_presence_and_types(self):
        cases = (
            (
                "null",
                {
                    "access_token": self.exchanged_token,
                    "expires_in": None,
                    "token_type": None,
                },
                True,
                "null",
                True,
                "null",
            ),
            (
                "zero",
                {
                    "access_token": self.exchanged_token,
                    "expires_in": 0,
                    "token_type": "bearer",
                },
                True,
                "integer",
                True,
                "string",
            ),
            (
                "negative",
                {
                    "access_token": self.exchanged_token,
                    "expires_in": -1,
                },
                True,
                "integer",
                False,
                "missing",
            ),
            (
                "oversized_numeric_string",
                {
                    "access_token": self.exchanged_token,
                    "expires_in": "9" * 5000,
                },
                True,
                "string",
                False,
                "missing",
            ),
            (
                "unexpected_type",
                {
                    "access_token": self.exchanged_token,
                    "expires_in": 12.5,
                    "token_type": {"untrusted": self.source_token},
                },
                True,
                "other",
                True,
                "other",
            ),
        )
        for case, payload, expiry_present, expiry_type, token_present, token_type in cases:
            with self.subTest(case=case):
                response = self._mock_exchange_response(payload)
                with (
                    patch(
                        "apps.integrations.meta.client.requests.get",
                        return_value=response,
                    ),
                    self.assertLogs(
                        "apps.integrations.meta.client", level="WARNING"
                    ) as logs,
                    self.assertRaises(MetaAPIError),
                ):
                    self.client.exchange_user_access_token(
                        access_token=self.source_token
                    )

                diagnostic = self._exchange_diagnostics(logs)[0]
                self.assertEqual(
                    diagnostic,
                    {
                        "failure_stage": "missing_or_invalid_expires_in",
                        "http_status_code": 200,
                        "expires_in_present": expiry_present,
                        "expires_in_type": expiry_type,
                        "token_type_present": token_present,
                        "token_type_type": token_type,
                    },
                )
                output = "\n".join(logs.output)
                self.assertNotIn(self.source_token, output)
                self.assertNotIn(self.exchanged_token, output)
                self.assertNotIn(APP_SECRET_CANARY, output)

    def test_positive_integer_expires_in_remains_valid(self):
        response = self._mock_exchange_response(
            {"access_token": self.exchanged_token, "expires_in": 3600}
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            patch.object(
                self.client,
                "diagnose_token",
                return_value=self.valid_diagnostics,
            ),
            patch.object(
                self.client,
                "get_user_permissions",
                return_value=self.valid_permissions,
            ),
            self.assertLogs("apps.integrations.meta.client", level="INFO") as logs,
        ):
            result = self.client.exchange_user_access_token(
                access_token=self.source_token
            )

        self.assertEqual(result["expires_in"], 3600)
        self.assertEqual(
            self._exchange_diagnostics(logs),
            [{"failure_stage": "returned_token_validation_success"}],
        )

    def test_returned_token_validation_failure_is_diagnosed_safely(self):
        response = self._mock_exchange_response(
            {"access_token": self.exchanged_token, "expires_in": 3600}
        )
        invalid_diagnostics = {
            **self.valid_diagnostics,
            "app_id": "different-meta-test-app-id",
        }
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            patch.object(
                self.client,
                "diagnose_token",
                return_value=invalid_diagnostics,
            ),
            self.assertLogs("apps.integrations.meta.client", level="WARNING") as logs,
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)

        diagnostic = self._exchange_diagnostics(logs)[0]
        self.assertEqual(
            diagnostic["failure_stage"],
            "returned_token_validation_failure",
        )
        self.assertEqual(
            diagnostic["validation_failure_reason"],
            "app_id_mismatch",
        )
        self.assertNotIn(self.source_token, str(diagnostic))
        self.assertNotIn(self.exchanged_token, str(diagnostic))
        self.assertNotIn(APP_SECRET_CANARY, str(diagnostic))

    def test_omitted_expires_in_is_accepted_after_full_debug_validation(self):
        response = self._mock_exchange_response(
            {"access_token": self.exchanged_token}
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            patch.object(
                self.client,
                "diagnose_token",
                return_value=self.valid_diagnostics,
            ) as diagnose,
            patch.object(
                self.client,
                "get_user_permissions",
                return_value=self.valid_permissions,
            ) as permissions,
            self.assertLogs("apps.integrations.meta.client", level="INFO"),
        ):
            result = self.client.exchange_user_access_token(
                access_token=self.source_token
            )
        self.assertIsNone(result["expires_in"])
        self.assertEqual(result["provider_expiry_state"], "FINITE")
        self.assertEqual(
            result["provider_expires_at"],
            datetime.fromtimestamp(
                self.valid_diagnostics["expires_at"], tz=datetime_timezone.utc
            ),
        )
        self.assertEqual(
            result["data_access_expires_at"],
            datetime.fromtimestamp(
                self.valid_diagnostics["data_access_expires_at"],
                tz=datetime_timezone.utc,
            ),
        )
        diagnose.assert_called_once_with(access_token=self.exchanged_token)
        permissions.assert_called_once_with(access_token=self.exchanged_token)

    def test_zero_expires_at_means_no_finite_expiry(self):
        diagnostics = {
            **self.valid_diagnostics,
            "expires_at": 0,
        }
        response = self._mock_exchange_response(
            {"access_token": self.exchanged_token}
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            patch.object(self.client, "diagnose_token", return_value=diagnostics),
            patch.object(
                self.client,
                "get_user_permissions",
                return_value=self.valid_permissions,
            ),
            self.assertLogs("apps.integrations.meta.client", level="INFO"),
        ):
            result = self.client.exchange_user_access_token(
                access_token=self.source_token
            )
        self.assertEqual(result["provider_expiry_state"], "NO_FINITE_EXPIRY")
        self.assertIsNone(result["provider_expires_at"])
        self.assertIsNotNone(result["data_access_expires_at"])

    def test_invalid_token_expiry_metadata_is_rejected(self):
        invalid_values = (
            ("missing", None, False),
            ("null", None, True),
            ("malformed", "not-a-timestamp", True),
            ("oversized_numeric_string", "9" * 5000, True),
            ("negative", -1, True),
            ("elapsed", 1, True),
        )
        for name, value, present in invalid_values:
            with self.subTest(expiry=name):
                diagnostics = dict(self.valid_diagnostics)
                if present:
                    diagnostics["expires_at"] = value
                else:
                    diagnostics.pop("expires_at")
                response = self._mock_exchange_response(
                    {"access_token": self.exchanged_token}
                )
                with (
                    patch(
                        "apps.integrations.meta.client.requests.get",
                        return_value=response,
                    ),
                    patch.object(
                        self.client,
                        "diagnose_token",
                        return_value=diagnostics,
                    ),
                    patch.object(
                        self.client,
                        "get_user_permissions",
                        return_value=self.valid_permissions,
                    ) as permissions,
                    self.assertLogs(
                        "apps.integrations.meta.client", level="WARNING"
                    ) as logs,
                    self.assertRaises(MetaAPIError),
                ):
                    self.client.exchange_user_access_token(
                        access_token=self.source_token
                    )
                self.assertEqual(
                    self._exchange_diagnostics(logs)[-1][
                        "validation_failure_reason"
                    ],
                    "token_expiry_missing_or_invalid"
                    if name in {
                        "missing",
                        "null",
                        "malformed",
                        "negative",
                        "oversized_numeric_string",
                    }
                    else "token_expired",
                )
                permissions.assert_not_called()

    def test_invalid_data_access_expiry_metadata_is_rejected_independently(self):
        invalid_values = (
            ("missing", None, False),
            ("null", None, True),
            ("zero", 0, True),
            ("malformed", "not-a-timestamp", True),
            ("negative", -1, True),
            ("elapsed", 1, True),
        )
        for name, value, present in invalid_values:
            with self.subTest(expiry=name):
                diagnostics = dict(self.valid_diagnostics)
                if present:
                    diagnostics["data_access_expires_at"] = value
                else:
                    diagnostics.pop("data_access_expires_at")
                response = self._mock_exchange_response(
                    {"access_token": self.exchanged_token}
                )
                with (
                    patch(
                        "apps.integrations.meta.client.requests.get",
                        return_value=response,
                    ),
                    patch.object(
                        self.client,
                        "diagnose_token",
                        return_value=diagnostics,
                    ),
                    patch.object(self.client, "get_user_permissions") as permissions,
                    self.assertLogs(
                        "apps.integrations.meta.client", level="WARNING"
                    ) as logs,
                    self.assertRaises(MetaAPIError),
                ):
                    self.client.exchange_user_access_token(
                        access_token=self.source_token
                    )
                self.assertEqual(
                    self._exchange_diagnostics(logs)[-1][
                        "validation_failure_reason"
                    ],
                    "data_access_expired"
                    if name in {"zero", "elapsed"}
                    else "data_access_expiry_missing_or_invalid",
                )
                permissions.assert_not_called()

    def test_app_type_validity_expiry_and_permission_validation_failures(self):
        invalid_cases = (
            {
                **self.valid_diagnostics,
                "app_id": "different-meta-app-id",
            },
            {**self.valid_diagnostics, "type": "SYSTEM_USER"},
            {**self.valid_diagnostics, "is_valid": False},
            {**self.valid_diagnostics, "expires_at": 1},
        )
        for diagnostics in invalid_cases:
            with self.subTest(diagnostics=diagnostics):
                response = self._mock_exchange_response(
                    {"access_token": self.exchanged_token, "expires_in": 3600}
                )
                with (
                    patch(
                        "apps.integrations.meta.client.requests.get",
                        return_value=response,
                    ),
                    patch.object(
                        self.client,
                        "diagnose_token",
                        return_value=diagnostics,
                    ),
                    patch.object(
                        self.client,
                        "get_user_permissions",
                        return_value=self.valid_permissions,
                    ),
                    self.assertRaises(MetaAPIError),
                ):
                    self.client.exchange_user_access_token(
                        access_token=self.source_token,
                    )

        response = self._mock_exchange_response(
            {"access_token": self.exchanged_token, "expires_in": 3600}
        )
        with (
            patch("apps.integrations.meta.client.requests.get", return_value=response),
            patch.object(
                self.client,
                "diagnose_token",
                return_value=self.valid_diagnostics,
            ),
            patch.object(self.client, "get_user_permissions", return_value={"data": []}),
            self.assertRaises(MetaAPIError),
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)

    def test_exchange_transport_error_does_not_log_or_chain_credentials(self):
        request_error = requests.ConnectionError(
            "request URL contained "
            f"{self.source_token} and {APP_SECRET_CANARY}"
        )
        with (
            patch(
                "apps.integrations.meta.client.requests.get",
                side_effect=request_error,
            ),
            self.assertLogs("apps.integrations.meta.client", level="ERROR") as logs,
            self.assertRaises(MetaAPIError) as raised,
        ):
            self.client.exchange_user_access_token(access_token=self.source_token)

        output = "\n".join(logs.output)
        self.assertNotIn(self.source_token, output)
        self.assertNotIn(APP_SECRET_CANARY, output)
        diagnostic = self._exchange_diagnostics(logs)[0]
        self.assertEqual(diagnostic["failure_stage"], "http_transport_failure")
        self.assertNotIn(self.source_token, str(diagnostic))
        self.assertNotIn(APP_SECRET_CANARY, str(diagnostic))
        self.assertIsNone(raised.exception.__cause__)


class MetaParentExpiryStateLifecycleUnitTests(SimpleTestCase):
    def setUp(self):
        self.now = timezone.now()
        self.provider_expiry = self.now + timedelta(days=12)
        self.data_access_expiry = self.now + timedelta(days=8)
        self.valid_debug = {
            "type": "USER",
            "is_valid": True,
            "expires_at": int(self.provider_expiry.timestamp()),
            "data_access_expires_at": int(self.data_access_expiry.timestamp()),
        }
        self.credential = SimpleNamespace(
            id="synthetic-user-credential",
            access_token="synthetic-encrypted-placeholder",
            updated_at=self.now,
            last_verified_at=None,
            provider_expiry_state=MetaProviderExpiryState.UNKNOWN,
            provider_expires_at=None,
            data_access_expires_at=None,
            granted_permissions=[],
        )
        self.api = MagicMock()
        self.api.diagnose_token.return_value = self.valid_debug
        self.api.get_user_permissions.return_value = {
            "data": [{"permission": "pages_show_list", "status": "granted"}]
        }
        self.service = MetaTokenLifecycleService(api_client=self.api)

    def _run_check(self, debug):
        self.api.diagnose_token.return_value = debug
        with (
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-user-token",
            ),
            patch.object(
                self.service,
                "_save_parent_health_if_current",
                return_value=self.now + timedelta(seconds=1),
            ) as save_health,
            patch.object(self.service, "_resolve_parent_reconnect_required"),
        ):
            outcome = self.service._check_parent_user_credential(self.credential)
        return outcome, save_health

    def test_future_provider_expiry_is_persisted_as_finite(self):
        outcome, save_health = self._run_check(self.valid_debug)
        first_updates = save_health.call_args_list[0].kwargs

        self.assertEqual(outcome, "valid")
        self.assertEqual(
            first_updates["provider_expiry_state"],
            MetaProviderExpiryState.FINITE,
        )
        self.assertEqual(
            first_updates["provider_expires_at"],
            datetime.fromtimestamp(
                self.valid_debug["expires_at"], tz=datetime_timezone.utc
            ),
        )
        self.assertEqual(
            first_updates["data_access_expires_at"],
            datetime.fromtimestamp(
                self.valid_debug["data_access_expires_at"],
                tz=datetime_timezone.utc,
            ),
        )

    def test_zero_provider_expiry_is_persisted_as_no_finite_expiry(self):
        debug = {**self.valid_debug, "expires_at": 0}
        outcome, save_health = self._run_check(debug)
        first_updates = save_health.call_args_list[0].kwargs

        self.assertEqual(outcome, "valid")
        self.assertEqual(
            first_updates["provider_expiry_state"],
            MetaProviderExpiryState.NO_FINITE_EXPIRY,
        )
        self.assertIsNone(first_updates["provider_expires_at"])
        self.assertIn("data_access_expires_at", first_updates)

    def test_missing_or_invalid_expiry_metadata_stays_unknown_for_unknown_credential(self):
        for name, expiry in (("missing", None), ("invalid", "bad-timestamp")):
            with self.subTest(expiry=name):
                self.credential.provider_expiry_state = MetaProviderExpiryState.UNKNOWN
                debug = dict(self.valid_debug)
                if expiry is None:
                    debug.pop("expires_at")
                else:
                    debug["expires_at"] = expiry
                outcome, save_health = self._run_check(debug)
                first_updates = save_health.call_args_list[0].kwargs

                self.assertEqual(outcome, "valid")
                self.assertEqual(
                    first_updates["provider_expiry_state"],
                    MetaProviderExpiryState.UNKNOWN,
                )
                self.assertNotIn("provider_expires_at", first_updates)

    def test_incomplete_diagnostic_preserves_previously_known_expiry_state(self):
        prior_expiry = self.now + timedelta(days=4)
        self.credential.provider_expiry_state = MetaProviderExpiryState.FINITE
        self.credential.provider_expires_at = prior_expiry
        self.credential.data_access_expires_at = self.now + timedelta(days=3)
        debug = {"type": "USER", "is_valid": True}

        outcome, save_health = self._run_check(debug)
        first_updates = save_health.call_args_list[0].kwargs

        self.assertEqual(outcome, "valid")
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.FINITE,
        )
        self.assertNotIn("provider_expiry_state", first_updates)
        self.assertNotIn("provider_expires_at", first_updates)
        self.assertNotIn("data_access_expires_at", first_updates)

    def test_incomplete_diagnostic_preserves_known_no_finite_state(self):
        self.credential.provider_expiry_state = (
            MetaProviderExpiryState.NO_FINITE_EXPIRY
        )
        self.credential.data_access_expires_at = self.now + timedelta(days=3)
        debug = {"type": "USER", "is_valid": True, "expires_at": None}

        outcome, save_health = self._run_check(debug)
        first_updates = save_health.call_args_list[0].kwargs

        self.assertEqual(outcome, "valid")
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.NO_FINITE_EXPIRY,
        )
        self.assertNotIn("provider_expiry_state", first_updates)
        self.assertNotIn("provider_expires_at", first_updates)

    def test_data_access_expiry_is_parsed_independently(self):
        previous_data_expiry = self.now + timedelta(days=2)
        self.credential.data_access_expires_at = previous_data_expiry
        debug = {
            **self.valid_debug,
            "data_access_expires_at": "invalid-provider-value",
        }

        outcome, save_health = self._run_check(debug)
        first_updates = save_health.call_args_list[0].kwargs

        self.assertEqual(outcome, "valid")
        self.assertEqual(
            first_updates["provider_expiry_state"],
            MetaProviderExpiryState.FINITE,
        )
        self.assertIn("provider_expires_at", first_updates)
        self.assertNotIn("data_access_expires_at", first_updates)
        self.assertEqual(
            self.credential.data_access_expires_at,
            previous_data_expiry,
        )


class MetaScopedUserCredentialValidationTests(SimpleTestCase):
    def setUp(self):
        self.now = timezone.now()
        self.updated_at = self.now - timedelta(minutes=5)
        self.credential = SimpleNamespace(
            id="selected-user-credential",
            access_token="synthetic-encrypted-token",
            updated_at=self.updated_at,
            status=MetaCredentialStatus.ACTIVE,
            credential_type=MetaCredentialType.USER,
            is_deleted=False,
        )
        self.provider_expiry = int((self.now + timedelta(days=10)).timestamp())
        self.data_access_expiry = int((self.now + timedelta(days=5)).timestamp())
        self.debug = {
            "app_id": "configured-meta-app",
            "type": "USER",
            "is_valid": True,
            "expires_at": self.provider_expiry,
            "data_access_expires_at": self.data_access_expiry,
        }
        self.api = MagicMock()
        self.api.diagnose_token.return_value = self.debug
        self.api.get_user_permissions.return_value = {
            "data": [
                {"permission": "pages_show_list", "status": "granted"},
                {"permission": "pages_manage_posts", "status": "granted"},
            ]
        }
        self.service = MetaTokenLifecycleService(api_client=self.api)
        self.locked_queryset = MagicMock()
        self.locked_queryset.filter.return_value.first.return_value = self.credential
        self.update_queryset = MagicMock()
        self.update_queryset.update.return_value = 1

    def _execute(self, *, debug=None, permissions=None, current=None):
        if debug is not None:
            self.api.diagnose_token.return_value = debug
        if permissions is not None:
            self.api.get_user_permissions.return_value = permissions
        if current is not None:
            self.locked_queryset.filter.return_value.first.return_value = current
        with (
            override_settings(META_APP_ID="configured-meta-app"),
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-user-token",
            ),
            patch.object(
                MetaAccountCredential.objects,
                "get",
                return_value=self.credential,
            ) as get_credential,
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                return_value=self.locked_queryset,
            ),
            patch.object(
                MetaAccountCredential.objects,
                "filter",
                return_value=self.update_queryset,
            ) as update_filter,
            patch(
                "apps.integrations.meta.lifecycle.transaction.atomic",
                return_value=nullcontext(),
            ),
        ):
            outcome = self.service.validate_and_persist_user_credential_health(
                self.credential.id,
                required_permissions={"pages_show_list", "pages_manage_posts"},
            )
        return outcome, get_credential, update_filter

    def test_valid_finite_token_writes_exactly_the_approved_fields(self):
        outcome, get_credential, update_filter = self._execute()

        self.assertEqual(outcome, "updated")
        get_credential.assert_called_once_with(
            pk=self.credential.id,
            credential_type=MetaCredentialType.USER,
            status=MetaCredentialStatus.ACTIVE,
            is_deleted=False,
        )
        update_filter.assert_called_once_with(
            pk=self.credential.id,
            credential_type=MetaCredentialType.USER,
            status=MetaCredentialStatus.ACTIVE,
            is_deleted=False,
            access_token=self.credential.access_token,
            updated_at=self.updated_at,
        )
        updates = self.update_queryset.update.call_args.kwargs
        self.assertEqual(
            set(updates),
            {
                "provider_token_type",
                "provider_is_valid",
                "provider_expiry_state",
                "provider_expires_at",
                "data_access_expires_at",
                "last_health_check_at",
            },
        )
        self.assertEqual(updates["provider_token_type"], "USER")
        self.assertIs(updates["provider_is_valid"], True)
        self.assertEqual(
            updates["provider_expiry_state"], MetaProviderExpiryState.FINITE
        )
        self.assertEqual(
            updates["provider_expires_at"],
            datetime.fromtimestamp(
                self.provider_expiry, tz=datetime_timezone.utc
            ),
        )
        self.assertEqual(
            updates["data_access_expires_at"],
            datetime.fromtimestamp(
                self.data_access_expiry, tz=datetime_timezone.utc
            ),
        )
        self.api.diagnose_token.assert_called_once_with(
            access_token="synthetic-user-token"
        )
        self.api.get_user_permissions.assert_called_once_with(
            access_token="synthetic-user-token"
        )

    def test_zero_provider_expiry_is_classified_as_no_finite_expiry(self):
        outcome, _get_credential, _update_filter = self._execute(
            debug={**self.debug, "expires_at": 0}
        )

        self.assertEqual(outcome, "updated")
        updates = self.update_queryset.update.call_args.kwargs
        self.assertEqual(
            updates["provider_expiry_state"],
            MetaProviderExpiryState.NO_FINITE_EXPIRY,
        )
        self.assertIsNone(updates["provider_expires_at"])

    def test_validation_failures_do_not_write_anything(self):
        invalid_debug_cases = (
            {**self.debug, "app_id": "another-app"},
            {**self.debug, "type": "PAGE"},
            {**self.debug, "is_valid": False},
            {**self.debug, "expires_at": None},
            {**self.debug, "expires_at": -1},
            {**self.debug, "expires_at": int(self.now.timestamp()) - 1},
            {**self.debug, "data_access_expires_at": 0},
            {**self.debug, "data_access_expires_at": "invalid"},
            {**self.debug, "data_access_expires_at": int(self.now.timestamp()) - 1},
        )
        for debug in invalid_debug_cases:
            with self.subTest(debug=debug), self.assertRaises(MetaAPIError):
                self._execute(debug=debug)
            self.update_queryset.update.assert_not_called()

    def test_missing_required_permission_does_not_write(self):
        with self.assertRaises(MetaAPIError):
            self._execute(
                permissions={
                    "data": [
                        {"permission": "pages_show_list", "status": "granted"}
                    ]
                }
            )

        self.update_queryset.update.assert_not_called()

    def test_incomplete_permissions_response_does_not_write(self):
        with self.assertRaises(MetaAPIError):
            self._execute(permissions={"error": {"message": "sanitized in test"}})

        self.update_queryset.update.assert_not_called()

    def test_concurrent_credential_change_prevents_write(self):
        changed = SimpleNamespace(
            **{
                **vars(self.credential),
                "access_token": "different-encrypted-token",
            }
        )
        outcome, _get_credential, _update_filter = self._execute(current=changed)

        self.assertEqual(outcome, "stale")
        self.update_queryset.update.assert_not_called()


@override_settings(
    META_USER_TOKEN_RENEWAL_WINDOW_SECONDS=7 * 24 * 60 * 60,
    META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS=24 * 60 * 60,
    META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS=(
        "pages_show_list",
        "pages_manage_posts",
    ),
)
class MetaUserTokenRenewalServiceTests(SimpleTestCase):
    def setUp(self):
        self.now = timezone.now()
        self.expected_updated_at = self.now - timedelta(minutes=3)
        self.credential = SimpleNamespace(
            id="renewal-user-credential",
            social_connection=SimpleNamespace(provider_user_id="meta-user-123"),
            credential_type=MetaCredentialType.USER,
            status=MetaCredentialStatus.ACTIVE,
            is_deleted=False,
            access_token="encrypted-original-user-token",
            updated_at=self.expected_updated_at,
            token_expires_at=self.now + timedelta(days=90),
            provider_token_type="USER",
            provider_is_valid=True,
            provider_expiry_state=MetaProviderExpiryState.FINITE,
            provider_expires_at=self.now + timedelta(days=3),
            data_access_expires_at=self.now + timedelta(days=20),
            last_health_check_at=self.now - timedelta(days=1),
            last_user_token_renewed_at=None,
            granted_permissions=[
                {"permission": "pages_show_list", "status": "granted"}
            ],
            save=MagicMock(),
        )
        self.api = MagicMock()
        self.api.safe_error_metadata.return_value = {
            "http_status": None,
            "graph_error_code": None,
            "graph_error_subcode": None,
        }
        self.api.exchange_user_access_token.return_value = {
            "access_token": "synthetic-returned-user-token",
            "expires_in": 20 * 24 * 60 * 60,
            "provider_expiry_state": MetaProviderExpiryState.FINITE,
            "provider_expires_at": self.now + timedelta(days=30),
            "data_access_expires_at": self.now + timedelta(days=20),
        }
        self.service = MetaTokenLifecycleService(api_client=self.api)
        self.locked_queryset = MagicMock()
        self.locked_queryset.get.return_value = self.credential

    def _run_renewal(self, *, exchange_result=None, current=None, encrypt_side_effect=None):
        if exchange_result is not None:
            self.api.exchange_user_access_token.return_value = exchange_result
        if current is None:
            current = self.credential
        self.locked_queryset.get.return_value = current
        with (
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-original-user-token",
            ),
            patch(
                "apps.integrations.meta.lifecycle.encrypt_token",
                return_value="encrypted-replacement-user-token",
                side_effect=encrypt_side_effect,
            ) as encrypt,
            patch.object(
                MetaAccountCredential.objects,
                "get",
                return_value=self.credential,
            ) as get_credential,
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                return_value=self.locked_queryset,
            ),
            patch.object(
                self.service,
                "_acquire_user_renewal_lock",
                return_value="synthetic-lock-owner",
            ) as acquire_lock,
            patch.object(self.service, "_release_user_renewal_lock") as release_lock,
            patch(
                "apps.integrations.meta.lifecycle.transaction.atomic",
                return_value=nullcontext(),
            ),
        ):
            outcome = self.service._renew_user_credential(
                self.credential.id,
                required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            )
        return outcome, get_credential, encrypt, acquire_lock, release_lock

    def _run_with_real_exchange_client(self, debug_metadata):
        client = MetaAPIClient()
        service = MetaTokenLifecycleService(api_client=client)
        locked_queryset = MagicMock()
        locked_queryset.get.return_value = self.credential

        def response(payload):
            mocked_response = MagicMock()
            mocked_response.ok = True
            mocked_response.status_code = 200
            mocked_response.json.return_value = payload
            return mocked_response

        permission_data = [
            {"permission": "pages_show_list", "status": "granted"},
            {"permission": "pages_manage_posts", "status": "granted"},
        ]
        provider_responses = [
            response({"access_token": "synthetic-returned-user-token"}),
            response({"data": debug_metadata}),
        ]
        if debug_metadata.get("user_id") == "meta-user-123":
            provider_responses.append(response({"data": permission_data}))
        exchange_results = []
        real_exchange = client.exchange_user_access_token

        def capture_exchange_result(**kwargs):
            result = real_exchange(**kwargs)
            exchange_results.append(result)
            return result

        with (
            override_settings(
                META_APP_ID="meta-test-app",
                META_APP_SECRET="synthetic-app-secret",
            ),
            patch(
                "apps.integrations.meta.client.requests.get",
                side_effect=provider_responses,
            ) as http_get,
            patch.object(
                client,
                "exchange_user_access_token",
                side_effect=capture_exchange_result,
            ) as exchange,
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-original-user-token",
            ),
            patch(
                "apps.integrations.meta.lifecycle.encrypt_token",
                return_value="encrypted-replacement-user-token",
            ) as encrypt,
            patch.object(
                MetaAccountCredential.objects,
                "get",
                return_value=self.credential,
            ),
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                return_value=locked_queryset,
            ),
            patch.object(
                service,
                "_acquire_user_renewal_lock",
                return_value="synthetic-lock-owner",
            ),
            patch.object(service, "_release_user_renewal_lock"),
            patch(
                "apps.integrations.meta.lifecycle.transaction.atomic",
                return_value=nullcontext(),
            ),
            self.assertLogs("apps.integrations.meta.client", level="INFO"),
        ):
            outcome = service._renew_user_credential(
                self.credential.id,
                required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            )
        return outcome, exchange_results, exchange, http_get, encrypt

    def test_client_lifecycle_persists_omitted_expiry_for_same_user(self):
        diagnostics = {
            "app_id": "meta-test-app",
            "type": "USER",
            "user_id": "meta-user-123",
            "is_valid": True,
            "expires_at": 0,
            "data_access_expires_at": int(
                (timezone.now() + timedelta(days=20)).timestamp()
            ),
        }

        outcome, exchange_results, exchange, _http_get, _encrypt = (
            self._run_with_real_exchange_client(diagnostics)
        )

        self.assertEqual(outcome, "renewed")
        self.assertEqual(len(exchange_results), 1)
        self.assertIn("expires_in", exchange_results[0])
        self.assertIsNone(exchange_results[0]["expires_in"])
        self.assertEqual(
            exchange.call_args.kwargs["expected_user_id"],
            "meta-user-123",
        )
        self.assertIsNone(self.credential.token_expires_at)
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.NO_FINITE_EXPIRY,
        )
        self.assertIsNone(self.credential.provider_expires_at)
        self.assertIsNotNone(self.credential.last_user_token_renewed_at)

    def test_missing_or_mismatched_user_identity_preserves_credential(self):
        for identity_case, identity in (
            ("missing", None),
            ("mismatched", "different-meta-user"),
        ):
            with self.subTest(identity_case=identity_case):
                original = dict(vars(self.credential))
                diagnostics = {
                    "app_id": "meta-test-app",
                    "type": "USER",
                    "is_valid": True,
                    "expires_at": 0,
                    "data_access_expires_at": int(
                        (timezone.now() + timedelta(days=20)).timestamp()
                    ),
                }
                if identity is not None:
                    diagnostics["user_id"] = identity

                outcome, _exchange_results, _exchange, http_get, encrypt = (
                    self._run_with_real_exchange_client(diagnostics)
                )

                self.assertEqual(outcome, "retry")
                self.assertEqual(vars(self.credential), original)
                self.credential.save.assert_not_called()
                encrypt.assert_not_called()
                self.assertEqual(http_get.call_count, 2)

    def test_eligibility_matrix(self):
        due = self.credential
        self.assertTrue(
            self.service._user_credential_is_due_for_renewal(
                due,
                now=self.now,
                window=timedelta(days=7),
            )
        )

        cases = (
            ("outside_window", {"provider_expires_at": self.now + timedelta(days=8)}),
            (
                "no_finite_expiry",
                {"provider_expiry_state": MetaProviderExpiryState.NO_FINITE_EXPIRY},
            ),
            ("unknown", {"provider_expiry_state": MetaProviderExpiryState.UNKNOWN}),
            ("missing_data_expiry", {"data_access_expires_at": None}),
            (
                "expired_data_expiry",
                {"data_access_expires_at": self.now - timedelta(seconds=1)},
            ),
            (
                "expired_provider_expiry",
                {"provider_expires_at": self.now - timedelta(seconds=1)},
            ),
            ("provider_unconfirmed", {"provider_is_valid": None}),
            (
                "recently_renewed",
                {"last_user_token_renewed_at": self.now - timedelta(hours=1)},
            ),
            ("inactive", {"status": MetaCredentialStatus.REVOKED}),
            ("deleted", {"is_deleted": True}),
        )
        for name, changes in cases:
            with self.subTest(name=name):
                candidate = SimpleNamespace(**{**vars(due), **changes})
                self.assertFalse(
                    self.service._user_credential_is_due_for_renewal(
                        candidate,
                        now=self.now,
                        window=timedelta(days=7),
                    )
                )

    def test_due_query_selects_only_active_finite_confirmed_meta_user_credentials(self):
        candidates = MagicMock()
        candidates.filter.return_value = candidates
        candidates.order_by.return_value = candidates
        candidates.values_list.return_value = candidates
        candidates.iterator.return_value = iter(())
        with patch.object(
            MetaAccountCredential.objects,
            "filter",
            return_value=candidates,
        ) as select_candidates:
            result = self.service.renew_due_user_credentials()

        self.assertEqual(result["eligible"], 0)
        select_candidates.assert_called_once()
        filters = select_candidates.call_args.kwargs
        self.assertEqual(
            set(filters),
            {
                "credential_type",
                "status",
                "is_deleted",
                "social_connection__isnull",
                "social_connection__is_deleted",
                "social_connection__provider",
                "social_connection__status",
                "provider_expiry_state",
                "provider_is_valid",
                "provider_token_type",
                "provider_expires_at__gt",
                "provider_expires_at__lte",
                "data_access_expires_at__gt",
            },
        )
        self.assertEqual(filters["credential_type"], MetaCredentialType.USER)
        self.assertEqual(filters["status"], MetaCredentialStatus.ACTIVE)
        self.assertFalse(filters["is_deleted"])
        self.assertEqual(
            filters["provider_expiry_state"], MetaProviderExpiryState.FINITE
        )
        self.assertTrue(filters["provider_is_valid"])
        self.assertEqual(filters["provider_token_type"], "USER")
        self.assertLess(
            filters["provider_expires_at__gt"],
            filters["provider_expires_at__lte"],
        )
        self.assertEqual(
            filters["data_access_expires_at__gt"],
            filters["provider_expires_at__gt"],
        )
        query_cooldown = candidates.filter.call_args.args[0]
        self.assertEqual(query_cooldown.connector, Q.OR)
        self.assertEqual(
            query_cooldown.children[0],
            ("last_user_token_renewed_at__isnull", True),
        )
        self.assertEqual(
            query_cooldown.children[1][0],
            "last_user_token_renewed_at__lte",
        )

    def test_success_encrypts_then_persists_only_renewal_fields(self):
        outcome, get_credential, encrypt, acquire, release = self._run_renewal()

        self.assertEqual(outcome, "renewed")
        get_credential.assert_called_once_with(
            pk=self.credential.id,
            credential_type=MetaCredentialType.USER,
            status=MetaCredentialStatus.ACTIVE,
            is_deleted=False,
            social_connection__provider=SocialConnectionProvider.META,
            social_connection__is_deleted=False,
            social_connection__status=SocialConnectionStatus.ACTIVE,
            provider_token_type="USER",
        )
        acquire.assert_called_once_with(self.credential.id)
        release.assert_called_once_with(self.credential.id, "synthetic-lock-owner")
        self.api.exchange_user_access_token.assert_called_once_with(
            access_token="synthetic-original-user-token",
            required_permissions=("pages_show_list", "pages_manage_posts"),
            expected_user_id="meta-user-123",
        )
        encrypt.assert_called_once_with("synthetic-returned-user-token")
        saved_fields = set(self.credential.save.call_args.kwargs["update_fields"])
        self.assertEqual(
            saved_fields,
            {
                "access_token",
                "token_expires_at",
                "provider_token_type",
                "provider_is_valid",
                "provider_expiry_state",
                "provider_expires_at",
                "data_access_expires_at",
                "last_health_check_at",
                "last_user_token_renewed_at",
                "updated_at",
            },
        )
        self.assertEqual(
            self.credential.access_token,
            "encrypted-replacement-user-token",
        )
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.FINITE,
        )
        self.assertGreater(self.credential.token_expires_at, self.now)
        self.assertLess(
            self.credential.token_expires_at,
            self.now + timedelta(days=30),
        )
        self.assertEqual(
            self.credential.granted_permissions,
            [{"permission": "pages_show_list", "status": "granted"}],
        )

    def test_repeated_maintenance_does_not_exchange_again_within_cooldown(self):
        first_outcome, *_ = self._run_renewal()
        self.assertEqual(first_outcome, "renewed")
        self.assertIsNotNone(self.credential.last_user_token_renewed_at)

        second_outcome, _get, _encrypt, acquire, release = self._run_renewal()

        self.assertEqual(second_outcome, "skipped")
        self.assertEqual(self.api.exchange_user_access_token.call_count, 1)
        acquire.assert_called_once()
        release.assert_called_once()

    def test_missing_expires_in_clears_old_token_expiry_and_keeps_no_finite_state(self):
        result = {
            "access_token": "synthetic-returned-user-token",
            "provider_expiry_state": MetaProviderExpiryState.NO_FINITE_EXPIRY,
            "provider_expires_at": None,
            "data_access_expires_at": self.now + timedelta(days=20),
        }
        outcome, _get, _encrypt, _acquire, _release = self._run_renewal(
            exchange_result=result
        )

        self.assertEqual(outcome, "renewed")
        self.assertIsNone(self.credential.token_expires_at)
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.NO_FINITE_EXPIRY,
        )
        self.assertIsNone(self.credential.provider_expires_at)

    def test_digit_string_expires_in_is_normalized_and_persisted(self):
        result = {
            "access_token": "synthetic-returned-user-token",
            "expires_in": "1728000",
            "provider_expiry_state": MetaProviderExpiryState.FINITE,
            "provider_expires_at": self.now + timedelta(days=30),
            "data_access_expires_at": self.now + timedelta(days=20),
        }
        outcome, _get, _encrypt, _acquire, _release = self._run_renewal(
            exchange_result=result
        )

        self.assertEqual(outcome, "renewed")
        self.assertGreater(self.credential.token_expires_at, self.now)
        self.assertLess(
            self.credential.token_expires_at,
            self.now + timedelta(days=21),
        )

    def test_exchange_failure_preserves_entire_credential(self):
        original = dict(vars(self.credential))
        self.api.exchange_user_access_token.side_effect = RuntimeError(
            "synthetic provider failure"
        )

        outcome, _get, encrypt, _acquire, release = self._run_renewal()

        self.assertEqual(outcome, "retry")
        self.assertEqual(vars(self.credential), original)
        self.credential.save.assert_not_called()
        encrypt.assert_not_called()
        release.assert_called_once()

    def test_invalid_exchange_metadata_preserves_entire_credential(self):
        invalid_results = (
            {
                "provider_expiry_state": MetaProviderExpiryState.UNKNOWN,
                "provider_expires_at": None,
            },
            {
                "provider_expiry_state": MetaProviderExpiryState.FINITE,
                "provider_expires_at": self.now - timedelta(seconds=1),
            },
            {
                "provider_expiry_state": MetaProviderExpiryState.NO_FINITE_EXPIRY,
                "provider_expires_at": self.now,
            },
        )
        for invalid_metadata in invalid_results:
            with self.subTest(metadata=invalid_metadata):
                original = dict(vars(self.credential))
                invalid_result = {
                    "access_token": "synthetic-returned-user-token",
                    "expires_in": 3600,
                    **invalid_metadata,
                    "data_access_expires_at": self.now + timedelta(days=20),
                }
                outcome, _get, encrypt, _acquire, release = self._run_renewal(
                    exchange_result=invalid_result
                )

                self.assertEqual(outcome, "retry")
                self.assertEqual(vars(self.credential), original)
                self.credential.save.assert_not_called()
                encrypt.assert_not_called()
                release.assert_called_once()

    def test_invalid_or_expired_data_access_expiry_and_invalid_expires_in_do_not_write(self):
        invalid_values = (
            {"expires_in": True},
            {"expires_in": False},
            {"data_access_expires_at": None},
            {"data_access_expires_at": self.now - timedelta(seconds=1)},
            {"expires_in": 0},
            {"expires_in": -1},
            {"expires_in": "12seconds"},
            {"expires_in": 5.0},
        )
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                original = dict(vars(self.credential))
                invalid_result = {
                    "access_token": "synthetic-returned-user-token",
                    "expires_in": 3600,
                    "provider_expiry_state": MetaProviderExpiryState.FINITE,
                    "provider_expires_at": self.now + timedelta(days=30),
                    "data_access_expires_at": self.now + timedelta(days=20),
                    **invalid_value,
                }
                outcome, _get, encrypt, _acquire, release = self._run_renewal(
                    exchange_result=invalid_result
                )

                self.assertEqual(outcome, "retry")
                self.assertEqual(vars(self.credential), original)
                self.credential.save.assert_not_called()
                encrypt.assert_not_called()
                release.assert_called_once()

    def test_encryption_failure_preserves_entire_credential(self):
        original = dict(vars(self.credential))

        outcome, _get, _encrypt, _acquire, release = self._run_renewal(
            encrypt_side_effect=RuntimeError("synthetic encryption failure")
        )

        self.assertEqual(outcome, "retry")
        self.assertEqual(vars(self.credential), original)
        self.credential.save.assert_not_called()
        release.assert_called_once()

    def test_stale_concurrent_token_or_timestamp_change_is_not_overwritten(self):
        original = dict(vars(self.credential))
        concurrent_variants = (
            {"access_token": "encrypted-concurrent-reconnect-token"},
            {"updated_at": self.expected_updated_at + timedelta(seconds=1)},
            {"provider_token_type": "SYSTEM_USER"},
            {"provider_token_type": "unknown"},
        )
        for changes in concurrent_variants:
            with self.subTest(changes=changes):
                concurrent = SimpleNamespace(
                    **{
                        **vars(self.credential),
                        **changes,
                        "save": MagicMock(),
                    }
                )
                outcome, _get, _encrypt, _acquire, release = self._run_renewal(
                    current=concurrent
                )

                self.assertEqual(outcome, "stale")
                self.assertEqual(vars(self.credential), original)
                concurrent.save.assert_not_called()
                release.assert_called_once()

    def test_non_user_provider_token_types_are_never_exchanged(self):
        for token_type in ("SYSTEM_USER", "unknown"):
            with self.subTest(token_type=token_type):
                self.credential.provider_token_type = token_type
                self.credential.save.reset_mock()
                self.api.exchange_user_access_token.reset_mock()
                outcome, get_credential, _encrypt, _acquire, release = (
                    self._run_renewal()
                )

                self.assertEqual(outcome, "skipped")
                self.assertEqual(
                    get_credential.call_args.kwargs["provider_token_type"], "USER"
                )
                self.api.exchange_user_access_token.assert_not_called()
                self.credential.save.assert_not_called()
                release.assert_called_once()

    def test_lock_contention_skips_without_exchange(self):
        with (
            patch.object(self.service, "_acquire_user_renewal_lock", return_value=None),
            patch.object(MetaAccountCredential.objects, "get") as get_credential,
        ):
            outcome = self.service._renew_user_credential(
                self.credential.id,
                required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            )

        self.assertEqual(outcome, "locked")
        get_credential.assert_not_called()
        self.api.exchange_user_access_token.assert_not_called()

    def test_lock_backend_failure_does_not_exchange(self):
        with patch.object(
            self.service,
            "_acquire_user_renewal_lock",
            side_effect=RuntimeError("synthetic lock backend failure"),
        ):
            outcome = self.service._renew_user_credential(
                self.credential.id,
                required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            )

        self.assertEqual(outcome, "retry")
        self.api.exchange_user_access_token.assert_not_called()
        self.credential.save.assert_not_called()


@override_settings(
    META_USER_TOKEN_AUTO_RENEWAL_ENABLED=False,
    META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS=24 * 60 * 60,
    META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS=(
        "pages_show_list",
        "pages_manage_posts",
    ),
)
class MetaControlledUserCredentialReplacementTests(SimpleTestCase):
    def setUp(self):
        self.now = timezone.now()
        self.original_updated_at = self.now - timedelta(minutes=2)
        self.credential = SimpleNamespace(
            id="controlled-user-credential",
            social_connection=SimpleNamespace(
                provider_user_id="meta-user-123",
                organization=SimpleNamespace(organization_id="ORG000034"),
            ),
            credential_type=MetaCredentialType.USER,
            status=MetaCredentialStatus.ACTIVE,
            is_deleted=False,
            access_token="encrypted-original-controlled-token",
            updated_at=self.original_updated_at,
            token_expires_at=None,
            provider_token_type="USER",
            provider_is_valid=True,
            provider_expiry_state=MetaProviderExpiryState.NO_FINITE_EXPIRY,
            provider_expires_at=None,
            data_access_expires_at=self.now + timedelta(days=20),
            last_health_check_at=self.now - timedelta(days=1),
            last_user_token_renewed_at=None,
            granted_permissions=[
                {"permission": "pages_show_list", "status": "granted"}
            ],
            save=MagicMock(),
        )
        self.api = MagicMock()
        self.api.safe_error_metadata.return_value = {
            "http_status": None,
            "graph_error_code": None,
            "graph_error_subcode": None,
        }
        self.api.exchange_user_access_token.return_value = {
            "access_token": "synthetic-returned-user-token",
            "expires_in": None,
            "provider_expiry_state": MetaProviderExpiryState.NO_FINITE_EXPIRY,
            "provider_expires_at": None,
            "data_access_expires_at": self.now + timedelta(days=25),
        }
        self.service = MetaTokenLifecycleService(api_client=self.api)
        self.locked_queryset = MagicMock()
        self.locked_queryset.get.return_value = self.credential

    def _run_manual(self, *, current=None, confirm=True):
        self.locked_queryset.get.return_value = current or self.credential
        with (
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-original-user-token",
            ),
            patch(
                "apps.integrations.meta.lifecycle.encrypt_token",
                return_value="encrypted-replacement-user-token",
            ) as encrypt,
            patch.object(
                MetaAccountCredential.objects,
                "get",
                return_value=self.credential,
            ) as get_credential,
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                return_value=self.locked_queryset,
            ),
            patch.object(
                self.service,
                "_acquire_user_renewal_lock",
                return_value="synthetic-lock-owner",
            ) as acquire_lock,
            patch.object(self.service, "_release_user_renewal_lock") as release_lock,
            patch(
                "apps.integrations.meta.lifecycle.transaction.atomic",
                return_value=nullcontext(),
            ),
        ):
            outcome = self.service._replace_no_finite_user_credential_for_controlled_test(
                self.credential.id,
                expected_organization_id="ORG000034",
                expected_provider_user_id="meta-user-123",
                confirm_external_exchange=confirm,
            )
        return outcome, encrypt, get_credential, acquire_lock, release_lock

    def _set_finite_result(self):
        self.api.exchange_user_access_token.return_value = {
            "access_token": "synthetic-returned-user-token",
            "expires_in": 30 * 24 * 60 * 60,
            "provider_expiry_state": MetaProviderExpiryState.FINITE,
            "provider_expires_at": timezone.now() + timedelta(days=30),
            "data_access_expires_at": timezone.now() + timedelta(days=25),
        }

    def test_manual_replacement_persists_valid_finite_result(self):
        self._set_finite_result()

        outcome, encrypt, _get, _acquire, release = self._run_manual()

        self.assertEqual(outcome, "renewed")
        self.api.exchange_user_access_token.assert_called_once_with(
            access_token="synthetic-original-user-token",
            required_permissions=("pages_show_list", "pages_manage_posts"),
            expected_user_id="meta-user-123",
        )
        encrypt.assert_called_once_with("synthetic-returned-user-token")
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.FINITE,
        )
        self.assertIsNotNone(self.credential.token_expires_at)
        self.assertIsNotNone(self.credential.last_user_token_renewed_at)
        self.assertFalse(settings.META_USER_TOKEN_AUTO_RENEWAL_ENABLED)
        release.assert_called_once_with(
            self.credential.id,
            "synthetic-lock-owner",
        )

    def test_manual_replacement_persists_valid_no_finite_result(self):
        outcome, _encrypt, _get, _acquire, release = self._run_manual()

        self.assertEqual(outcome, "renewed")
        self.assertIsNone(self.credential.token_expires_at)
        self.assertEqual(
            self.credential.provider_expiry_state,
            MetaProviderExpiryState.NO_FINITE_EXPIRY,
        )
        self.assertIsNone(self.credential.provider_expires_at)
        self.assertIsNotNone(self.credential.data_access_expires_at)
        self.assertIsNotNone(self.credential.last_user_token_renewed_at)
        self.assertFalse(settings.META_USER_TOKEN_AUTO_RENEWAL_ENABLED)
        release.assert_called_once()

    def test_confirmation_and_provider_identity_are_required(self):
        with self.assertRaises(ValueError):
            self.service._replace_no_finite_user_credential_for_controlled_test(
                self.credential.id,
                expected_organization_id="ORG000034",
                expected_provider_user_id="meta-user-123",
            )
        self.api.exchange_user_access_token.assert_not_called()

        direct_outcome = self.service._renew_user_credential(
            self.credential.id,
            required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            allow_confirmed_no_finite_source=True,
            expected_organization_id="ORG000034",
            expected_provider_user_id="meta-user-123",
        )
        self.assertEqual(direct_outcome, "skipped")
        self.api.exchange_user_access_token.assert_not_called()

        for provider_user_id, expected_user_id in (
            ("", "meta-user-123"),
            ("other-meta-user", "meta-user-123"),
        ):
            with self.subTest(provider_user_id=provider_user_id):
                self.credential.social_connection.provider_user_id = provider_user_id
                outcome, _encrypt, _get, _acquire, release = self._run_manual()
                self.assertEqual(outcome, "skipped")
                self.api.exchange_user_access_token.assert_not_called()
                self.credential.save.assert_not_called()
                release.assert_called_once()
                self.credential.social_connection.provider_user_id = "meta-user-123"

        self.credential.social_connection.organization.organization_id = "OTHER-ORG"
        outcome, _encrypt, _get, _acquire, release = self._run_manual()
        self.assertEqual(outcome, "skipped")
        self.api.exchange_user_access_token.assert_not_called()
        release.assert_called_once()
        self.credential.social_connection.organization.organization_id = "ORG000034"

        with self.assertRaises(ValueError):
            self.service._replace_no_finite_user_credential_for_controlled_test(
                self.credential.id,
                expected_organization_id="ORG000034",
                expected_provider_user_id=" ",
                confirm_external_exchange=True,
            )

    def test_invalid_returned_token_preserves_original_credential(self):
        original = dict(vars(self.credential))
        self.api.exchange_user_access_token.return_value = {
            "access_token": "",
            "expires_in": None,
            "provider_expiry_state": MetaProviderExpiryState.NO_FINITE_EXPIRY,
            "provider_expires_at": None,
            "data_access_expires_at": timezone.now() + timedelta(days=25),
        }

        outcome, encrypt, _get, _acquire, release = self._run_manual()

        self.assertEqual(outcome, "retry")
        self.assertEqual(vars(self.credential), original)
        self.credential.save.assert_not_called()
        encrypt.assert_not_called()
        release.assert_called_once()

    def test_missing_permissions_validation_failure_preserves_credential(self):
        original = dict(vars(self.credential))
        self.api.exchange_user_access_token.side_effect = MetaAPIError(
            "Returned token did not pass permission validation."
        )

        outcome, encrypt, _get, _acquire, release = self._run_manual()

        self.assertEqual(outcome, "retry")
        self.assertEqual(vars(self.credential), original)
        self.credential.save.assert_not_called()
        encrypt.assert_not_called()
        release.assert_called_once()

    def test_expired_data_access_result_preserves_credential(self):
        original = dict(vars(self.credential))
        self.api.exchange_user_access_token.return_value[
            "data_access_expires_at"
        ] = timezone.now() - timedelta(seconds=1)

        outcome, encrypt, _get, _acquire, release = self._run_manual()

        self.assertEqual(outcome, "retry")
        self.assertEqual(vars(self.credential), original)
        self.credential.save.assert_not_called()
        encrypt.assert_not_called()
        release.assert_called_once()

    def test_redis_lock_unavailable_does_not_exchange(self):
        with patch.object(
            self.service,
            "_acquire_user_renewal_lock",
            side_effect=RuntimeError("synthetic Redis error"),
        ):
            outcome = self.service._replace_no_finite_user_credential_for_controlled_test(
                self.credential.id,
                expected_organization_id="ORG000034",
                expected_provider_user_id="meta-user-123",
                confirm_external_exchange=True,
            )

        self.assertEqual(outcome, "retry")
        self.api.exchange_user_access_token.assert_not_called()
        self.credential.save.assert_not_called()

    def test_stale_credential_is_not_overwritten(self):
        concurrent = SimpleNamespace(
            **{
                **vars(self.credential),
                "access_token": "encrypted-concurrent-credential",
                "save": MagicMock(),
            }
        )
        original = dict(vars(self.credential))

        outcome, encrypt, _get, _acquire, release = self._run_manual(
            current=concurrent
        )

        self.assertEqual(outcome, "stale")
        self.assertEqual(vars(self.credential), original)
        concurrent.save.assert_not_called()
        encrypt.assert_called_once()
        release.assert_called_once()

    def test_meta_exchange_failure_preserves_original_credential(self):
        original = dict(vars(self.credential))
        self.api.exchange_user_access_token.side_effect = RuntimeError(
            "synthetic provider transport failure"
        )

        outcome, encrypt, _get, _acquire, release = self._run_manual()

        self.assertEqual(outcome, "retry")
        self.assertEqual(vars(self.credential), original)
        self.credential.save.assert_not_called()
        encrypt.assert_not_called()
        release.assert_called_once()

    def test_automatic_renewal_still_skips_no_finite_credentials(self):
        with (
            patch.object(
                self.service,
                "_acquire_user_renewal_lock",
                return_value="synthetic-lock-owner",
            ),
            patch.object(
                MetaAccountCredential.objects,
                "get",
                return_value=self.credential,
            ),
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                return_value=self.locked_queryset,
            ),
            patch.object(self.service, "_release_user_renewal_lock"),
            patch(
                "apps.integrations.meta.lifecycle.decrypt_token",
                return_value="synthetic-original-user-token",
            ),
        ):
            outcome = self.service._renew_user_credential(
                self.credential.id,
                required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            )

        self.assertEqual(outcome, "skipped")
        self.api.exchange_user_access_token.assert_not_called()
        self.credential.save.assert_not_called()
        self.assertFalse(settings.META_USER_TOKEN_AUTO_RENEWAL_ENABLED)


class MetaUserRenewalRedisLockTests(SimpleTestCase):
    class FakeRedis:
        def __init__(self):
            self.values = {}
            self.expirations = {}
            self.now = 0

        def set(self, key, value, *, nx, ex):
            if nx and key in self.values and self.expirations[key] > self.now:
                return False
            self.values[key] = value.encode("utf-8")
            self.expirations[key] = self.now + ex
            return True

        def expire_old_keys(self):
            for key, expires_at in list(self.expirations.items()):
                if expires_at <= self.now:
                    self.values.pop(key, None)
                    self.expirations.pop(key, None)

        def eval(self, script, numkeys, key, expected_owner):
            self.expire_old_keys()
            if self.values.get(key) == expected_owner.encode("utf-8"):
                del self.values[key]
                self.expirations.pop(key, None)
                return 1
            return 0

    @override_settings(CELERY_TASK_TIME_LIMIT=1800)
    def test_lock_lease_exceeds_task_limit_and_old_owner_cannot_release_new_lock(self):
        service = MetaTokenLifecycleService(api_client=MagicMock())
        fake_redis = self.FakeRedis()
        with (
            patch.object(MetaTokenLifecycleService, "LOCK_TIMEOUT_SECONDS", 300),
            patch.object(
                service,
                "_get_user_renewal_redis_client",
                return_value=fake_redis,
            ),
        ):
            first_owner = service._acquire_user_renewal_lock("credential-a")
            key = cache.make_key("meta:user-token-renewal:credential-a")
            self.assertEqual(fake_redis.expirations[key], 2100)
            self.assertIsNone(service._acquire_user_renewal_lock("credential-a"))

            fake_redis.now = 2101
            second_owner = service._acquire_user_renewal_lock("credential-a")
            self.assertNotEqual(first_owner, second_owner)

            service._release_user_renewal_lock("credential-a", first_owner)
            self.assertIn(key, fake_redis.values)
            service._release_user_renewal_lock("credential-a", second_owner)
            self.assertNotIn(key, fake_redis.values)

    def test_redis_client_uses_configured_public_url_and_database_without_cache_serializer(self):
        service = MetaTokenLifecycleService(api_client=MagicMock())
        sentinel = object()
        with (
            override_settings(
                CACHES={
                    "default": {
                        "BACKEND": "django.core.cache.backends.redis.RedisCache",
                        "LOCATION": "redis://redis.example.invalid:6379/0",
                        "OPTIONS": {"db": 2},
                    }
                }
            ),
            patch("apps.integrations.meta.lifecycle.redis.Redis.from_url", return_value=sentinel) as from_url,
        ):
            self.assertIs(service._get_user_renewal_redis_client(), sentinel)

        from_url.assert_called_once_with(
            "redis://redis.example.invalid:6379/0",
            db=2,
        )


class MetaUserRenewalRunCounterTests(SimpleTestCase):
    def test_user_renewal_aggregates_map_to_separate_run_fields(self):
        from apps.integrations.meta.tasks import _user_renewal_run_counters

        run_fields = {field.name for field in MetaTokenMaintenanceRun._meta.fields}
        self.assertTrue(
            {
                "user_renewed",
                "user_skipped",
                "user_locked",
                "user_stale",
                "user_retry",
            }.issubset(run_fields)
        )
        self.assertEqual(
            _user_renewal_run_counters(
                {"renewed": 2, "skipped": 3, "locked": 4, "stale": 5, "retry": 6}
            ),
            {
                "user_renewed": 2,
                "user_skipped": 3,
                "user_locked": 4,
                "user_stale": 5,
                "user_retry": 6,
            },
        )


class MetaUserCredentialEligibilityQueryTests(SimpleTestCase):
    @staticmethod
    def _leaves(node):
        if isinstance(node, Q):
            for child in node.children:
                yield from MetaUserCredentialEligibilityQueryTests._leaves(child)
        else:
            yield node

    def test_expiry_query_requires_future_provider_and_data_access_expiry(self):
        now = timezone.now()
        eligibility = meta_user_credential_expiry_eligibility_q(now)
        leaves = set(self._leaves(eligibility))

        self.assertIn(("data_access_expires_at__gt", now), leaves)
        self.assertIn(("token_expires_at__isnull", True), leaves)
        self.assertIn(("token_expires_at__gt", now), leaves)

        state_alternatives = [
            child
            for child in eligibility.children
            if isinstance(child, Q)
            and child.connector == Q.OR
            and any(
                key == "provider_expiry_state"
                for key, _value in self._leaves(child)
                if isinstance(key, str)
            )
        ]
        self.assertEqual(len(state_alternatives), 1)
        alternatives = state_alternatives[0]
        self.assertEqual(alternatives.connector, Q.OR)
        finite, no_finite = alternatives.children
        finite_leaves = set(self._leaves(finite))
        no_finite_leaves = set(self._leaves(no_finite))

        self.assertIn(
            ("provider_expiry_state", MetaProviderExpiryState.FINITE),
            finite_leaves,
        )
        self.assertIn(("provider_expires_at__gt", now), finite_leaves)
        self.assertIn(
            ("provider_expiry_state", MetaProviderExpiryState.NO_FINITE_EXPIRY),
            no_finite_leaves,
        )
        self.assertIn(("provider_is_valid", True), no_finite_leaves)
        self.assertIn(("provider_expires_at__isnull", True), no_finite_leaves)
        self.assertNotIn(("provider_expires_at__isnull", True), finite_leaves)


class MetaDisconnectDetectionUnitTests(SimpleTestCase):
    """Database-independent checks for automatic Meta credential invalidation."""

    def make_page(self):
        organization = SimpleNamespace(pk="org-1")
        connection = SimpleNamespace(pk="connection-1", organization=organization)
        account = SimpleNamespace(
            pk="page-1",
            platform="facebook",
            is_deleted=False,
            platform_account_id="synthetic-page-id",
            account_name="Synthetic Page",
            username="synthetic_page",
            connection=connection,
            organization=organization,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
            save=MagicMock(),
        )
        credential = SimpleNamespace(
            id="page-credential-1",
            pk="page-credential-1",
            credential_type=MetaCredentialType.PAGE,
            status=MetaCredentialStatus.ACTIVE,
            access_token="synthetic-encrypted-page-token",
            social_account=account,
            save=MagicMock(),
        )
        return organization, connection, account, credential

    def test_authentication_failure_and_failed_recovery_invalidates_page_and_notifies(self):
        _organization, _connection, account, page = self.make_page()
        parent = SimpleNamespace(status=MetaCredentialStatus.ACTIVE)
        auth_error = MetaAPIError(
            "Synthetic authentication failure",
            status_code=400,
            error_payload={"error": {"code": 190}},
        )
        api = MagicMock()
        api.safe_error_metadata.return_value = {
            "http_status": 400,
            "graph_error_code": 190,
            "graph_error_subcode": None,
        }
        service = MetaTokenLifecycleService(api_client=api)
        service._acquire_lock = MagicMock(return_value="synthetic-lock")
        service._release_lock = MagicMock()
        service._get_parent_user_credential = MagicMock(return_value=parent)
        service._reissue_page_token = MagicMock(return_value="synthetic-reissued-token")
        service._validate_page_token = MagicMock(side_effect=[auth_error, auth_error])

        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = page
        with (
            patch("apps.integrations.meta.lifecycle.MetaAccountCredential.objects.get", return_value=page),
            patch("apps.integrations.meta.lifecycle.MetaAccountCredential.objects.select_for_update", manager.select_for_update),
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="synthetic-page-token"),
            patch.object(
                service,
                "_mark_page_invalid",
                side_effect=lambda *, credential_id: MetaTokenLifecycleService._mark_page_invalid.__wrapped__(
                    service,
                    credential_id=credential_id,
                ),
            ),
            patch("apps.notifications.services.record_social_credential_reconnect_required") as notify,
            patch("apps.integrations.meta.lifecycle.transaction.atomic", return_value=nullcontext()),
        ):
            outcome = service.process_page_credential(page)

        self.assertEqual(outcome, "invalid")
        self.assertEqual(page.status, MetaCredentialStatus.INVALID)
        self.assertEqual(page.access_token, "synthetic-encrypted-page-token")
        self.assertEqual(parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(account.status, SocialAccountStatus.ERROR)
        self.assertFalse(account.is_valid)
        notify.assert_called_once_with(
            organization=account.organization,
            scope="facebook-page",
            subject_id=account.pk,
            platform="facebook",
            account_name=account.account_name,
        )
        service._validate_page_token.assert_has_calls(
            [
                call(page_id="synthetic-page-id", page_access_token="synthetic-page-token"),
                call(page_id="synthetic-page-id", page_access_token="synthetic-reissued-token"),
            ]
        )

    def test_parent_user_invalidation_is_connection_scoped_and_does_not_revoke_pages(self):
        _organization, connection, account, page = self.make_page()
        parent = SimpleNamespace(
            pk="user-credential-1",
            status=MetaCredentialStatus.ACTIVE,
            save=MagicMock(),
            social_connection=connection,
        )
        sibling_account = SimpleNamespace(pk="page-2", status=SocialAccountStatus.CONNECTED)
        sibling_page = SimpleNamespace(
            id="page-credential-2",
            status=MetaCredentialStatus.ACTIVE,
            access_token="synthetic-sibling-page-token",
            social_account=sibling_account,
            save=MagicMock(),
        )
        error = MetaAPIError(
            "Synthetic parent token rejected",
            status_code=400,
            error_payload={"error": {"code": 190}},
        )
        api = MagicMock()
        api.safe_error_metadata.return_value = {
            "http_status": 400,
            "graph_error_code": 190,
            "graph_error_subcode": None,
        }
        service = MetaTokenLifecycleService(api_client=api)
        service._get_parent_user_credential = MagicMock(return_value=parent)
        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = parent

        with (
            patch("apps.integrations.meta.lifecycle.MetaAccountCredential.objects.select_for_update", manager.select_for_update),
            patch("apps.integrations.meta.lifecycle.transaction.atomic", return_value=nullcontext()),
            patch("apps.notifications.services.record_social_credential_reconnect_required") as notify,
        ):
            service._mark_parent_reconnect_needed(page, error)

        self.assertEqual(parent.status, MetaCredentialStatus.INVALID)
        self.assertEqual(page.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(page.access_token, "synthetic-encrypted-page-token")
        self.assertEqual(sibling_page.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(sibling_page.access_token, "synthetic-sibling-page-token")
        notify.assert_called_once_with(
            organization=connection.organization,
            scope="meta-connection",
            subject_id=connection.pk,
            platform="facebook",
        )
