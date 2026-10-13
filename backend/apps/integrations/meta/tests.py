import logging
import uuid
from datetime import timedelta
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.integrations.meta.client import MetaAPIClient
from apps.integrations.meta.exceptions import MetaAPIError
from apps.integrations.meta.lifecycle import MetaTokenLifecycleService
from apps.integrations.meta.models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaTokenMaintenanceRun,
)
from apps.integrations.meta.selectors import get_meta_connection_credential
from apps.integrations.meta.services import (
    MetaAccountDiscoveryService,
    MetaOAuthService,
    MetaSocialAccountService,
)
from apps.integrations.meta.views import (
    MetaOAuthCallbackAPIView,
    MetaOAuthSelectionAPIView,
    MetaOAuthSelectionConfirmAPIView,
)
from apps.organizations.models import Organization
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
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
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-empty")

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
        service = self.make_service(
            {
                "data": [
                    {
                        "id": "page-1",
                        "name": "Page One",
                        "access_token": PAGE_TOKEN_CANARY,
                    }
                ],
                "paging": {"next": next_url},
            }
        )

        with self.assertLogs("apps.integrations.meta.services", level="INFO") as logs:
            result = service.discover_accounts(correlation_id="correlation-next")

        output = "\n".join(logs.output)
        self.assertEqual(len(result.accounts), 1)
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
        service.client.get_pages = lambda **kwargs: pages
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
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-2")

        output = "\n".join(logs.output)
        self.assertIn("page_access_token_present=False", output)
        self.assertIn("outcome=skipped_missing_page_token", output)

    def test_page_missing_id_is_skipped_and_only_token_presence_is_logged(self):
        service = self.make_discovery(
            [{"name": "Unidentified Page", "access_token": PAGE_TOKEN_CANARY}]
        )

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-3")

        output = "\n".join(logs.output)
        self.assertIn("page_name=Unidentified Page", output)
        self.assertIn("page_access_token_present=True", output)
        self.assertIn("outcome=skipped_missing_id", output)
        self.assertNotIn(PAGE_TOKEN_CANARY, output)

    def test_invalid_page_entry_is_skipped(self):
        service = self.make_discovery([None])

        with self.assertLogs("apps.integrations.meta.services", level="WARNING") as logs:
            with self.assertRaises(MetaAPIError):
                service.discover_accounts(correlation_id="correlation-4")

        self.assertIn("outcome=skipped_invalid_entry", "\n".join(logs.output))

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

    def test_page_lock_release_atomically_deletes_only_its_own_lock(self):
        from django.core.cache import cache

        class FakeRedisClient:
            def __init__(self):
                self.values = {}

            def eval(self, script, key_count, key, expected_value):
                self.script = script
                self.key_count = key_count
                if self.values.get(key) == expected_value:
                    del self.values[key]
                    return 1
                return 0

        redis_client = FakeRedisClient()
        lock_key = cache.make_key("meta:page-token-lifecycle:page-1")
        expected_owner = cache._cache._serializer.dumps("owner-a")
        other_owner = cache._cache._serializer.dumps("owner-b")
        redis_client.values[lock_key] = other_owner

        with patch(
            "apps.integrations.meta.lifecycle.cache._cache.get_client",
            return_value=redis_client,
        ):
            self.service._release_lock("page-1", "owner-a")
            self.assertEqual(redis_client.values[lock_key], other_owner)

            redis_client.values[lock_key] = expected_owner
            self.service._release_lock("page-1", "owner-a")

        self.assertNotIn(lock_key, redis_client.values)
        self.assertEqual(redis_client.key_count, 1)
        self.assertIn("redis.call('GET'", redis_client.script)
        self.assertIn("redis.call('DEL'", redis_client.script)

    def test_shared_parent_is_health_checked_once_for_multiple_pages(self):
        self.page_credentials.append(self.create_page("page-2", "Test Page 2"))
        with (
            patch.object(self.api, "diagnose_token", wraps=self.api.diagnose_token) as debug,
            patch("apps.integrations.meta.lifecycle.decrypt_token", return_value="token-canary"),
        ):
            result = self.service.refresh_due_credentials()
        self.assertEqual(debug.call_count, 1)
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
        self.api.diagnose_token = lambda **kwargs: {"type": "USER", "is_valid": False}
        result = self.run_lifecycle()
        self.parent.refresh_from_db()
        self.page_credentials[0].refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.INVALID)
        self.assertEqual(self.page_credentials[0].status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(result["reconnect_needed"], 1)
        self.assertTrue(
            SocialAccountLifecycleStatus.needs_reconnect(
                social_account=self.page_credentials[0].social_account,
                credential_status=MetaCredentialStatus.ACTIVE.lower(),
            )
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
        self.api.diagnose_token = lambda **kwargs: _raise(
            MetaAPIError("temporary failure", status_code=503)
        )
        result = self.run_lifecycle()
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.status, MetaCredentialStatus.ACTIVE)
        self.assertEqual(self.parent.granted_permissions, [
            {"permission": "pages_show_list", "status": "granted"}
        ])
        self.assertEqual(result["parent_retry"], 1)

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

    def test_page_recovery_is_deferred_and_does_not_save_token_if_parent_invalid(self):
        self.parent.status = MetaCredentialStatus.INVALID
        self.parent.save(update_fields=["status"])
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
        self.assertEqual(outcome, "reconnect_needed")
        save_token.assert_not_called()
        self.page_credentials[0].refresh_from_db()
        self.assertEqual(self.page_credentials[0].status, MetaCredentialStatus.ACTIVE)

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

    def test_save_user_credential_resets_provider_health_on_reconnect(self):
        previous_expiry = self.parent.token_expires_at
        previous_verified_at = timezone.now() - timedelta(days=2)
        self.parent.last_verified_at = previous_verified_at
        self.parent.provider_token_type = "USER"
        self.parent.provider_is_valid = True
        self.parent.provider_expires_at = timezone.now() + timedelta(days=20)
        self.parent.data_access_expires_at = timezone.now() + timedelta(days=15)
        self.parent.last_health_check_at = timezone.now() - timedelta(days=1)
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
        self.assertEqual(result.provider_token_type, "")
        self.assertIsNone(result.provider_is_valid)
        self.assertIsNone(result.provider_expires_at)
        self.assertIsNone(result.data_access_expires_at)
        self.assertIsNone(result.last_health_check_at)
        self.assertEqual(result.granted_permissions, [])

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
