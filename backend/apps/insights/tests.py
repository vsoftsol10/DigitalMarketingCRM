import json
import logging
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import requests
from django.db import IntegrityError, connection, transaction
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.integrations.instagram.exceptions import InstagramAPIError, InstagramIntegrationError
from apps.integrations.meta.client import MetaAPIClient
from apps.integrations.meta.exceptions import MetaAPIError, MetaIntegrationError
from apps.organizations.models import Organization
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)
from .models import (
    InsightsAccountSnapshot,
    InsightsContentSnapshotItem,
    InsightsMediaSnapshot,
    InsightsSnapshotSlot,
    InsightsSyncState,
    InsightsSyncStatus,
    InsightsSyncWork,
    InsightsSyncWorkStage,
    InsightsSyncWorkStatus,
)
from .providers import (
    CONTENT_PAGE_SIZE,
    MAX_CONTENT_PAGES_PER_REQUEST,
    _make_content_cursor,
    fetch_provider_insights,
)


class FacebookContentDiagnosticLogTests(SimpleTestCase):
    def test_permission_error_logs_allowlisted_metadata_and_keeps_normalized_result(self):
        from .sync_service import _facebook_content_provider_failure

        claim = {
            "sync_state_id": "sync-state-safe-id",
            "work_id": "work-safe-id",
            "stage": "content",
        }
        error = MetaAPIError(
            "Raw exception secret must not be logged",
            status_code=403,
            error_payload={
                "error": {
                    "code": 200,
                    "error_subcode": 10,
                    "type": "OAuthException",
                    "message": (
                        "Permissions error access_token=DIAG_ACCESS_SECRET "
                        "Bearer DIAG_BEARER_SECRET "
                        "https://meta.example/posts?access_token=DIAG_URL_SECRET "
                        "12345678901234 user@example.test"
                    ),
                    "fbtrace_id": "TRACE_ABC123",
                    "private_payload_field": "DIAG_RAW_PAYLOAD_SECRET",
                },
            },
        )

        with (
            patch("apps.insights.sync_service.mark_content_sync_terminal") as mark_terminal,
            self.assertLogs("apps.insights.sync_service", level="WARNING") as captured,
        ):
            result = _facebook_content_provider_failure(
                claim,
                error,
                social_account_id="social-account-safe-id",
            )

        self.assertEqual(result, {"status": "partial", "error_code": "permission_required"})
        mark_terminal.assert_called_once_with(
            claim=claim,
            status=InsightsSyncStatus.PARTIAL,
            error_code="permission_required",
            reason="pages_read_engagement",
        )
        self.assertEqual(len(captured.records), 1)
        record = captured.records[0]
        rendered = record.getMessage()
        self.assertIn("operation=facebook_page_posts", rendered)
        self.assertIn("social_account_id=social-account-safe-id", rendered)
        self.assertIn("sync_state_id=sync-state-safe-id", rendered)
        self.assertIn("work_id=work-safe-id", rendered)
        self.assertIn("stage=CONTENT", rendered)
        self.assertIn("http_status=403", rendered)
        self.assertIn("meta_error_code=200", rendered)
        self.assertIn("meta_error_subcode=10", rendered)
        self.assertIn("meta_error_type=OAuthException", rendered)
        self.assertIn("fbtrace_id=TRACE_ABC123", rendered)
        self.assertIn("normalized_classification=permission_required", rendered)
        logged_message = json.loads(
            rendered.split("meta_error_message=", 1)[1].split(" fbtrace_id=", 1)[0]
        )
        self.assertLessEqual(len(logged_message), 300)
        self.assertIn("access_token=[redacted]", logged_message)
        self.assertIn("Bearer [redacted]", logged_message)
        self.assertIn("[redacted-url]", logged_message)
        self.assertIn("[redacted-id]", logged_message)
        self.assertIn("[redacted-email]", logged_message)
        self.assertFalse(hasattr(record, "operation"))
        for sensitive_value in (
            "DIAG_ACCESS_SECRET",
            "DIAG_BEARER_SECRET",
            "DIAG_URL_SECRET",
            "DIAG_RAW_PAYLOAD_SECRET",
            "12345678901234",
            "user@example.test",
            "Raw exception secret",
        ):
            self.assertNotIn(sensitive_value, rendered)

    def test_missing_diagnostic_fields_render_as_unknown(self):
        from .sync_service import _facebook_content_provider_failure

        with (
            patch("apps.insights.sync_service.mark_content_sync_terminal"),
            self.assertLogs("apps.insights.sync_service", level="WARNING") as captured,
        ):
            _facebook_content_provider_failure(
                {"stage": "content"},
                MetaAPIError("No response metadata."),
                social_account_id=None,
            )

        rendered = captured.records[0].getMessage()
        for field in (
            "social_account_id",
            "sync_state_id",
            "work_id",
            "http_status",
            "meta_error_code",
            "meta_error_subcode",
            "meta_error_type",
            "fbtrace_id",
        ):
            self.assertIn(f"{field}=unknown", rendered)
        self.assertIn("meta_error_message=null", rendered)


class InsightsContentInstrumentationTests(SimpleTestCase):
    @patch("apps.integrations.instagram.client.requests.get")
    def test_instagram_http_timing_log_is_sanitized_and_response_is_unchanged(self, get):
        from apps.integrations.instagram.client import InstagramAPIClient

        client = InstagramAPIClient.__new__(InstagramAPIClient)
        client.timeout = 10
        client._pace_graph_request = Mock()
        expected_response = {"data": [{"name": "reach", "values": [{"value": 7}]}]}
        response = Mock(status_code=200)
        client._handle_response = Mock(return_value=expected_response)
        get.return_value = response

        with self.assertLogs("apps.integrations.instagram.client", level="DEBUG") as captured:
            result = client.graph_get(
                "private-account-id/media",
                access_token="LATENCY_TEST_SECRET_TOKEN",
                params={"after": "PRIVATE_PROVIDER_CURSOR", "caption": "PRIVATE_POST_TEXT"},
            )

        self.assertIs(result, expected_response)
        rendered = "\n".join(record.getMessage() for record in captured.records)
        self.assertIn("operation=instagram_media_list", rendered)
        self.assertIn("http_status=200", rendered)
        self.assertNotIn("LATENCY_TEST_SECRET_TOKEN", rendered)
        self.assertNotIn("PRIVATE_PROVIDER_CURSOR", rendered)
        self.assertNotIn("PRIVATE_POST_TEXT", rendered)
        self.assertNotIn("private-account-id", rendered)

    def test_low_level_http_debug_logs_redact_tokens_and_authorization(self):
        access_token = "HTTP_LOG_ACCESS_TOKEN_SECRET"
        bearer_token = "HTTP_LOG_BEARER_TOKEN_SECRET"

        with self.assertLogs("urllib3.connectionpool", level="DEBUG") as captured:
            logging.getLogger("urllib3.connectionpool").debug(
                "GET https://graph.example.test/path?access_token=%s HTTP/1.1 200 42",
                access_token,
            )
        access_log = "\n".join(record.getMessage() for record in captured.records)
        self.assertIn("access_token=[redacted]", access_log)
        self.assertIn("HTTP/1.1 200 42", access_log)
        self.assertNotIn(access_token, access_log)

        with self.assertLogs("http.client", level="DEBUG") as captured:
            logging.getLogger("http.client").debug(
                "send: Authorization: Bearer %s Cookie: session=private-cookie",
                bearer_token,
            )
        auth_log = "\n".join(record.getMessage() for record in captured.records)
        self.assertIn("Authorization: [redacted]", auth_log)
        self.assertIn("Cookie: [redacted]", auth_log)
        self.assertNotIn(bearer_token, auth_log)
        self.assertNotIn("private-cookie", auth_log)


class FacebookPostInsightsParserTests(SimpleTestCase):
    @staticmethod
    def capture_diagnostic_shape(test_case, value, provider_metric="post_reactions_by_type_total"):
        from .sync_service import _facebook_post_insight_shape_diagnostic

        point = {"value": value}
        values = [point]
        with test_case.assertLogs("apps.insights.sync_service", level="WARNING") as captured:
            _facebook_post_insight_shape_diagnostic(
                provider_metric=provider_metric,
                period="lifetime",
                values=values,
                point=point,
                duplicate_name=False,
                classification="malformed_metric_response",
            )
        rendered = captured.records[0].getMessage()
        fields = {}
        for part in rendered.split(" "):
            if "=" in part:
                name, field_value = part.split("=", 1)
                fields[name] = field_value
        return fields, rendered

    @staticmethod
    def capture_shape_only(test_case, response):
        from .sync_service import _parse_facebook_post_insights

        with test_case.assertLogs("apps.insights.sync_service", level="WARNING") as captured:
            parsed = _parse_facebook_post_insights(response)
        fields = {}
        for part in captured.records[0].getMessage().split(" "):
            if "=" in part:
                name, value = part.split("=", 1)
                fields[name] = value
        return parsed, fields

    def test_lifetime_metrics_are_mapped_without_post_engagement(self):
        from .sync_service import _parse_facebook_post_insights

        parsed = _parse_facebook_post_insights({"data": [
            {"name": "post_total_media_view_unique", "period": "lifetime", "values": [{"value": 0}]},
            {"name": "post_media_view", "period": "lifetime", "values": [{"value": 24}]},
            {"name": "post_reactions_by_type_total", "period": "lifetime", "values": [{"value": {"like": 3}}]},
            {"name": "post_clicks", "period": "lifetime", "values": [{"value": 7}]},
            {"name": "post_clicks_by_type", "period": "lifetime", "values": [{"value": {"link clicks": 2}}]},
        ]})

        self.assertEqual(parsed["reach"]["value"], 0)
        self.assertEqual(parsed["reach"]["provider_metric"], "post_total_media_view_unique")
        self.assertEqual(parsed["reach"]["measurement"], "unique_media_viewers")
        self.assertEqual(parsed["reach"]["period"], "lifetime")
        self.assertEqual(parsed["views"]["value"], 24)
        self.assertEqual(parsed["views"]["provider_metric"], "post_media_view")
        self.assertEqual(parsed["reactions_by_type"]["value"], {"like": 3})
        self.assertEqual(parsed["reactions_by_type"]["provider_metric"], "post_reactions_by_type_total")
        self.assertEqual(parsed["clicks"]["value"], 7)
        self.assertEqual(parsed["clicks"]["provider_metric"], "post_clicks")
        self.assertEqual(parsed["clicks_by_type"]["value"], {"link clicks": 2})
        self.assertNotIn("engagement", parsed)

    def test_missing_metric_is_unavailable_with_provider_metadata(self):
        from .sync_service import _parse_facebook_post_insights

        parsed = _parse_facebook_post_insights({"data": [
            {"name": "post_media_view", "period": "lifetime", "values": [{"value": 5}]},
        ]})

        self.assertEqual(parsed["reach"]["availability"], "unavailable")
        self.assertIsNone(parsed["reach"]["value"])
        self.assertEqual(parsed["reach"]["reason"], "metric_not_returned")
        self.assertEqual(parsed["reach"]["provider_metric"], "post_total_media_view_unique")
        self.assertEqual(parsed["reach"]["period"], "lifetime")

    def test_malformed_metric_response_is_unavailable_not_zero(self):
        from .sync_service import _parse_facebook_post_insights

        parsed = _parse_facebook_post_insights({"data": [
            {"name": "post_total_media_view_unique", "period": "lifetime", "values": [{"value": "not-a-number"}]},
            {"name": "post_clicks", "period": "day", "values": [{"value": 3}]},
        ]})

        self.assertEqual(parsed["reach"]["availability"], "unavailable")
        self.assertEqual(parsed["reach"]["reason"], "malformed_metric_response")
        self.assertIsNone(parsed["reach"]["value"])
        self.assertEqual(parsed["clicks"]["availability"], "unavailable")
        self.assertEqual(parsed["clicks"]["reason"], "malformed_metric_response")

    def test_malformed_top_level_response_marks_metrics_unavailable(self):
        from .sync_service import _parse_facebook_post_insights

        parsed = _parse_facebook_post_insights({"data": None})

        self.assertTrue(all(metric["availability"] == "unavailable" for metric in parsed.values()))
        self.assertTrue(all(metric["reason"] == "malformed_insights_response" for metric in parsed.values()))

    def test_malformed_breakdown_logs_shape_without_values(self):
        private_marker = 8675309
        response = {"data": [
            {
                "name": "post_reactions_by_type_total",
                "period": "lifetime",
                "values": [{"value": [private_marker, "not-numeric"]}],
            },
        ]}

        parsed, shape = self.capture_shape_only(self, response)

        self.assertEqual(shape["metric"], "post_reactions_by_type_total")
        self.assertEqual(shape["period"], "lifetime")
        self.assertEqual(shape["values_type"], "list")
        self.assertEqual(shape["values_is_list"], "true")
        self.assertEqual(shape["values_length"], "1")
        self.assertEqual(shape["value_key_exists"], "true")
        self.assertEqual(shape["value_type"], "list")
        self.assertEqual(shape["value_shape"], "list")
        self.assertEqual(shape["numeric_leaf_count"], "1")
        self.assertEqual(shape["duplicate_metric_name"], "false")
        self.assertEqual(shape["normalized_classification"], "malformed_metric_response")
        self.assertNotIn(str(private_marker), str(shape))
        self.assertNotIn("not-numeric", str(shape))
        self.assertEqual(parsed["reactions_by_type"]["availability"], "unavailable")
        self.assertEqual(parsed["reactions_by_type"]["reason"], "malformed_metric_response")
        self.assertIsNone(parsed["reactions_by_type"]["value"])

    def test_nested_breakdown_diagnostic_logs_only_allowlisted_structure(self):
        unsafe_key = "post_message_private-marker"
        response = {"data": [
            {
                "name": "post_reactions_by_type_total",
                "period": "lifetime",
                "values": [{"value": {
                    "love": {unsafe_key: [17, "caption-marker", None]},
                    "like": {"total": 9},
                }}],
            },
        ]}

        _, shape = self.capture_shape_only(self, response)

        self.assertEqual(shape["top_level_key_count"], "2")
        self.assertEqual(shape["top_level_key_names"], "LIKE,LOVE")
        self.assertEqual(shape["nested_dict_count"], "2")
        self.assertEqual(shape["nested_list_count"], "1")
        self.assertEqual(shape["numeric_leaf_count"], "1")
        self.assertEqual(shape["string_leaf_count"], "0")
        self.assertEqual(shape["null_leaf_count"], "0")
        self.assertEqual(shape["max_depth"], "2+")
        self.assertEqual(shape["list_lengths"], "depth2:3")
        self.assertEqual(shape["nested_keys_known_metric_categories"], "false")
        self.assertNotIn(unsafe_key, str(shape))
        self.assertNotIn("caption-marker", str(shape))
        self.assertNotIn("17", str(shape))
        self.assertNotIn("9", str(shape))

    def test_unrecognized_breakdown_keys_are_not_logged(self):
        response = {"data": [
            {
                "name": "post_reactions_by_type_total",
                "period": "lifetime",
                "values": [{"value": {"user supplied text": "not-numeric"}}],
            },
        ]}

        _, shape = self.capture_shape_only(self, response)

        self.assertEqual(shape["top_level_key_count"], "1")
        self.assertEqual(shape["top_level_key_names"], "omitted")
        self.assertNotIn("user supplied text", str(shape))

    def test_structural_diagnostic_helper_shapes_never_include_metric_values(self):
        cases = (
            (
                "flat_dict",
                {"LIKE": 31415, "LOVE": 27182},
                {"top_level_key_count": "2", "top_level_key_names": "LIKE,LOVE", "numeric_leaf_count": "2", "nested_keys_known_metric_categories": "true"},
                ("31415", "27182"),
            ),
            (
                "nested_dict",
                {"LIKE": {"private_key": 12345}},
                {"nested_dict_count": "1", "numeric_leaf_count": "1", "max_depth": "2", "nested_keys_known_metric_categories": "false"},
                ("12345", "private_key"),
            ),
            (
                "nested_list",
                {"LOVE": [333, 444]},
                {"nested_list_count": "1", "list_lengths": "depth1:2", "numeric_leaf_count": "2", "max_depth": "2"},
                ("333", "444"),
            ),
            (
                "mixed_values",
                {"LIKE": 555, "LOVE": [666, "private-label", None], "WOW": {"private_key": 777}},
                {"nested_dict_count": "1", "nested_list_count": "1", "numeric_leaf_count": "3", "string_leaf_count": "1", "null_leaf_count": "1"},
                ("555", "666", "777", "private-label", "private_key"),
            ),
            (
                "empty_dict",
                {},
                {"top_level_key_count": "0", "top_level_key_names": "empty", "numeric_leaf_count": "0", "max_depth": "0"},
                (),
            ),
            (
                "null",
                None,
                {"value_shape": "null", "value_type": "null", "max_depth": "0", "top_level_key_count": "0"},
                (),
            ),
            (
                "unexpected_key",
                {"private-user-label": 98765},
                {"top_level_key_names": "omitted", "numeric_leaf_count": "1"},
                ("private-user-label", "98765"),
            ),
            (
                "excessive_nesting",
                {"LIKE": {"LOVE": {"WOW": 87654}}},
                {"max_depth": "2+", "nested_keys_known_metric_categories": "true"},
                ("87654",),
            ),
        )

        for label, value, expected_fields, forbidden in cases:
            with self.subTest(shape=label):
                fields, rendered = self.capture_diagnostic_shape(self, value)
                for name, expected in expected_fields.items():
                    self.assertEqual(fields[name], expected)
                for item in forbidden:
                    self.assertNotIn(item, rendered)
                self.assertIn("normalized_classification=malformed_metric_response", rendered)

    def test_missing_and_empty_breakdown_values_are_not_coerced(self):
        from .sync_service import _parse_facebook_post_insights

        response = {"data": [
            {
                "name": "post_reactions_by_type_total",
                "period": "lifetime",
                "values": [{"period": "lifetime"}],
            },
            {
                "name": "post_clicks_by_type",
                "period": "lifetime",
                "values": [{"value": {}}],
            },
        ]}

        parsed = _parse_facebook_post_insights(response)

        self.assertEqual(parsed["reactions_by_type"]["reason"], "metric_not_returned")
        self.assertIsNone(parsed["reactions_by_type"]["value"])
        self.assertEqual(parsed["clicks_by_type"]["reason"], "malformed_metric_response")
        self.assertIsNone(parsed["clicks_by_type"]["value"])

    def test_duplicate_breakdown_entry_is_unavailable_and_flagged(self):
        from .sync_service import _parse_facebook_post_insights

        response = {"data": [
            {"name": "post_clicks_by_type", "period": "lifetime", "values": [{"value": {"x": 1}}]},
            {"name": "post_clicks_by_type", "period": "lifetime", "values": [{"value": {"y": 2}}]},
        ]}

        with self.assertLogs("apps.insights.sync_service", level="WARNING") as captured:
            parsed = _parse_facebook_post_insights(response)

        self.assertEqual(parsed["clicks_by_type"]["availability"], "unavailable")
        self.assertEqual(parsed["clicks_by_type"]["reason"], "malformed_metric_response")
        diagnostic = next(
            record.getMessage()
            for record in captured.records
            if "metric=post_clicks_by_type" in record.getMessage()
        )
        self.assertIn("duplicate_metric_name=true", diagnostic)


class InsightsSnapshotModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="insights-snapshot-owner@example.com",
            first_name="Snapshot Owner",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INS-SNAPSHOT",
            name="Insights Snapshot Org",
            slug="insights-snapshot-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.account = self.create_account("ig-account-1")

    def create_account(self, platform_account_id):
        return SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id=platform_account_id,
            username=platform_account_id,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )

    def test_account_snapshot_keeps_zero_and_enforces_live_range_uniqueness(self):
        snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=date(2026, 8, 1),
            until=date(2026, 8, 31),
            api_version="v26.0",
            metrics={"reach": {"value": 0, "availability": "available", "reason": ""}},
            fetched_at=timezone.now(),
        )
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.metrics["reach"]["value"], 0)

        with self.assertRaises(IntegrityError), transaction.atomic():
            InsightsAccountSnapshot.objects.create(
                social_account=self.account,
                since=date(2026, 8, 1),
                until=date(2026, 8, 31),
                api_version="v26.0",
                metrics={},
                fetched_at=timezone.now(),
            )

    def test_account_snapshot_upsert_is_idempotent(self):
        from .sync_service import _save_account_snapshot

        for _ in range(2):
            _save_account_snapshot(
                account=self.account,
                since=date(2026, 8, 1),
                until=date(2026, 8, 31),
                metrics={"followers": {"value": 0, "availability": "available"}},
                follower_growth={"availability": "unavailable", "points": []},
                profile={"username": "test-account"},
            )

        self.assertEqual(InsightsAccountSnapshot.objects.filter(social_account=self.account).count(), 1)
        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        self.assertEqual(snapshot.metrics["followers"]["value"], 0)
        self.assertEqual(snapshot.profile_metadata["username"], "test-account")

    def test_partial_refresh_preserves_existing_account_snapshot(self):
        from .sync_service import _save_account_snapshot

        since = date(2026, 8, 1)
        until = date(2026, 8, 31)
        fetched_at = timezone.now() - timedelta(days=1)
        snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=since,
            until=until,
            api_version="v26.0",
            metrics={"followers": {"value": 0, "availability": "available"}},
            follower_growth={"availability": "available", "points": []},
            profile_metadata={"username": "saved-profile"},
            fetched_at=fetched_at,
        )

        _save_account_snapshot(
            account=self.account,
            since=since,
            until=until,
            metrics={"followers": {"value": None, "availability": "unavailable"}},
            follower_growth={"availability": "unavailable", "points": []},
            profile={"username": "partial-refresh"},
            preserve_existing=True,
        )

        snapshot.refresh_from_db()
        self.assertEqual(snapshot.metrics["followers"]["value"], 0)
        self.assertEqual(snapshot.metrics["followers"]["availability"], "available")
        self.assertEqual(snapshot.profile_metadata["username"], "saved-profile")
        self.assertEqual(snapshot.fetched_at, fetched_at)

    def test_account_snapshot_rejects_reversed_date_range(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InsightsAccountSnapshot.objects.create(
                social_account=self.account,
                since=date(2026, 9, 1),
                until=date(2026, 8, 31),
                api_version="v26.0",
                metrics={},
                fetched_at=timezone.now(),
            )

    def test_media_snapshot_is_unique_per_account_and_provider_media_id(self):
        values = {
            "social_account": self.account,
            "provider_media_id": "native-media-1",
            "api_version": "v26.0",
            "metrics": {"engagement": {"value": 0, "availability": "available", "reason": ""}},
            "fetched_at": timezone.now(),
        }
        media = InsightsMediaSnapshot.objects.create(**values)
        media.refresh_from_db()
        self.assertEqual(media.metrics["engagement"]["value"], 0)

        with self.assertRaises(IntegrityError), transaction.atomic():
            InsightsMediaSnapshot.objects.create(**values)

        other_account = self.create_account("ig-account-2")
        other_media = InsightsMediaSnapshot.objects.create(
            **{**values, "social_account": other_account},
        )
        self.assertNotEqual(media.social_account_id, other_media.social_account_id)

    def test_only_one_queued_or_syncing_state_per_account_range(self):
        values = {
            "social_account": self.account,
            "since": date(2026, 8, 1),
            "until": date(2026, 8, 31),
            "api_version": "v26.0",
            "status": InsightsSyncStatus.QUEUED,
        }
        InsightsSyncState.objects.create(**values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            InsightsSyncState.objects.create(
                **{**values, "status": InsightsSyncStatus.SYNCING},
            )

        InsightsSyncState.objects.filter(**values).update(
            status=InsightsSyncStatus.COMPLETE,
        )
        queued = InsightsSyncState.objects.create(**values)
        self.assertEqual(queued.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(queued.account_status, InsightsSyncStatus.QUEUED)
        self.assertEqual(queued.content_status, InsightsSyncStatus.QUEUED)

    def test_sync_state_enforces_date_range_and_progress_consistency(self):
        invalid_values = {
            "social_account": self.account,
            "since": date(2026, 9, 1),
            "until": date(2026, 8, 31),
            "api_version": "v26.0",
        }
        with self.assertRaises(IntegrityError), transaction.atomic():
            InsightsSyncState.objects.create(**invalid_values)

        with self.assertRaises(IntegrityError), transaction.atomic():
            InsightsSyncState.objects.create(
                **{
                    **invalid_values,
                    "since": date(2026, 8, 1),
                    "until": date(2026, 8, 31),
                    "items_discovered": 2,
                    "items_processed": 3,
                    "items_total": 4,
                },
            )


class FacebookNativeMetricSelectionTests(SimpleTestCase):
    @staticmethod
    def native_metric_points(*, provider_metric, period, values_by_date):
        return [
            {
                "date": end_date.isoformat(),
                "value": {
                    "value": value,
                    "availability": "available",
                    "period": period,
                    "provider_metric": provider_metric,
                    "source": "facebook",
                },
            }
            for end_date, value in values_by_date
        ]

    def select(self, points, *, provider_metric, label, period, until):
        from .sync_service import _facebook_native_metric

        return _facebook_native_metric(
            points,
            provider_metric=provider_metric,
            label=label,
            native_period=period,
            until=until,
        )

    def test_facebook_week_native_metric_selects_exact_until_date(self):
        until = date(2026, 10, 3)
        points = self.native_metric_points(
            provider_metric="page_media_view",
            period="week",
            values_by_date=[
                (date(2026, 9, 28), 1),
                (date(2026, 9, 29), 2),
                (date(2026, 9, 30), 3),
                (date(2026, 10, 1), 4),
                (date(2026, 10, 2), 5),
                (until, 6),
            ],
        )

        metric = self.select(
            points,
            provider_metric="page_media_view",
            label="Views",
            period="week",
            until=until,
        )

        self.assertEqual(metric["availability"], "available")
        self.assertEqual(metric["value"], 6)
        self.assertEqual(metric["period"], "week")
        self.assertEqual(metric["date"], until.isoformat())

    def test_facebook_week_native_metric_selection_is_independent_of_list_order(self):
        until = date(2026, 10, 3)
        points = self.native_metric_points(
            provider_metric="page_post_engagements",
            period="week",
            values_by_date=[
                (date(2026, 9, 28), 1),
                (date(2026, 9, 29), 2),
                (date(2026, 9, 30), 3),
                (date(2026, 10, 1), 4),
                (date(2026, 10, 2), 5),
                (until, 6),
            ],
        )

        metric = self.select(
            list(reversed(points)),
            provider_metric="page_post_engagements",
            label="Engagement",
            period="week",
            until=until,
        )

        self.assertEqual(metric["availability"], "available")
        self.assertEqual(metric["value"], 6)
        self.assertEqual(metric["date"], until.isoformat())

    def test_facebook_days_28_native_metric_selects_exact_until_among_multiple_points(self):
        from .sync_service import _facebook_native_reach_metric

        until = date(2026, 10, 3)
        points = self.native_metric_points(
            provider_metric="page_total_media_view_unique",
            period="days_28",
            values_by_date=[
                (date(2026, 9, 10), 10),
                (date(2026, 9, 24), 20),
                (until, 28),
            ],
        )

        metric = _facebook_native_reach_metric(
            points,
            provider_metric="page_total_media_view_unique",
            native_period="days_28",
            until=until,
        )

        self.assertEqual(metric["availability"], "available")
        self.assertEqual(metric["value"], 28)
        self.assertEqual(metric["period"], "days_28")
        self.assertEqual(metric["measurement"], "unique_media_viewers")

    def test_facebook_native_metric_without_until_candidate_is_unavailable(self):
        metric = self.select(
            self.native_metric_points(
                provider_metric="page_media_view",
                period="week",
                values_by_date=[(date(2026, 10, 1), 4), (date(2026, 10, 2), 5)],
            ),
            provider_metric="page_media_view",
            label="Views",
            period="week",
            until=date(2026, 10, 3),
        )

        self.assertEqual(metric["availability"], "unavailable")
        self.assertIsNone(metric["value"])
        self.assertEqual(metric["reason"], "native_window_not_returned")

    def test_facebook_native_metric_duplicate_until_candidates_are_ambiguous(self):
        until = date(2026, 10, 3)
        metric = self.select(
            self.native_metric_points(
                provider_metric="page_media_view",
                period="week",
                values_by_date=[(until, 6), (until, 7)],
            ),
            provider_metric="page_media_view",
            label="Views",
            period="week",
            until=until,
        )

        self.assertEqual(metric["availability"], "unavailable")
        self.assertIsNone(metric["value"])
        self.assertEqual(metric["reason"], "ambiguous_native_aggregate")

    def test_facebook_native_metric_preserves_exact_until_zero(self):
        until = date(2026, 10, 3)
        metric = self.select(
            self.native_metric_points(
                provider_metric="page_media_view",
                period="week",
                values_by_date=[(date(2026, 10, 2), 4), (until, 0)],
            ),
            provider_metric="page_media_view",
            label="Views",
            period="week",
            until=until,
        )

        self.assertEqual(metric["availability"], "available")
        self.assertEqual(metric["value"], 0)
        self.assertEqual(metric["date"], until.isoformat())

    def test_facebook_native_metric_still_validates_provider_period(self):
        until = date(2026, 10, 3)
        metric = self.select(
            self.native_metric_points(
                provider_metric="page_media_view",
                period="days_28",
                values_by_date=[(until, 8)],
            ),
            provider_metric="page_media_view",
            label="Views",
            period="week",
            until=until,
        )

        self.assertEqual(metric["availability"], "unavailable")
        self.assertEqual(metric["reason"], "malformed_metric_response")


class FacebookAccountSnapshotSyncTests(TestCase):
    since = date(2026, 9, 1)
    until = date(2026, 9, 7)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="facebook-insights-sync@example.com",
            first_name="Facebook Insights",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-FB-INS-SYNC",
            name="Facebook Insights Org",
            slug="facebook-insights-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="facebook-page-1",
            username="facebook-page",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        self.state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
        )
        self.work = InsightsSyncWork.objects.create(
            sync_state=self.state,
            stage=InsightsSyncWorkStage.ACCOUNT,
            generation=1,
            status=InsightsSyncWorkStatus.DISPATCHED,
        )
        self.content_work = InsightsSyncWork.objects.create(
            sync_state=self.state,
            stage=InsightsSyncWorkStage.CONTENT,
            generation=1,
            status=InsightsSyncWorkStatus.PENDING,
            next_attempt_at=timezone.now(),
        )

    def insights_payload(self, *, omit=(), engagement_values=None, view_values=None):
        number_of_days = (self.until - self.since).days + 1
        all_metrics = {
            "page_follows": list(range(5, 5 + number_of_days)),
            "page_post_engagements": engagement_values or list(range(11, 11 + number_of_days)),
            "page_media_view": view_values or list(range(20, 20 + number_of_days)),
        }
        return {"data": [
            {
                "name": name,
                "period": "day",
                "values": [
                    {
                        "value": value,
                        "end_time": f"{(self.since + timedelta(days=index)).isoformat()}T07:00:00+0000",
                    }
                    for index, value in enumerate(values)
                ],
            }
            for name, values in all_metrics.items()
            if name not in omit
        ]}

    def native_metrics_payload(
        self, *, period, reach_value=6, engagement_value=107,
        views_value=207, omit=(), end_dates=None, value_step=0,
    ):
        values = {
            "page_total_media_view_unique": reach_value,
            "page_post_engagements": engagement_value,
            "page_media_view": views_value,
        }
        end_dates = end_dates or [self.until]
        return {"data": [
            {
                "name": name,
                "period": period,
                "values": [
                    {
                        "value": value + index * value_step,
                        "end_time": f"{end_date.isoformat()}T07:00:00+0000",
                    }
                    for index, end_date in enumerate(end_dates)
                ],
            }
            for name, value in values.items()
            if name not in omit
        ]}

    def run_account_task(self, meta_client, *, credential="facebook-page-token"):
        from .tasks import sync_account_insights_task

        with (
            patch("apps.insights.sync_service.MetaCredentialService.get_access_token", return_value=credential) as token_resolver,
            patch("apps.insights.sync_service.MetaAPIClient", return_value=meta_client),
        ):
            result = sync_account_insights_task.run(work_id=str(self.work.id), generation=1)
        self.token_resolver = token_resolver
        return result

    def test_account_task_persists_v26_metric_mapping_and_preserves_daily_followers(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {
                "id": "facebook-page-1",
                "name": "Coffee Page",
                "followers_count": 123,
                "picture": {"data": {"url": "https://example.test/page.png"}},
            },
            self.insights_payload(),
            self.native_metrics_payload(
                period="week",
                end_dates=[self.since + timedelta(days=offset) for offset in range(1, 7)],
                value_step=1,
            ),
        ]
        result = self.run_account_task(client)

        self.assertEqual(result["status"], "complete")
        self.token_resolver.assert_called_once_with(social_account=self.account)
        client.get.assert_any_call(
            "/facebook-page-1/insights",
            access_token="facebook-page-token",
            params={
                "metric": "page_follows",
                "period": "day",
                "since": self.since.isoformat(),
                "until": self.until.isoformat(),
            },
        )
        client.get.assert_any_call(
            "/facebook-page-1/insights",
            access_token="facebook-page-token",
            params={
                "metric": "page_total_media_view_unique,page_post_engagements,page_media_view",
                "period": "week",
                "since": self.since.isoformat(),
                "until": self.until.isoformat(),
            },
        )
        snapshot = InsightsAccountSnapshot.objects.get(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
        )
        self.assertEqual(snapshot.metrics["followers"]["value"], 123)
        self.assertEqual(snapshot.metrics["followers"]["provider_metric"], "followers_count")
        self.assertEqual(snapshot.metrics["followers"]["period"], "current")
        self.assertEqual(snapshot.metrics["engagement"]["value"], 112)
        self.assertEqual(snapshot.metrics["engagement"]["provider_metric"], "page_post_engagements")
        self.assertEqual(snapshot.metrics["engagement"]["period"], "week")
        self.assertNotIn("aggregation", snapshot.metrics["engagement"])
        self.assertEqual(snapshot.metrics["views"]["value"], 212)
        self.assertEqual(snapshot.metrics["views"]["provider_metric"], "page_media_view")
        self.assertEqual(snapshot.metrics["views"]["period"], "week")
        self.assertNotIn("aggregation", snapshot.metrics["views"])
        self.assertEqual(snapshot.metrics["reach"]["value"], 11)
        self.assertEqual(snapshot.metrics["reach"]["provider_metric"], "page_total_media_view_unique")
        self.assertEqual(snapshot.metrics["reach"]["measurement"], "unique_media_viewers")
        self.assertEqual(snapshot.metrics["reach"]["period"], "week")
        from .serializers import MetricValueSerializer

        serialized_reach = MetricValueSerializer(snapshot.metrics["reach"]).data
        self.assertEqual(serialized_reach["date"], "2026-09-07")
        self.assertEqual(serialized_reach["measurement"], "unique_media_viewers")
        self.assertEqual(
            MetricValueSerializer(snapshot.metrics["engagement"]).data["period"],
            "week",
        )
        self.assertEqual(snapshot.profile_metadata["followers_count"], 123)
        self.assertEqual(snapshot.follower_growth["current_value"]["value"], 123)
        self.assertEqual(len(snapshot.follower_growth["points"]), 7)
        self.assertEqual(snapshot.follower_growth["change"]["value"], None)
        self.state.refresh_from_db()
        self.work.refresh_from_db()
        self.assertEqual(self.state.account_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.QUEUED)
        self.assertEqual(self.state.status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)

    def test_facebook_account_snapshot_upsert_is_idempotent(self):
        from .sync_service import _save_account_snapshot

        for _ in range(2):
            _save_account_snapshot(
                account=self.account,
                since=self.since,
                until=self.until,
                api_version="v26.0",
                metrics={"reach": {"value": 6, "availability": "available"}},
                follower_growth={"availability": "unavailable", "points": []},
                profile={"id": "facebook-page-1"},
            )

        self.assertEqual(
            InsightsAccountSnapshot.objects.filter(
                social_account=self.account,
                since=self.since,
                until=self.until,
                api_version="v26.0",
            ).count(),
            1,
        )

    def test_successful_facebook_refresh_updates_snapshot_and_merges_metric_envelopes(self):
        old_fetched_at = timezone.now() - timedelta(days=2)
        previous_state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            account_completed_at=old_fetched_at,
        )
        old_reach = {
            "value": 88,
            "availability": "available",
            "reason": "",
            "provider_metric": "page_total_media_view_unique",
            "period": "week",
            "measurement": "unique_media_viewers",
        }
        snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={
                "reach": old_reach,
                "engagement": {
                    "value": None,
                    "availability": "unavailable",
                    "reason": "old_reason",
                    "provider_metric": "page_post_engagements",
                    "period": "week",
                },
                "views": {
                    "value": None,
                    "availability": "unavailable",
                    "reason": "old_reason",
                    "provider_metric": "page_media_view",
                    "period": "week",
                },
                "followers": {
                    "value": 123,
                    "availability": "available",
                    "provider_metric": "followers_count",
                    "period": "current",
                },
                "preserved_extra": {"value": 7, "availability": "available"},
            },
            follower_growth={"availability": "available", "points": [{"date": "old"}]},
            profile_metadata={"id": "facebook-page-1", "name": "Old Page Name"},
            fetched_at=old_fetched_at,
            sync_state=previous_state,
        )
        snapshot_id = snapshot.id
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=7,
            published_account_sync_state=previous_state,
            published_content_sync_state=previous_state,
            active_sync_state=self.state,
        )
        old_snapshot_values = (snapshot.metrics.copy(), snapshot.fetched_at, snapshot.profile_metadata.copy())
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "name": "Coffee Page", "followers_count": 125},
            self.insights_payload(),
            self.native_metrics_payload(
                period="week",
                omit={"page_total_media_view_unique", "page_media_view"},
            ),
        ]

        result = self.run_account_task(client)

        snapshot.refresh_from_db()
        self.state.refresh_from_db()
        new_snapshot = InsightsAccountSnapshot.objects.get(sync_state=self.state)
        slot.refresh_from_db()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(snapshot.id, snapshot_id)
        self.assertEqual(
            (snapshot.metrics, snapshot.fetched_at, snapshot.profile_metadata),
            old_snapshot_values,
        )
        self.assertNotEqual(self.state.id, previous_state.id)
        self.assertEqual(new_snapshot.sync_state_id, self.state.id)
        self.assertGreater(new_snapshot.fetched_at, old_fetched_at)
        self.assertEqual(new_snapshot.fetched_at, self.state.account_completed_at)
        self.assertEqual(self.state.account_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(slot.published_account_sync_state_id, self.state.id)
        self.assertEqual(slot.active_sync_state_id, self.state.id)
        self.assertEqual(
            InsightsAccountSnapshot.objects.filter(
                social_account=self.account,
                since=self.since,
                until=self.until,
                api_version="v26.0",
                is_deleted=False,
            ).count(),
            2,
        )
        self.assertEqual(snapshot.metrics["reach"], old_reach)
        self.assertEqual(new_snapshot.metrics["reach"], old_reach)
        self.assertEqual(new_snapshot.metrics["engagement"]["value"], 107)
        self.assertEqual(new_snapshot.metrics["engagement"]["period"], "week")
        self.assertEqual(new_snapshot.metrics["views"]["value"], None)
        self.assertEqual(new_snapshot.metrics["views"]["reason"], "native_window_not_returned")
        self.assertEqual(new_snapshot.metrics["views"]["period"], "week")
        self.assertEqual(new_snapshot.metrics["followers"]["value"], 125)
        self.assertEqual(new_snapshot.metrics["preserved_extra"]["value"], 7)
        self.assertEqual(new_snapshot.profile_metadata["name"], "Coffee Page")
        client.get.assert_any_call(
            "/facebook-page-1/insights",
            access_token="facebook-page-token",
            params={
                "metric": "page_total_media_view_unique,page_post_engagements,page_media_view",
                "period": "week",
                "since": self.since.isoformat(),
                "until": self.until.isoformat(),
            },
        )

    def test_successful_facebook_28_day_refresh_persists_native_metrics(self):
        self.until = self.since + timedelta(days=27)
        self.state.until = self.until
        self.state.save(update_fields=("until", "updated_at"))
        old_fetched_at = timezone.now() - timedelta(days=2)
        previous_state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            account_completed_at=old_fetched_at,
        )
        snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={
                "reach": {"value": None, "availability": "unavailable"},
                "engagement": {"value": None, "availability": "unavailable"},
                "views": {"value": None, "availability": "unavailable"},
            },
            follower_growth={"availability": "available", "points": []},
            profile_metadata={},
            fetched_at=old_fetched_at,
            sync_state=previous_state,
        )
        slot = InsightsSnapshotSlot.objects.create(
            social_account=self.account,
            duration_days=28,
            published_account_sync_state=previous_state,
            published_content_sync_state=previous_state,
            active_sync_state=self.state,
        )
        old_snapshot_values = (snapshot.metrics.copy(), snapshot.fetched_at)
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            self.insights_payload(),
            self.native_metrics_payload(
                period="days_28",
                reach_value=28,
                engagement_value=128,
                views_value=228,
                end_dates=[
                    self.since + timedelta(days=1),
                    self.since + timedelta(days=14),
                    self.until,
                ],
                value_step=1,
            ),
        ]

        self.run_account_task(client)

        snapshot.refresh_from_db()
        self.state.refresh_from_db()
        new_snapshot = InsightsAccountSnapshot.objects.get(sync_state=self.state)
        slot.refresh_from_db()
        self.assertEqual((snapshot.metrics, snapshot.fetched_at), old_snapshot_values)
        self.assertNotEqual(self.state.id, previous_state.id)
        self.assertEqual(new_snapshot.sync_state_id, self.state.id)
        self.assertGreater(new_snapshot.fetched_at, old_fetched_at)
        self.assertEqual(new_snapshot.fetched_at, self.state.account_completed_at)
        self.assertEqual(self.state.account_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(slot.published_account_sync_state_id, self.state.id)
        self.assertEqual(slot.active_sync_state_id, self.state.id)
        for name, expected_value, provider_metric in (
            ("reach", 30, "page_total_media_view_unique"),
            ("engagement", 130, "page_post_engagements"),
            ("views", 230, "page_media_view"),
        ):
            self.assertEqual(new_snapshot.metrics[name]["value"], expected_value)
            self.assertEqual(new_snapshot.metrics[name]["availability"], "available")
            self.assertEqual(new_snapshot.metrics[name]["provider_metric"], provider_metric)
            self.assertEqual(new_snapshot.metrics[name]["period"], "days_28")
            self.assertNotIn("aggregation", new_snapshot.metrics[name])
        self.assertEqual(
            InsightsAccountSnapshot.objects.filter(
                social_account=self.account,
                since=self.since,
                until=self.until,
                api_version="v26.0",
                is_deleted=False,
            ).count(),
            2,
        )

    def test_facebook_provider_failure_preserves_existing_snapshot(self):
        old_fetched_at = timezone.now() - timedelta(days=2)
        snapshot = InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={"reach": {"value": 88, "availability": "available"}},
            follower_growth={"availability": "available", "points": []},
            profile_metadata={"name": "Saved Page"},
            fetched_at=old_fetched_at,
        )
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 125},
            MetaAPIError(
                "Page Insights permission required.",
                status_code=403,
                error_payload={"error": {"code": 200, "message": "Permissions error."}},
            ),
            self.native_metrics_payload(period="week"),
        ]

        result = self.run_account_task(client)

        snapshot.refresh_from_db()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(snapshot.metrics, {"reach": {"value": 88, "availability": "available"}})
        self.assertEqual(snapshot.profile_metadata, {"name": "Saved Page"})
        self.assertEqual(snapshot.fetched_at, old_fetched_at)
        self.assertEqual(
            InsightsAccountSnapshot.objects.filter(
                social_account=self.account,
                since=self.since,
                until=self.until,
                api_version="v26.0",
                is_deleted=False,
            ).count(),
            1,
        )

    def test_missing_metric_is_unavailable_not_fabricated_as_zero(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            self.insights_payload(),
            self.native_metrics_payload(period="week", omit={"page_total_media_view_unique"}),
        ]
        result = self.run_account_task(client)
        self.assertEqual(result["status"], "complete")
        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        reach = snapshot.metrics["reach"]
        self.assertIsNone(reach["value"])
        self.assertEqual(reach["availability"], "unavailable")
        self.assertEqual(reach["provider_metric"], "page_total_media_view_unique")
        self.assertEqual(reach["period"], "week")
        self.state.refresh_from_db()
        self.assertEqual(self.state.account_status, InsightsSyncStatus.COMPLETE)

    def test_profile_followers_are_not_replaced_by_daily_follows(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            self.insights_payload(),
            self.native_metrics_payload(period="week"),
        ]

        self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        self.assertEqual(snapshot.metrics["followers"]["value"], 123)
        self.assertEqual(snapshot.metrics["followers"]["provider_metric"], "followers_count")
        self.assertEqual(snapshot.follower_growth["points"][-1]["value"]["value"], 11)

    def test_missing_profile_followers_stays_unavailable_despite_daily_follows(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1"},
            self.insights_payload(),
            self.native_metrics_payload(period="week"),
        ]

        result = self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        followers = snapshot.metrics["followers"]
        self.assertEqual(result["status"], "complete")
        self.assertIsNone(followers["value"])
        self.assertEqual(followers["availability"], "unavailable")
        self.assertEqual(followers["provider_metric"], "followers_count")
        self.assertEqual(snapshot.follower_growth["points"][-1]["value"]["value"], 11)

    def test_28_day_range_uses_native_days_28_reach_and_preserves_zero(self):
        self.until = self.since + timedelta(days=27)
        self.state.until = self.until
        self.state.save(update_fields=("until", "updated_at"))
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 0},
            self.insights_payload(),
            self.native_metrics_payload(
                period="days_28",
                reach_value=0,
                engagement_value=0,
                views_value=0,
            ),
        ]

        result = self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(snapshot.metrics["followers"]["value"], 0)
        self.assertEqual(snapshot.metrics["engagement"]["value"], 0)
        self.assertEqual(snapshot.metrics["views"]["value"], 0)
        self.assertEqual(snapshot.metrics["reach"]["value"], 0)
        self.assertEqual(snapshot.metrics["reach"]["period"], "days_28")
        self.assertEqual(snapshot.metrics["reach"]["measurement"], "unique_media_viewers")
        self.assertEqual(snapshot.metrics["engagement"]["source"], "facebook")
        self.assertEqual(snapshot.metrics["engagement"]["period"], "days_28")
        self.assertNotIn("aggregation", snapshot.metrics["engagement"])
        self.assertEqual(snapshot.metrics["views"]["period"], "days_28")
        self.assertNotIn("aggregation", snapshot.metrics["views"])
        self.assertEqual(snapshot.metrics["views"]["provider_metric"], "page_media_view")
        client.get.assert_any_call(
            "/facebook-page-1/insights",
            access_token="facebook-page-token",
            params={
                "metric": "page_total_media_view_unique,page_post_engagements,page_media_view",
                "period": "days_28",
                "since": self.since.isoformat(),
                "until": self.until.isoformat(),
            },
        )

    def test_30_day_range_does_not_request_or_fabricate_account_reach(self):
        self.until = self.since + timedelta(days=29)
        self.state.until = self.until
        self.state.save(update_fields=("until", "updated_at"))
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            self.insights_payload(),
        ]

        result = self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        reach = snapshot.metrics["reach"]
        self.assertEqual(result["status"], "complete")
        self.assertEqual(client.get.call_count, 2)
        self.assertIsNone(reach["value"])
        self.assertEqual(reach["availability"], "not_supported")
        self.assertEqual(reach["reason"], "no_exact_native_aggregate_for_selected_range")
        self.assertEqual(reach["provider_metric"], "page_total_media_view_unique")
        self.assertEqual(reach["measurement"], "unique_media_viewers")
        self.assertIsNone(reach["period"])

    def test_90_day_range_does_not_request_or_fabricate_account_reach(self):
        self.until = self.since + timedelta(days=89)
        self.state.until = self.until
        self.state.save(update_fields=("until", "updated_at"))
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            self.insights_payload(),
        ]

        result = self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(client.get.call_count, 2)
        self.assertIsNone(snapshot.metrics["reach"]["value"])
        self.assertEqual(snapshot.metrics["reach"]["availability"], "not_supported")
        self.assertEqual(
            snapshot.metrics["reach"]["reason"],
            "no_exact_native_aggregate_for_selected_range",
        )
        self.assertEqual(snapshot.metrics["reach"]["provider_metric"], "page_total_media_view_unique")
        self.assertIsNone(snapshot.metrics["reach"]["period"])

    def test_native_metric_unavailable_is_not_fabricated_as_zero(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            self.insights_payload(),
            self.native_metrics_payload(period="week", omit={"page_post_engagements"}),
        ]

        result = self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        engagement = snapshot.metrics["engagement"]
        self.assertEqual(result["status"], "complete")
        self.assertIsNone(engagement["value"])
        self.assertEqual(engagement["availability"], "unavailable")
        self.assertEqual(engagement["reason"], "metric_not_returned")

    def test_permission_error_keeps_facebook_account_stage_partial(self):
        permission_error = MetaAPIError(
            "Page Insights permission required.",
            status_code=403,
            error_payload={"error": {"code": 200, "message": "Permissions error."}},
        )
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            permission_error,
            permission_error,
        ]

        result = self.run_account_task(client)

        self.state.refresh_from_db()
        self.work.refresh_from_db()
        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(self.state.account_status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.state.account_error_reason, "read_insights")
        self.assertEqual(self.work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(snapshot.metrics["engagement"]["availability"], "permission_required")

    def test_exhausted_facebook_account_request_retries_fail_the_stage(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            MetaAPIError(
                "Temporary provider failure.",
                status_code=429,
                error_payload={"error": {"code": 4, "message": "Rate limited."}},
            ),
        ]
        self.work.provider_retry_count = 3
        self.work.save(update_fields=("provider_retry_count", "updated_at"))

        result = self.run_account_task(client)

        self.state.refresh_from_db()
        self.work.refresh_from_db()
        self.assertEqual(result["status"], InsightsSyncStatus.FAILED)
        self.assertEqual(self.state.account_status, InsightsSyncStatus.FAILED)
        self.assertEqual(self.state.account_error_code, "rate_limited")
        self.assertEqual(self.work.status, InsightsSyncWorkStatus.TERMINAL)

    def test_facebook_account_and_content_complete_produce_overall_complete(self):
        from .sync_service import _aggregate_overall_status

        InsightsAccountSnapshot.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={
                "reach": {
                    "value": None,
                    "availability": "not_supported",
                    "reason": "no_exact_native_aggregate_for_selected_range",
                    "provider_metric": "page_total_media_view_unique",
                    "period": None,
                    "measurement": "unique_media_viewers",
                },
            },
            follower_growth={"availability": "unavailable", "points": []},
            fetched_at=timezone.now(),
        )
        self.state.account_status = InsightsSyncStatus.COMPLETE
        self.state.content_status = InsightsSyncStatus.COMPLETE
        self.state.status = InsightsSyncStatus.SYNCING

        _aggregate_overall_status(self.state)

        self.assertEqual(self.state.status, InsightsSyncStatus.COMPLETE)

    def test_daily_metric_requires_full_inclusive_date_coverage(self):
        self.until = self.since + timedelta(days=29)
        self.state.until = self.until
        self.state.save(update_fields=("until", "updated_at"))
        partial_data = self.insights_payload()
        for metric in partial_data["data"]:
            if metric["name"] == "page_media_view":
                metric["values"].pop()
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            partial_data,
        ]

        self.run_account_task(client)

        snapshot = InsightsAccountSnapshot.objects.get(social_account=self.account)
        views = snapshot.metrics["views"]
        self.assertIsNone(views["value"])
        self.assertEqual(views["availability"], "unavailable")
        self.assertEqual(views["reason"], "incomplete_date_coverage")

    def test_invalid_meta_credential_fails_account_stage_without_provider_call(self):
        from .tasks import sync_account_insights_task

        client = SimpleNamespace(get=Mock())
        with (
            patch(
                "apps.insights.sync_service.MetaCredentialService.get_access_token",
                side_effect=MetaIntegrationError("credential unavailable"),
            ),
            patch("apps.insights.sync_service.MetaAPIClient", return_value=client),
        ):
            result = sync_account_insights_task.run(work_id=str(self.work.id), generation=1)
        self.assertEqual(result["status"], "failed")
        client.get.assert_not_called()
        self.state.refresh_from_db()
        self.work.refresh_from_db()
        self.assertEqual(self.state.account_status, InsightsSyncStatus.FAILED)
        self.assertEqual(self.work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertFalse(InsightsAccountSnapshot.objects.exists())

    def test_rate_limit_rearms_only_account_work_for_existing_retry_flow(self):
        client = SimpleNamespace(get=Mock())
        client.get.side_effect = [
            {"id": "facebook-page-1", "followers_count": 123},
            MetaAPIError("rate limited", status_code=429, error_payload={"error": {"code": 4}}),
        ]
        result = self.run_account_task(client)
        self.assertEqual(result["status"], "retrying")
        self.work.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.work.provider_retry_count, 1)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertFalse(InsightsAccountSnapshot.objects.exists())

    def test_facebook_content_work_can_be_dispatched_and_claimed(self):
        from .sync_service import claim_stage_work, dispatch_stage_work
        from .tasks import sync_instagram_content_batch_task

        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            return_value=SimpleNamespace(id="facebook-content-task"),
        ) as dispatch:
            self.assertTrue(dispatch_stage_work(self.content_work.id))
        dispatch.assert_called_once_with(
            kwargs={"work_id": str(self.content_work.id), "generation": 1},
        )
        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.DISPATCHED)
        claim = claim_stage_work(work_id=self.content_work.id, generation=1)
        self.assertEqual(claim["stage"], InsightsSyncWorkStage.CONTENT)
        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.CLAIMED)

    def test_facebook_account_stage_dispatch_uses_existing_account_task(self):
        from .sync_service import dispatch_stage_work
        from .tasks import sync_account_insights_task, sync_instagram_content_batch_task

        self.work.status = InsightsSyncWorkStatus.PENDING
        self.work.save(update_fields=("status", "updated_at"))
        self.content_work.status = InsightsSyncWorkStatus.PENDING
        self.content_work.save(update_fields=("status", "updated_at"))
        with (
            patch.object(sync_account_insights_task, "apply_async", return_value=SimpleNamespace(id="account-task")) as account_dispatch,
            patch.object(sync_instagram_content_batch_task, "apply_async") as content_dispatch,
        ):
            self.assertTrue(dispatch_stage_work(self.work.id))

        account_dispatch.assert_called_once_with(
            kwargs={"work_id": str(self.work.id), "generation": 1},
        )
        content_dispatch.assert_not_called()
        self.work.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.work.status, InsightsSyncWorkStatus.DISPATCHED)
        self.assertEqual(self.work.celery_task_id, "account-task")
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)


class FacebookContentSyncTests(TestCase):
    since = date(2026, 9, 1)
    until = date(2026, 9, 30)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="facebook-content-sync@example.com",
            first_name="Facebook Content",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-FB-CONTENT-SYNC",
            name="Facebook Content Org",
            slug="facebook-content-sync-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="facebook-page-content-1",
            username="facebook-content-page",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        self.state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.SYNCING,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.QUEUED,
        )
        self.content_work = InsightsSyncWork.objects.create(
            sync_state=self.state,
            stage=InsightsSyncWorkStage.CONTENT,
            generation=1,
            status=InsightsSyncWorkStatus.DISPATCHED,
        )
        self.client = SimpleNamespace(get=Mock())
        self.post_insights_response = self.complete_post_insights()
        self._facebook_page_responses = None
        self._facebook_router_initialized = False

    @staticmethod
    def post(post_id="post-1", **overrides):
        item = {
            "id": post_id,
            "message": "A Facebook post",
            "created_time": "2026-09-15T13:24:00+0000",
            "permalink_url": f"https://facebook.example.test/{post_id}",
            "shares": {"count": 2},
            "comments": {"data": [], "summary": {"total_count": 3}},
            "reactions": {"data": [], "summary": {"total_count": 4}},
        }
        item.update(overrides)
        return item

    @staticmethod
    def complete_post_insights():
        return {"data": [
            {"name": "post_total_media_view_unique", "period": "lifetime", "values": [{"value": 12}]},
            {"name": "post_media_view", "period": "lifetime", "values": [{"value": 21}]},
            {"name": "post_clicks", "period": "lifetime", "values": [{"value": 6}]},
        ]}

    @staticmethod
    def page(posts, *, after=None, has_next=False):
        paging = {}
        if has_next:
            paging["next"] = "present"
            paging["cursors"] = {"after": after} if after else {}
        return {"data": posts, "paging": paging}

    def run_content_task(self, *, generation=None):
        from .tasks import sync_instagram_content_batch_task

        request_mock = self.client.get
        if not self._facebook_router_initialized:
            configured = request_mock.side_effect
            if isinstance(configured, (list, tuple)):
                self._facebook_page_responses = iter(configured)
            else:
                self._facebook_page_responses = configured
            self._facebook_page_return_value = request_mock.return_value
            self._facebook_router_initialized = True

        def route_request(path, **kwargs):
            if path.endswith("/insights"):
                result = self.post_insights_response
                if isinstance(result, BaseException):
                    raise result
                if callable(result):
                    return result(path, **kwargs)
                return result

            page_responses = self._facebook_page_responses
            if isinstance(page_responses, BaseException):
                raise page_responses
            if callable(page_responses):
                return page_responses(path, **kwargs)
            if page_responses is not None:
                return next(page_responses)
            return self._facebook_page_return_value

        request_mock.side_effect = route_request

        with (
            patch(
                "apps.insights.sync_service.MetaCredentialService.get_access_token",
                return_value="facebook-page-token",
            ) as token_resolver,
            patch("apps.insights.sync_service.MetaAPIClient", return_value=self.client),
        ):
            result = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation if generation is None else generation,
            )
        self.token_resolver = token_resolver
        return result

    def test_content_sync_fetches_and_persists_available_facebook_post_fields(self):
        self.client.get.return_value = self.page([self.post()])
        self.post_insights_response = {"data": [
            {"name": "post_total_media_view_unique", "period": "lifetime", "values": [{"value": 12}]},
            {"name": "post_media_view", "period": "lifetime", "values": [{"value": 21}]},
            {"name": "post_clicks", "period": "lifetime", "values": [{"value": 6}]},
        ]}
        result = self.run_content_task()

        self.assertEqual(result["content_status"], InsightsSyncStatus.COMPLETE)
        self.token_resolver.assert_called_once_with(social_account=self.account)
        self.assertEqual(self.client.get.call_args_list[0], call(
            "/facebook-page-content-1/posts",
            access_token="facebook-page-token",
            params={
                "fields": (
                    "id,message,created_time,permalink_url,shares,"
                    "comments.limit(0).summary(true),reactions.limit(0).summary(true)"
                ),
                "limit": 25,
            },
        ))
        self.assertEqual(self.client.get.call_args_list[1], call(
            "/post-1/insights",
            access_token="facebook-page-token",
            params={
                "metric": (
                    "post_total_media_view_unique,post_media_view,post_clicks"
                ),
                "period": "lifetime",
            },
        ))
        snapshot = InsightsMediaSnapshot.objects.get(
            social_account=self.account,
            provider_media_id="post-1",
        )
        self.assertEqual(snapshot.caption, "A Facebook post")
        self.assertEqual(snapshot.permalink, "https://facebook.example.test/post-1")
        self.assertEqual(snapshot.published_at.date(), date(2026, 9, 15))
        self.assertEqual(snapshot.api_version, "v26.0")
        self.assertIsNotNone(snapshot.fetched_at)
        self.assertEqual(snapshot.metrics["shares"]["value"], 2)
        self.assertEqual(snapshot.metrics["comments"]["value"], 3)
        self.assertEqual(snapshot.metrics["reactions"]["value"], 4)
        self.assertEqual(snapshot.metrics["reactions"]["source"], "facebook")
        self.assertEqual(snapshot.metrics["reach"]["value"], 12)
        self.assertEqual(snapshot.metrics["reach"]["provider_metric"], "post_total_media_view_unique")
        self.assertEqual(snapshot.metrics["reach"]["measurement"], "unique_media_viewers")
        self.assertEqual(snapshot.metrics["reach"]["period"], "lifetime")
        self.assertEqual(snapshot.metrics["views"]["value"], 21)
        self.assertIsNone(snapshot.metrics["reactions_by_type"]["value"])
        self.assertEqual(snapshot.metrics["reactions_by_type"]["availability"], "unavailable")
        self.assertEqual(snapshot.metrics["reactions_by_type"]["reason"], "metric_not_returned")
        self.assertEqual(snapshot.metrics["clicks"]["value"], 6)
        self.assertIsNone(snapshot.metrics["clicks_by_type"]["value"])
        self.assertEqual(snapshot.metrics["clicks_by_type"]["availability"], "unavailable")
        self.assertEqual(snapshot.metrics["clicks_by_type"]["reason"], "metric_not_returned")
        self.assertIn("engagement", snapshot.metrics)
        self.assertIsNone(snapshot.metrics["engagement"]["value"])
        self.assertEqual(snapshot.metrics["engagement"]["availability"], "unavailable")
        requested_metrics = self.client.get.call_args_list[1].kwargs["params"]["metric"]
        self.assertNotIn("post_reactions_by_type_total", requested_metrics)
        self.assertNotIn("post_clicks_by_type", requested_metrics)
        self.assertNotIn("page_impressions_unique", str(self.client.get.call_args))
        self.assertNotIn("page_impressions", str(self.client.get.call_args))
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.status, InsightsSyncStatus.COMPLETE)
        self.assertEqual((self.state.items_discovered, self.state.items_processed, self.state.items_total), (1, 1, 1))
        self.assertEqual(self.state.checkpoint, {})
        self.assertEqual(self.state.provider_cursor, "")
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)

    def test_missing_shares_does_not_make_complete_facebook_sync_partial(self):
        post_without_shares = self.post("post-without-shares")
        post_without_shares.pop("shares")
        self.client.get.return_value = self.page([post_without_shares])
        self.post_insights_response = self.complete_post_insights()

        result = self.run_content_task()

        self.assertEqual(result["content_status"], InsightsSyncStatus.COMPLETE)
        snapshot = InsightsMediaSnapshot.objects.get(provider_media_id="post-without-shares")
        self.assertIsNone(snapshot.metrics["shares"]["value"])
        self.assertEqual(snapshot.metrics["shares"]["availability"], "unavailable")
        self.assertEqual(snapshot.metrics["shares"]["reason"], "metric_not_returned")
        self.assertIsNone(snapshot.metrics["engagement"]["value"])
        self.assertEqual(snapshot.metrics["engagement"]["availability"], "unavailable")
        self.state.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.error_code, "")

    def test_missing_post_metrics_remain_unavailable_instead_of_zero(self):
        self.post_insights_response = {"data": []}
        self.client.get.return_value = self.page([{
            "id": "post-without-counts",
            "created_time": "2026-09-15T13:24:00+0000",
        }])
        self.run_content_task()
        snapshot = InsightsMediaSnapshot.objects.get(provider_media_id="post-without-counts")
        for metric in ("likes", "comments", "shares", "reactions", "reach", "views", "engagement"):
            with self.subTest(metric=metric):
                self.assertIsNone(snapshot.metrics[metric]["value"])
                self.assertEqual(snapshot.metrics[metric]["availability"], "unavailable")

    def test_metadata_and_insights_updates_merge_without_erasing_other_metrics(self):
        from .sync_service import _persist_facebook_posts, _store_media_metrics

        snapshot = InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="post-merge",
            api_version="v26.0",
            metrics={
                "reactions": {"value": 8, "availability": "available", "source": "facebook"},
                "comments": {"value": 2, "availability": "available", "source": "facebook"},
                "shares": {"value": 1, "availability": "available", "source": "facebook"},
                "reach": {"value": 50, "availability": "available", "source": "facebook"},
            },
            fetched_at=timezone.now(),
        )
        metadata_post = self.post(
            "post-merge",
            shares=None,
            comments=None,
            reactions=None,
            message="Updated metadata",
        )
        _persist_facebook_posts(
            account=self.account,
            page=self.page([metadata_post]),
            since=self.since,
            until=self.until,
            api_version="v26.0",
        )
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.caption, "Updated metadata")
        self.assertEqual(snapshot.metrics["reactions"]["value"], 8)
        self.assertEqual(snapshot.metrics["comments"]["value"], 2)
        self.assertEqual(snapshot.metrics["shares"]["value"], 1)
        self.assertEqual(snapshot.metrics["reach"]["value"], 50)

        _store_media_metrics(
            account=self.account,
            media_id="post-merge",
            metrics={
                "reach": {"value": None, "availability": "unavailable", "reason": "metric_not_returned"},
                "views": {"value": 100, "availability": "available"},
                "clicks": {"value": 4, "availability": "available"},
            },
            preserve_available=True,
        )
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.metrics["reach"]["value"], 50)
        self.assertEqual(snapshot.metrics["views"]["value"], 100)
        self.assertEqual(snapshot.metrics["clicks"]["value"], 4)
        self.assertEqual(snapshot.metrics["reactions"]["value"], 8)
        self.assertEqual(snapshot.metrics["comments"]["value"], 2)
        self.assertEqual(snapshot.metrics["shares"]["value"], 1)

    def test_created_time_filter_is_inclusive_at_both_boundaries(self):
        self.client.get.return_value = self.page([
            self.post("at-since", created_time="2026-09-01T00:00:00+0000"),
            self.post("before-since", created_time="2026-08-31T23:59:59+0000"),
            self.post("at-until", created_time="2026-09-30T23:59:59+0000"),
            self.post("after-until", created_time="2026-10-01T00:00:00+0000"),
        ])
        self.run_content_task()
        self.assertEqual(
            set(InsightsMediaSnapshot.objects.filter(social_account=self.account).values_list("provider_media_id", flat=True)),
            {"at-since", "at-until"},
        )
        self.state.refresh_from_db()
        self.assertEqual((self.state.items_discovered, self.state.items_processed), (2, 2))

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=2)
    def test_facebook_cursor_is_checkpointed_and_resumed_until_complete(self):
        from .tasks import sync_instagram_content_batch_task

        self.client.get.side_effect = [
            self.page([self.post("first-page")], after="page-two-cursor", has_next=True),
            self.page([self.post("second-page")]),
        ]
        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            return_value=SimpleNamespace(id="facebook-content-continuation"),
        ) as continuation_dispatch:
            first = self.run_content_task()
            self.state.refresh_from_db()
            self.content_work.refresh_from_db()
            self.assertTrue(first["continue"])
            self.assertEqual(self.state.checkpoint["pages_fetched"], 1)
            self.assertEqual(self.state.checkpoint["max_pages"], 2)
            self.assertEqual(self.state.checkpoint["next_cursor"], "page-two-cursor")
            self.assertEqual(self.state.provider_cursor, "page-two-cursor")
            self.assertIsNone(self.state.items_total)
            continuation_dispatch.assert_called_once()
            second = self.run_content_task()

        self.assertEqual(second["content_status"], InsightsSyncStatus.COMPLETE)
        post_calls = [item for item in self.client.get.call_args_list if item.args[0].endswith("/posts")]
        self.assertEqual(post_calls[1].kwargs["params"]["after"], "page-two-cursor")
        self.assertEqual(InsightsMediaSnapshot.objects.filter(social_account=self.account).count(), 2)
        self.state.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.items_total, 2)
        self.assertEqual(self.state.provider_cursor, "")
        self.assertEqual(self.state.checkpoint, {})

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    def test_page_ceiling_rearms_and_budget_exhaustion_keeps_more_content_evidence(self):
        from .tasks import sync_instagram_content_batch_task

        self.client.get.side_effect = [
            self.page([self.post("first-page")], after="page-two-cursor", has_next=True),
            self.page([self.post("second-page")], after="page-three-cursor", has_next=True),
        ]
        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            return_value=SimpleNamespace(id="facebook-content-continuation"),
        ) as continuation_dispatch:
            first = self.run_content_task()
            self.state.refresh_from_db()
            self.assertTrue(first["continue"])
            self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
            self.assertEqual(self.state.checkpoint["pages_fetched"], 0)
            self.assertEqual(self.state.provider_cursor, "page-two-cursor")
            second = self.run_content_task()

        self.assertEqual(second["content_status"], InsightsSyncStatus.PARTIAL)
        continuation_dispatch.assert_called_once()
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.state.status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.state.checkpoint["stop_reason"], "automatic_continuation_budget_reached")
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
        self.assertTrue(self.state.checkpoint["has_more"])
        self.assertEqual(self.state.checkpoint["next_cursor"], "page-three-cursor")
        self.assertEqual(self.state.provider_cursor, "page-three-cursor")
        self.assertEqual((self.state.items_discovered, self.state.items_processed, self.state.items_total), (2, 2, 2))
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        from .snapshot_read import _attempt_payload

        attempt_payload = _attempt_payload(self.state)
        self.assertTrue(attempt_payload["more_content_available"])
        self.assertNotIn("provider_cursor", attempt_payload)
        self.assertNotIn("checkpoint", attempt_payload)
        self.assertNotIn("page-three-cursor", str(attempt_payload))

    def test_duplicate_post_across_pages_updates_one_snapshot_and_counts_once(self):
        from .tasks import sync_instagram_content_batch_task

        self.client.get.side_effect = [
            self.page([self.post("repeated-post")], after="cursor-2", has_next=True),
            self.page([
                self.post("repeated-post", message="Updated post text"),
                self.post("new-post"),
            ]),
        ]
        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            return_value=SimpleNamespace(id="facebook-content-continuation"),
        ):
            self.run_content_task()
            self.run_content_task()
        self.assertEqual(InsightsMediaSnapshot.objects.filter(social_account=self.account).count(), 2)
        self.assertEqual(InsightsContentSnapshotItem.objects.filter(sync_state=self.state).count(), 2)
        repeated = InsightsMediaSnapshot.objects.get(provider_media_id="repeated-post")
        self.assertEqual(repeated.caption, "Updated post text")
        repeated_version = InsightsContentSnapshotItem.objects.get(
            sync_state=self.state,
            provider_media_id="repeated-post",
        )
        self.assertEqual(repeated_version.caption, "Updated post text")
        self.assertEqual(repeated_version.metrics["reach"]["value"], 12)
        self.state.refresh_from_db()
        self.assertEqual((self.state.items_discovered, self.state.items_processed, self.state.items_total), (2, 2, 2))

    def test_explicit_refresh_after_partial_creates_new_facebook_attempt(self):
        from .sync_service import request_insights_sync

        self.state.status = InsightsSyncStatus.PARTIAL
        self.state.content_status = InsightsSyncStatus.PARTIAL
        self.state.provider_cursor = "retry-from-this-cursor"
        self.state.checkpoint = {
            "next_cursor": "retry-from-this-cursor",
            "has_more": True,
            "pages_fetched": 1,
            "max_pages": 1,
            "automatic_continuations": 1,
            "stop_reason": "automatic_continuation_budget_reached",
            "discovered_post_ids": ["already-seen"],
        }
        self.state.items_discovered = 1
        self.state.items_processed = 1
        self.state.items_total = 1
        self.state.save()
        self.content_work.status = InsightsSyncWorkStatus.TERMINAL
        self.content_work.save(update_fields=("status", "updated_at"))

        with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch:
            with self.captureOnCommitCallbacks(execute=True):
                request_insights_sync(
                    social_account_id=self.account.id,
                    since=self.since,
                    until=self.until,
                )
        dispatch.assert_called_once()
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        new_state = InsightsSyncState.objects.exclude(id=self.state.id).get()
        self.assertEqual(self.state.provider_cursor, "retry-from-this-cursor")
        self.assertEqual(self.state.checkpoint["next_cursor"], "retry-from-this-cursor")
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
        self.assertEqual(self.state.checkpoint["pages_fetched"], 1)
        self.assertEqual(self.state.status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.state.checkpoint["discovered_post_ids"], ["already-seen"])
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(new_state.status, InsightsSyncStatus.QUEUED)
        self.assertEqual(new_state.checkpoint, {})
        self.assertEqual(new_state.provider_cursor, "")
        self.assertEqual(new_state.items_processed, 0)

    def test_invalid_facebook_credential_fails_without_provider_call(self):
        from .tasks import sync_instagram_content_batch_task

        with (
            patch(
                "apps.insights.sync_service.MetaCredentialService.get_access_token",
                side_effect=MetaIntegrationError("credential unavailable"),
            ),
            patch("apps.insights.sync_service.MetaAPIClient", return_value=self.client),
        ):
            result = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=1,
            )
        self.assertEqual(result["status"], "failed")
        self.client.get.assert_not_called()
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.FAILED)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertFalse(InsightsMediaSnapshot.objects.exists())

    def test_permission_error_is_terminal_partial_without_raw_provider_details(self):
        self.client.get.return_value = self.page([self.post()])
        self.post_insights_response = MetaAPIError(
            "Raw private permission detail",
            status_code=403,
            error_payload={
                "error": {
                    "code": 200,
                    "error_subcode": 10,
                    "type": "OAuthException",
                    "message": (
                        "Permissions error access_token=DIAG_ACCESS_SECRET "
                        "Bearer DIAG_BEARER_SECRET "
                        "https://meta.example/posts?access_token=DIAG_URL_SECRET "
                        "12345678901234"
                    ),
                    "fbtrace_id": "TRACE_ABC123",
                    "private_payload_field": "DIAG_RAW_PAYLOAD_SECRET",
                },
            },
        )
        result = self.run_content_task()

        self.assertEqual(result["status"], InsightsSyncStatus.PARTIAL)
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        snapshot = InsightsMediaSnapshot.objects.get(provider_media_id="post-1")
        self.assertEqual(self.state.error_code, "permission_required")
        self.assertEqual(self.state.error_reason, "read_insights")
        self.assertEqual(self.state.content_status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        for metric in ("reach", "views", "reactions_by_type", "clicks", "clicks_by_type"):
            self.assertEqual(snapshot.metrics[metric]["availability"], "permission_required")
            self.assertIsNone(snapshot.metrics[metric]["value"])

    def test_rate_limited_post_exhaustion_records_one_post_and_continues(self):
        from .tasks import sync_instagram_content_batch_task

        self.client.get.return_value = self.page([self.post("retry-post"), self.post("next-post")])
        self.post_insights_response = MetaAPIError(
            "Temporary provider failure",
            status_code=429,
            error_payload={"error": {"code": 4, "message": "Rate limited"}},
        )
        self.content_work.provider_retry_count = 3
        self.content_work.save(update_fields=("provider_retry_count", "updated_at"))

        with patch("apps.insights.tasks.dispatch_stage_work") as dispatch:
            result = self.run_content_task()

        self.assertEqual(result["status"], InsightsSyncStatus.SYNCING)
        self.assertTrue(result["continue"])
        dispatch.assert_called_once_with(str(self.content_work.id))
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 2)
        self.assertEqual(self.state.items_processed, 1)
        self.assertEqual(self.state.checkpoint["offset"], 1)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.error_code, "rate_limited")
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.content_work.provider_retry_count, 0)
        first = InsightsMediaSnapshot.objects.get(provider_media_id="retry-post")
        self.assertEqual(first.metrics["reach"]["availability"], "provider_error")
        self.assertEqual(first.metrics["reach"]["reason"], "rate_limited")
        second = InsightsMediaSnapshot.objects.get(provider_media_id="next-post")
        self.assertEqual(second.metrics["reach"]["availability"], "unavailable")

    def test_transient_post_error_keeps_checkpoint_and_retries_durably(self):
        self.client.get.return_value = self.page([self.post("transient-post")])
        self.post_insights_response = MetaAPIError(
            "Temporary provider failure",
            status_code=503,
            error_payload={"error": {"code": 1, "message": "Temporary failure"}},
        )

        result = self.run_content_task()

        self.assertEqual(result["status"], "retrying")
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 1)
        self.assertEqual(self.state.items_processed, 0)
        self.assertEqual(self.state.checkpoint["offset"], 0)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.content_work.provider_retry_count, 1)
        snapshot = InsightsMediaSnapshot.objects.get(provider_media_id="transient-post")
        self.assertEqual(snapshot.metrics["reach"]["availability"], "unavailable")
        self.assertEqual(snapshot.metrics["reach"]["reason"], "metric_not_fetched")

    def test_post_insights_batch_continues_from_checkpoint_without_refetching_page(self):
        from .tasks import sync_instagram_content_batch_task

        self.client.get.return_value = self.page([
            self.post(f"post-{number}") for number in range(6)
        ])
        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            return_value=SimpleNamespace(id="facebook-post-insights-continuation"),
        ) as continuation_dispatch:
            first = self.run_content_task()
            self.state.refresh_from_db()
            self.assertTrue(first["continue"])
            self.assertEqual(self.state.items_processed, 5)
            self.assertEqual(self.state.checkpoint["offset"], 5)
            continuation_dispatch.assert_called_once()
            self.content_work.refresh_from_db()
            second = self.run_content_task()

        self.assertEqual(second["content_status"], InsightsSyncStatus.COMPLETE)
        post_page_requests = [
            request for request in self.client.get.call_args_list
            if request.args[0].endswith("/posts")
        ]
        self.assertEqual(len(post_page_requests), 1)
        self.state.refresh_from_db()
        self.assertEqual(self.state.items_processed, 6)
        self.assertEqual(self.state.items_discovered, 6)
        self.assertEqual(InsightsMediaSnapshot.objects.filter(social_account=self.account).count(), 6)
    def test_unsupported_posts_fields_finish_partial_without_persisting_raw_error(self):
        self.client.get.side_effect = MetaAPIError(
            "Raw unsupported field detail",
            status_code=400,
            error_payload={"error": {"code": 100, "message": "Unsupported fields requested."}},
        )
        result = self.run_content_task()
        self.assertEqual(result["status"], InsightsSyncStatus.PARTIAL)
        self.state.refresh_from_db()
        self.assertEqual(self.state.error_code, "not_supported")
        self.assertEqual(self.state.error_reason, "not_supported")
        self.assertNotIn("Raw unsupported", self.state.error_reason)
        self.assertFalse(InsightsMediaSnapshot.objects.exists())

    def test_retryable_provider_error_uses_durable_retry_and_keeps_cursor(self):
        self.state.provider_cursor = "retry-cursor"
        self.state.checkpoint = {"next_cursor": "retry-cursor", "has_more": True}
        self.state.save(update_fields=("provider_cursor", "checkpoint", "updated_at"))
        self.client.get.side_effect = MetaAPIError(
            "Temporary provider failure",
            status_code=429,
            error_payload={"error": {"code": 4}},
        )
        result = self.run_content_task()
        self.assertEqual(result["status"], "retrying")
        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.content_work.provider_retry_count, 1)
        self.assertEqual(self.state.provider_cursor, "retry-cursor")
        self.assertEqual(self.state.checkpoint["next_cursor"], "retry-cursor")
        self.assertFalse(InsightsMediaSnapshot.objects.exists())

    def test_stale_generation_cannot_persist_facebook_posts(self):
        from .sync_service import StaleInsightsWorkClaim, claim_stage_work, process_content_sync_batch

        claim = claim_stage_work(work_id=self.content_work.id, generation=1)
        self.assertIsNotNone(claim)
        InsightsSyncWork.objects.filter(id=self.content_work.id).update(generation=2)
        self.client.get.return_value = self.page([self.post()])

        with (
            patch("apps.insights.sync_service.MetaCredentialService.get_access_token", return_value="facebook-page-token"),
            patch("apps.insights.sync_service.MetaAPIClient", return_value=self.client),
            self.assertRaises(StaleInsightsWorkClaim),
        ):
            process_content_sync_batch(claim=claim)
        self.client.get.assert_not_called()
        self.assertFalse(InsightsMediaSnapshot.objects.exists())
        self.state.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 0)

    def test_missing_after_cursor_with_next_page_finishes_partial_safely(self):
        self.client.get.return_value = self.page([self.post()], has_next=True)
        result = self.run_content_task()
        self.assertEqual(result["content_status"], InsightsSyncStatus.PARTIAL)
        self.state.refresh_from_db()
        self.assertEqual(self.state.error_code, "pagination_unavailable")
        self.assertEqual(self.state.error_reason, "provider_pagination_cursor_unavailable")
        self.assertTrue(self.state.checkpoint["has_more"])
        self.assertEqual(self.state.checkpoint["next_cursor"], "")
        self.assertEqual(InsightsMediaSnapshot.objects.count(), 1)


class InsightsSyncWorkflowTests(TestCase):
    since = date(2026, 8, 27)
    until = date(2026, 9, 25)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="insights-sync-owner@example.com",
            first_name="Sync Owner",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INS-SYNC",
            name="Insights Sync Org",
            slug="insights-sync-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="ig-sync-1",
            username="ig-sync-1",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        self.state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            account_status=InsightsSyncStatus.COMPLETE,
        )
        InsightsSyncWork.objects.create(
            sync_state=self.state,
            stage=InsightsSyncWorkStage.ACCOUNT,
            status=InsightsSyncWorkStatus.TERMINAL,
        )
        self.content_work = InsightsSyncWork.objects.create(
            sync_state=self.state,
            stage=InsightsSyncWorkStage.CONTENT,
            status=InsightsSyncWorkStatus.PENDING,
            next_attempt_at=timezone.now(),
        )
        self.credential_patches = [
            patch(
                "apps.insights.sync_service.get_active_instagram_credential",
                return_value=SimpleNamespace(encrypted_access_token="encrypted-test-value"),
            ),
            patch("apps.insights.sync_service.decrypt_token", return_value="mock-token"),
            patch("apps.insights.sync_service.InstagramAPIClient"),
        ]
        for mocked in self.credential_patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    @staticmethod
    def media_page(media_ids, *, next_cursor=""):
        data = [
            {
                "id": media_id,
                "media_type": "IMAGE",
                "timestamp": "2026-09-10T12:00:00+0000",
                "like_count": 1,
                "comments_count": 0,
            }
            for media_id in media_ids
        ]
        paging = {"cursors": {"after": next_cursor}} if next_cursor else {}
        if next_cursor:
            paging["next"] = "present"
        return {"data": data, "paging": paging}

    @staticmethod
    def metrics_response(*, reach=1, include_engagement=True):
        data = [
            {"name": "reach", "values": [{"value": reach}]},
            {"name": "views", "values": [{"value": 1}]},
            {"name": "shares", "values": [{"value": 0}]},
            {"name": "saved", "values": [{"value": 0}]},
        ]
        if include_engagement:
            data.append({"name": "total_interactions", "values": [{"value": 1}]})
        return {"data": data}

    def _process_content_batch(self):
        from .sync_service import claim_stage_work, process_content_sync_batch

        self.content_work.refresh_from_db()
        if self.content_work.status in {
            InsightsSyncWorkStatus.PENDING,
            InsightsSyncWorkStatus.DISPATCHED,
        }:
            InsightsSyncWork.objects.filter(id=self.content_work.id).update(
                status=InsightsSyncWorkStatus.PUBLISHING,
                next_attempt_at=timezone.now(),
            )
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )
        if claim is None:
            return {"status": "not_claimed"}
        return process_content_sync_batch(claim=claim)

    def test_classified_media_failure_preserves_existing_available_metrics(self):
        from .sync_service import _store_media_metrics

        fetched_at = timezone.now() - timedelta(days=1)
        media = InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="saved-media",
            api_version="v26.0",
            metrics={"reach": {"value": 0, "availability": "available"}},
            fetched_at=fetched_at,
        )

        stored = _store_media_metrics(
            account=self.account,
            media_id=media.provider_media_id,
            metrics={"reach": {"value": None, "availability": "provider_error"}},
            preserve_available=True,
        )

        media.refresh_from_db()
        self.assertFalse(stored)
        self.assertEqual(media.metrics["reach"]["value"], 0)
        self.assertEqual(media.metrics["reach"]["availability"], "available")
        self.assertEqual(media.fetched_at, fetched_at)

    def test_partial_media_refresh_keeps_good_values_and_updates_available_metrics(self):
        from .sync_service import _store_media_metrics

        media = InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="partially-refreshed-media",
            api_version="v26.0",
            metrics={
                "reach": {"value": 0, "availability": "available"},
                "views": {"value": 10, "availability": "available"},
            },
            fetched_at=timezone.now() - timedelta(days=1),
        )

        _store_media_metrics(
            account=self.account,
            media_id=media.provider_media_id,
            metrics={
                "reach": {"value": None, "availability": "provider_error"},
                "views": {"value": 15, "availability": "available"},
            },
            preserve_available=True,
        )

        media.refresh_from_db()
        self.assertEqual(media.metrics["reach"]["value"], 0)
        self.assertEqual(media.metrics["reach"]["availability"], "available")
        self.assertEqual(media.metrics["views"]["value"], 15)

    def _prepare_retry_with_second_page_pending(self):
        from .sync_service import _persist_media_page, process_content_sync_batch

        first_page_ids = [f"media-{number}" for number in range(25)]
        _persist_media_page(
            state=self.state,
            account=self.account,
            page=self.media_page(first_page_ids, next_cursor="page-two-cursor"),
            since=self.since,
            until=self.until,
        )
        # Keep the same attempt active: explicit user refreshes create a new
        # version, while Celery continuations resume this checkpoint in place.
        self.state.status = InsightsSyncStatus.SYNCING
        self.state.content_status = InsightsSyncStatus.SYNCING
        self.state.provider_cursor = "first-page-start"
        self.state.items_discovered = 25
        self.state.items_processed = 5
        self.state.items_total = 25
        self.state.checkpoint = {
            "pending_media_ids": first_page_ids,
            "offset": 5,
            "next_cursor": "page-two-cursor",
            "has_more": True,
            "pages_fetched": 1,
            "max_pages": 1,
            "stop_reason": "page_ceiling_reached",
        }
        self.state.save()
        self.assertEqual(self.state.checkpoint["pending_media_ids"], first_page_ids)
        self.assertEqual(self.state.checkpoint["offset"], 5)
        self.assertEqual(self.state.checkpoint["next_cursor"], "page-two-cursor")
        self.assertTrue(self.state.checkpoint["has_more"])
        self.assertEqual(self.state.provider_cursor, "first-page-start")
        self.assertEqual(self.state.items_total, 25)

        with override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1):
            with patch("apps.insights.sync_service._instagram_graph_get") as graph_get:
                graph_get.side_effect = [self.metrics_response() for _ in range(20)]
                for _ in range(4):
                    self._process_content_batch()

        self.state.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 25)
        self.assertEqual(self.state.items_processed, 25)
        self.assertEqual(self.state.items_total, 25)
        self.assertEqual(self.state.provider_cursor, "page-two-cursor")

        with patch("apps.insights.sync_service._instagram_graph_get") as graph_get:
            graph_get.side_effect = [
                self.media_page([f"media-{number}" for number in range(25, 50)], next_cursor="page-three-cursor"),
                self.metrics_response(),
            ]
            with patch(
                "apps.insights.sync_service._store_media_metrics",
                side_effect=RuntimeError("stop after durable page discovery"),
            ):
                with self.assertRaisesRegex(RuntimeError, "stop after durable page discovery"):
                    self._process_content_batch()

        self.state.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 50)
        self.assertEqual(self.state.items_processed, 25)
        self.assertEqual(self.state.items_total, 50)
        # The injected exception interrupts the service-level test helper before
        # the Celery wrapper can record/release the claim. Model a retryable
        # handoff while keeping the durable page-discovery checkpoint intact.
        self.content_work.refresh_from_db()
        self.content_work.status = InsightsSyncWorkStatus.PENDING
        self.content_work.claim_token = None
        self.content_work.claimed_at = None
        self.content_work.heartbeat_at = None
        self.content_work.lease_expires_at = None
        self.content_work.save(
            update_fields=(
                "status",
                "claim_token",
                "claimed_at",
                "heartbeat_at",
                "lease_expires_at",
                "updated_at",
            )
        )
        return process_content_sync_batch

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_initial_active_page_discovery_keeps_items_total_null(self, graph_get):
        graph_get.side_effect = [
            self.media_page(["media-1"], next_cursor="next-page-cursor"),
            self.metrics_response(),
        ]

        from .sync_service import process_content_sync_batch

        self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 1)
        self.assertEqual(self.state.items_processed, 1)
        self.assertIsNone(self.state.items_total)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_consecutive_empty_pages_are_checkpointed_and_coalesced_before_later_eligible_page(self, graph_get):
        pages = [
            self.media_page([], next_cursor="empty-page-two"),
            self.media_page([], next_cursor="eligible-page"),
            self.media_page(["media-after-empty-pages"], next_cursor="final-page"),
            self.metrics_response(),
        ]
        checkpoint_observations = []

        def return_page(*args, **kwargs):
            if graph_get.call_count > 1 and len(checkpoint_observations) < 2:
                self.state.refresh_from_db()
                checkpoint_observations.append(
                    (self.state.checkpoint.get("pages_fetched"), self.state.checkpoint.get("next_cursor"))
                )
            return pages.pop(0)

        graph_get.side_effect = return_page

        result = self._process_content_batch()

        self.state.refresh_from_db()
        self.assertEqual(checkpoint_observations, [(1, "empty-page-two"), (2, "eligible-page")])
        self.assertTrue(result["continue"])
        self.assertEqual(self.state.items_discovered, 1)
        self.assertEqual(self.state.items_processed, 1)
        self.assertEqual(self.state.checkpoint["pages_fetched"], 3)
        self.assertNotIn("pending_media_ids", self.state.checkpoint)
        self.assertEqual(self.state.provider_cursor, "final-page")
        page_calls = [
            call for call in graph_get.call_args_list
            if call.args[1].endswith("/media")
        ]
        self.assertEqual(len(page_calls), 3)
        self.assertNotIn("after", page_calls[0].kwargs["params"])
        self.assertEqual(page_calls[1].kwargs["params"]["after"], "empty-page-two")
        self.assertEqual(page_calls[2].kwargs["params"]["after"], "eligible-page")

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_final_empty_page_without_cursor_completes_normally(self, graph_get):
        outside_range_page = self.media_page(["outside-range"], next_cursor="next-page-cursor")
        outside_range_page["data"][0]["timestamp"] = "2026-10-01T12:00:00+0000"
        graph_get.side_effect = [outside_range_page, {"data": [], "paging": {}}]

        first = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(first["content_status"], InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.items_processed, 0)
        self.assertEqual(self.state.items_total, 0)
        self.assertEqual(self.state.items_discovered, 0)
        self.assertEqual(self.state.checkpoint, {})
        self.assertEqual(self.state.provider_cursor, "")
        self.assertEqual(graph_get.call_count, 2)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_empty_page_ceiling_uses_existing_continuation_without_extra_page_request(self, graph_get):
        graph_get.return_value = self.media_page([], next_cursor="next-empty-page")

        result = self._process_content_batch()

        self.state.refresh_from_db()
        self.assertTrue(result["continue"])
        self.assertEqual(graph_get.call_count, 1)
        self.assertEqual(self.state.items_discovered, 0)
        self.assertEqual(self.state.provider_cursor, "next-empty-page")
        self.assertEqual(self.state.checkpoint["pages_fetched"], 0)
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_empty_page_retry_resumes_from_last_checkpoint_cursor(self, graph_get):
        graph_get.side_effect = [
            self.media_page([], next_cursor="durable-next-cursor"),
            InstagramAPIError(
                "Temporary provider failure",
                status_code=503,
                error_payload={"error": {"code": 999}},
            ),
        ]
        failed = self._process_content_batch()
        self.assertTrue(failed["retryable"])
        self.state.refresh_from_db()
        self.assertEqual(self.state.checkpoint["pages_fetched"], 1)
        self.assertEqual(self.state.checkpoint["next_cursor"], "durable-next-cursor")
        self.assertEqual(self.state.provider_cursor, "")

        self.content_work.refresh_from_db()
        self.content_work.status = InsightsSyncWorkStatus.PENDING
        self.content_work.claim_token = None
        self.content_work.claimed_at = None
        self.content_work.heartbeat_at = None
        self.content_work.lease_expires_at = None
        self.content_work.save(update_fields=(
            "status", "claim_token", "claimed_at", "heartbeat_at", "lease_expires_at", "updated_at",
        ))
        graph_get.side_effect = [{"data": [], "paging": {}}]

        resumed = self._process_content_batch()

        self.assertEqual(resumed["content_status"], InsightsSyncStatus.COMPLETE)
        page_calls = [
            call for call in graph_get.call_args_list
            if call.args[1].endswith("/media")
        ]
        self.assertEqual(page_calls[-1].kwargs["params"]["after"], "durable-next-cursor")

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_stale_generation_cannot_commit_coalesced_instagram_page(self, graph_get):
        from .sync_service import StaleInsightsWorkClaim, claim_stage_work, process_content_sync_batch

        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )
        self.assertIsNotNone(claim)
        InsightsSyncWork.objects.filter(id=self.content_work.id).update(generation=claim["generation"] + 1)
        graph_get.return_value = self.media_page([], next_cursor="must-not-persist")

        with self.assertRaises(StaleInsightsWorkClaim):
            process_content_sync_batch(claim=claim)

        self.state.refresh_from_db()
        self.assertNotIn("next_cursor", self.state.checkpoint)
        self.assertEqual(self.state.items_discovered, 0)

    def test_partial_retry_discovery_advances_known_total_before_processing(self):
        process_content_sync_batch = self._prepare_retry_with_second_page_pending()

        with (
            override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1),
            patch("apps.insights.sync_service.CONTENT_INSIGHTS_BATCH_SIZE", 1),
            patch(
                "apps.insights.sync_service._instagram_graph_get",
                return_value=self.metrics_response(),
            ),
        ):
            self._process_content_batch()

        self.state.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 50)
        self.assertEqual(self.state.items_processed, 26)
        self.assertEqual(self.state.items_total, 50)
        self.assertLessEqual(self.state.items_processed, self.state.items_total)

    def test_classified_media_failure_after_new_discovery_advances_processed_safely(self):
        process_content_sync_batch = self._prepare_retry_with_second_page_pending()
        provider_error = InstagramAPIError(
            "Media item unavailable.",
            status_code=400,
            error_payload={"error": {"code": 100, "message": "Object does not exist."}},
        )

        with patch(
            "apps.insights.sync_service._instagram_graph_get",
            side_effect=provider_error,
        ), patch("apps.insights.sync_service.CONTENT_INSIGHTS_BATCH_SIZE", 1):
            self._process_content_batch()

        self.state.refresh_from_db()
        self.assertEqual(self.state.items_discovered, 50)
        self.assertEqual(self.state.items_processed, 26)
        self.assertEqual(self.state.items_total, 50)
        self.assertLessEqual(self.state.items_processed, self.state.items_total)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_media_upsert_preserves_real_zero_values_and_completes(self, graph_get):
        self.state.provider_cursor = "cursor-to-clear-on-complete"
        self.state.save(update_fields=("provider_cursor", "updated_at"))
        graph_get.side_effect = [
            self.media_page(["media-1"]),
            self.metrics_response(reach=0),
        ]

        from .sync_service import process_content_sync_batch

        result = self._process_content_batch()

        from .sync_service import _persist_media_page

        _persist_media_page(
            state=self.state,
            account=self.account,
            page=self.media_page(["media-1"]),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(result["status"], InsightsSyncStatus.COMPLETE)
        snapshot = InsightsMediaSnapshot.objects.get(
            social_account=self.account,
            provider_media_id="media-1",
        )
        self.assertEqual(snapshot.metrics["reach"]["value"], 0)
        self.assertEqual(snapshot.metrics["reach"]["availability"], "available")
        self.assertEqual(snapshot.metrics["engagement"]["value"], 1)
        self.assertEqual(InsightsMediaSnapshot.objects.filter(provider_media_id="media-1").count(), 1)
        self.assertEqual(graph_get.call_count, 2)
        self.state.refresh_from_db()
        self.assertEqual(self.state.status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.checkpoint, {})
        self.assertEqual(self.state.provider_cursor, "")
        self.assertEqual(self.state.items_processed, 1)
        self.assertEqual(self.state.items_total, 1)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_missing_metric_is_unavailable_and_results_in_partial_sync(self, graph_get):
        self.state.provider_cursor = "cursor-to-retain-on-partial"
        self.state.save(update_fields=("provider_cursor", "updated_at"))
        graph_get.side_effect = [
            self.media_page(["media-1"]),
            self.metrics_response(include_engagement=False),
        ]

        from .sync_service import process_content_sync_batch

        result = self._process_content_batch()
        snapshot = InsightsMediaSnapshot.objects.get(provider_media_id="media-1")

        self.assertEqual(result["status"], InsightsSyncStatus.PARTIAL)
        self.assertIsNone(snapshot.metrics["engagement"]["value"])
        self.assertEqual(snapshot.metrics["engagement"]["availability"], "unavailable")
        self.state.refresh_from_db()
        self.assertEqual(self.state.provider_cursor, "cursor-to-retain-on-partial")
        self.assertEqual(self.state.checkpoint["pending_media_ids"], ["media-1"])
        self.assertEqual(self.state.checkpoint["offset"], 1)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_batch_is_bounded_and_resume_uses_checkpoint(self, graph_get):
        media_ids = [f"media-{number}" for number in range(6)]
        graph_get.side_effect = [
            self.media_page(media_ids, next_cursor="cursor-1"),
            *[self.metrics_response() for _ in range(6)],
            {"data": [], "paging": {}},
        ]

        from .sync_service import process_content_sync_batch
        first = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(first["status"], InsightsSyncStatus.SYNCING)
        self.assertEqual(first["processed"], 5)
        self.assertEqual(self.state.items_processed, 5)
        self.assertEqual(self.state.checkpoint["offset"], 5)
        self.assertEqual(graph_get.call_count, 6)

        second = self._process_content_batch()
        self.assertEqual(second["status"], InsightsSyncStatus.SYNCING)
        third = self._process_content_batch()
        self.assertEqual(third["status"], InsightsSyncStatus.COMPLETE)
        # Resume consumes the saved sixth ID without refetching the media page.
        self.assertEqual(graph_get.call_count, 8)
        self.assertEqual(InsightsMediaSnapshot.objects.count(), 6)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_page_ceiling_rearms_and_preserves_pending_page_for_automatic_continuation(self, graph_get):
        media_ids = [f"media-{number}" for number in range(6)]
        self.state.provider_cursor = "input-cursor"
        self.state.save(update_fields=("provider_cursor", "updated_at"))
        graph_get.side_effect = [
            self.media_page(media_ids, next_cursor="next-page-cursor"),
            *[self.metrics_response() for _ in range(5)],
        ]

        from .sync_service import process_content_sync_batch

        result = self._process_content_batch()
        self.state.refresh_from_db()

        self.assertTrue(result["continue"])
        self.assertEqual(result["status"], InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.provider_cursor, "input-cursor")
        self.assertEqual(self.state.checkpoint["pending_media_ids"], media_ids)
        self.assertEqual(self.state.checkpoint["offset"], 5)
        self.assertEqual(self.state.checkpoint["next_cursor"], "next-page-cursor")
        self.assertEqual(self.state.checkpoint["pages_fetched"], 0)
        self.assertNotIn("max_pages", self.state.checkpoint)
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.state.items_total, self.state.items_discovered)
        self.assertEqual(graph_get.call_count, 6)
        self.assertEqual(InsightsMediaSnapshot.objects.count(), 6)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._dispatch_sync_tasks")
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_partial_retry_resumes_pending_ids_and_resets_attempt_page_counter(
        self, graph_get, _dispatch
    ):
        media_ids = [f"media-{number}" for number in range(6)]
        from .sync_service import _persist_media_page

        _persist_media_page(
            state=self.state,
            account=self.account,
            page=self.media_page(media_ids, next_cursor="next-page-cursor"),
            since=self.since,
            until=self.until,
        )
        self.state.status = InsightsSyncStatus.SYNCING
        self.state.content_status = InsightsSyncStatus.SYNCING
        self.state.provider_cursor = "input-cursor"
        self.state.items_discovered = len(media_ids)
        self.state.checkpoint = {
            "pending_media_ids": media_ids,
            "offset": 5,
            "next_cursor": "next-page-cursor",
            "has_more": True,
            "pages_fetched": 1,
            "max_pages": 8,
            "stop_reason": "page_ceiling_reached",
        }
        self.state.save()
        graph_get.side_effect = [
            self.metrics_response(),
            self.media_page(["media-6"]),
            self.metrics_response(),
        ]

        from .sync_service import process_content_sync_batch

        self.state.refresh_from_db()
        self.assertEqual(self.state.provider_cursor, "input-cursor")
        self.assertEqual(self.state.checkpoint["pending_media_ids"], media_ids)
        self.assertEqual(self.state.checkpoint["offset"], 5)

        with override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1):
            resumed = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(self.state.checkpoint["max_pages"], 1)
        self.assertEqual(resumed["status"], InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.items_processed, 1)
        self.assertEqual(self.state.provider_cursor, "next-page-cursor")
        self.assertEqual(graph_get.call_count, 1)
        self.assertEqual(graph_get.call_args_list[0].args[1], "media-5/insights")

        next_batch = self._process_content_batch()
        self.assertEqual(next_batch["content_status"], InsightsSyncStatus.COMPLETE)
        self.assertEqual(next_batch["status"], InsightsSyncStatus.SYNCING)
        self.assertEqual(graph_get.call_count, 3)
        self.assertEqual(InsightsMediaSnapshot.objects.count(), 7)

    @patch("apps.insights.sync_service._dispatch_sync_tasks")
    def test_active_attempt_can_resolve_changed_worker_ceiling_without_resetting_checkpoint(
        self, _dispatch
    ):
        from .sync_service import _persist_media_page

        _persist_media_page(
            state=self.state,
            account=self.account,
            page=self.media_page(["media-1"], next_cursor="next-cursor"),
            since=self.since,
            until=self.until,
        )

        self.state.status = InsightsSyncStatus.SYNCING
        self.state.content_status = InsightsSyncStatus.SYNCING
        self.state.provider_cursor = "saved-cursor"
        self.state.items_discovered = 1
        self.state.checkpoint = {
            "pending_media_ids": ["media-1"],
            "offset": 0,
            "next_cursor": "next-cursor",
            "has_more": True,
            "pages_fetched": 1,
            "max_pages": 1,
            "stop_reason": "page_ceiling_reached",
        }
        self.state.save()

        self.state.refresh_from_db()
        self.assertEqual(self.state.checkpoint["max_pages"], 1)
        self.assertEqual(self.state.checkpoint["pages_fetched"], 1)
        self.assertEqual(self.state.checkpoint["pending_media_ids"], ["media-1"])
        self.assertEqual(self.state.checkpoint["offset"], 0)
        self.assertEqual(self.state.checkpoint["next_cursor"], "next-cursor")
        self.assertTrue(self.state.checkpoint["has_more"])
        self.assertEqual(self.state.provider_cursor, "saved-cursor")

        with override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1):
            from .sync_service import process_content_sync_batch

            with patch("apps.insights.sync_service._instagram_graph_get") as graph_get:
                graph_get.return_value = self.metrics_response()
                first_retry_batch = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertTrue(first_retry_batch["continue"])
        self.assertEqual(self.state.checkpoint["max_pages"], 1)

        with override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=10):
            with patch("apps.insights.sync_service._instagram_graph_get") as graph_get:
                graph_get.side_effect = [
                    self.media_page(["media-2"], next_cursor="third-cursor"),
                    self.metrics_response(),
                ]
                # Finish the pending page handoff, then fetch the next page
                # using the newly configured worker ceiling.
                self._process_content_batch()
                resumed = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertTrue(resumed["continue"])
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.checkpoint["max_pages"], 10)
        self.assertEqual(self.state.checkpoint["pages_fetched"], 0)
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
        self.assertEqual(self.state.provider_cursor, "third-cursor")

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=2)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_provider_cursor_advances_only_after_page_ids_are_processed(self, graph_get):
        media_ids = [f"media-{number}" for number in range(6)]
        self.state.provider_cursor = "input-cursor"
        self.state.save(update_fields=("provider_cursor", "updated_at"))
        graph_get.side_effect = [
            self.media_page(media_ids, next_cursor="next-page-cursor"),
            *[self.metrics_response() for _ in range(6)],
            self.media_page(["media-6"]),
            self.metrics_response(),
        ]

        from .sync_service import process_content_sync_batch

        first = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(first["processed"], 5)
        self.assertEqual(self.state.provider_cursor, "input-cursor")
        self.assertEqual(self.state.checkpoint["offset"], 5)

        second = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(second["status"], InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.provider_cursor, "next-page-cursor")
        self.assertEqual(self.state.checkpoint["pages_fetched"], 1)
        self.assertEqual(self.state.checkpoint["max_pages"], 2)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_no_next_provider_page_completes_normally_at_page_ceiling(self, graph_get):
        media_ids = [f"media-{number}" for number in range(6)]
        graph_get.side_effect = [
            self.media_page(media_ids),
            *[self.metrics_response() for _ in range(6)],
        ]

        from .sync_service import process_content_sync_batch

        first = self._process_content_batch()
        self.assertEqual(first["status"], InsightsSyncStatus.SYNCING)
        self.assertTrue(first["continue"])
        second = self._process_content_batch()

        self.assertEqual(second["status"], InsightsSyncStatus.COMPLETE)
        self.state.refresh_from_db()
        self.assertEqual(self.state.checkpoint, {})
        self.assertEqual(self.state.provider_cursor, "")
        self.assertEqual(graph_get.call_count, 7)
        self.assertEqual(InsightsMediaSnapshot.objects.count(), 6)
        self.assertEqual(InsightsContentSnapshotItem.objects.filter(sync_state=self.state).count(), 6)
        self.assertTrue(all(
            item.metrics.get("reach", {}).get("availability") == "available"
            for item in InsightsContentSnapshotItem.objects.filter(sync_state=self.state)
        ))

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_page_ceiling_does_not_request_an_additional_provider_page(self, graph_get):
        graph_get.side_effect = [
            self.media_page([f"media-{number}" for number in range(6)], next_cursor="next"),
            *[self.metrics_response() for _ in range(5)],
        ]

        from .sync_service import process_content_sync_batch

        result = self._process_content_batch()
        self.assertEqual(graph_get.call_count, 6)
        self.assertTrue(result["continue"])
        self.state.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.provider_cursor, "")
        self.assertEqual(self.state.checkpoint["offset"], 5)

    @override_settings(
        INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1,
    )
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_bounded_content_tasks_continue_to_completion_without_another_sync_request(self, graph_get):
        from .tasks import sync_instagram_content_batch_task

        graph_get.side_effect = [
            self.media_page(["media-1"], next_cursor="page-two-cursor"),
            self.metrics_response(),
            self.media_page(["media-2"]),
            self.metrics_response(),
        ]
        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))

        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            side_effect=[
                SimpleNamespace(id="continuation-task-1"),
                SimpleNamespace(id="continuation-task-2"),
            ],
        ) as publish:
            first = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation,
            )
            self.state.refresh_from_db()
            self.content_work.refresh_from_db()
            self.assertTrue(first["continue"])
            self.assertEqual(self.state.account_status, InsightsSyncStatus.COMPLETE)
            self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
            self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.DISPATCHED)
            self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
            self.assertEqual(self.state.checkpoint["pending_media_ids"], ["media-1"])
            self.assertEqual(self.state.checkpoint["offset"], 1)
            self.assertEqual(self.state.provider_cursor, "page-two-cursor")

            second = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation,
            )
            self.assertTrue(second["continue"])
            third = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation,
            )

        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(third["content_status"], InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.account_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(self.state.items_discovered, 2)
        self.assertEqual(self.state.items_processed, 2)
        self.assertEqual(
            InsightsMediaSnapshot.objects.filter(social_account=self.account).count(),
            2,
        )
        media_page_requests = [
            call for call in graph_get.call_args_list
            if call.args[1].endswith("/media")
        ]
        self.assertEqual(len(media_page_requests), 2)
        publish.assert_has_calls(
            [
                call(kwargs={"work_id": str(self.content_work.id), "generation": self.content_work.generation}),
                call(kwargs={"work_id": str(self.content_work.id), "generation": self.content_work.generation}),
            ]
        )
        self.assertEqual(publish.call_count, 2)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_automatic_continuation_dispatch_failure_remains_recoverable(self, graph_get):
        from .tasks import sync_instagram_content_batch_task

        graph_get.side_effect = [
            self.media_page(["media-1"], next_cursor="page-two-cursor"),
            self.metrics_response(),
        ]
        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))

        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            side_effect=ConnectionError("broker unavailable"),
        ):
            result = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation,
            )

        self.assertTrue(result["continue"])
        self.content_work.refresh_from_db()
        self.state.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.content_work.last_error_code, "broker_publish_failed")
        self.assertGreater(self.content_work.next_attempt_at, timezone.now())
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_invalid_credential_during_continuation_does_not_auto_chain(self, graph_get):
        from .tasks import sync_instagram_content_batch_task

        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))
        with patch(
            "apps.insights.sync_service.get_active_instagram_credential",
            return_value=None,
        ), patch.object(sync_instagram_content_batch_task, "apply_async") as publish:
            result = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation,
            )

        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.state.content_status, InsightsSyncStatus.FAILED)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        graph_get.assert_not_called()
        publish.assert_not_called()

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_exhausted_provider_retry_does_not_auto_chain(self, graph_get):
        from .tasks import sync_instagram_content_batch_task

        graph_get.side_effect = InstagramAPIError(
            "Temporary provider failure",
            status_code=503,
            error_payload={"error": {"code": 999, "message": "Temporary outage"}},
        )
        InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="media-1",
            api_version="v26.0",
            metrics={},
        )
        self.state.checkpoint = {
            "pending_media_ids": ["media-1"],
            "offset": 0,
            "next_cursor": "page-two-cursor",
            "has_more": True,
            "pages_fetched": 1,
            "max_pages": 1,
            "automatic_continuations": 1,
        }
        self.state.items_discovered = 1
        self.state.items_total = 1
        self.state.save(update_fields=("checkpoint", "items_discovered", "items_total", "updated_at"))
        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.provider_retry_count = 3
        self.content_work.save(update_fields=("status", "provider_retry_count", "updated_at"))

        with patch.object(sync_instagram_content_batch_task, "apply_async") as publish:
            result = sync_instagram_content_batch_task.run(
                work_id=str(self.content_work.id),
                generation=self.content_work.generation,
            )

        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(result["status"], InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        publish.assert_not_called()

    @override_settings(
        INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1,
    )
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_automatic_continuation_budget_stops_at_user_retryable_partial(self, graph_get):
        graph_get.side_effect = [
            self.media_page(["media-1"], next_cursor="page-two-cursor"),
            self.metrics_response(),
            self.media_page(["media-2"], next_cursor="page-three-cursor"),
            self.metrics_response(),
        ]

        first = self._process_content_batch()
        self.assertTrue(first["continue"])
        second = self._process_content_batch()
        self.assertTrue(second["continue"])
        third = self._process_content_batch()
        self.assertEqual(third["status"], InsightsSyncStatus.PARTIAL)

        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.PARTIAL)
        self.assertEqual(self.state.checkpoint["automatic_continuations"], 1)
        self.assertEqual(self.state.checkpoint["stop_reason"], "automatic_continuation_budget_reached")
        self.assertEqual(self.state.provider_cursor, "page-three-cursor")
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_metric_failure_at_page_ceiling_does_not_auto_continue(self, graph_get):
        graph_get.side_effect = [
            self.media_page(["media-1"], next_cursor="page-two-cursor"),
            self.metrics_response(include_engagement=False),
        ]

        result = self._process_content_batch()

        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(result["content_status"], InsightsSyncStatus.PARTIAL)
        self.assertNotIn("continue", result)
        self.assertEqual(self.state.error_code, "metric_unavailable")
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)
        self.assertEqual(graph_get.call_count, 2)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=1)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_unusable_next_page_cursor_does_not_auto_continue(self, graph_get):
        graph_get.side_effect = [
            {"data": [{"id": "media-1", "timestamp": "2026-09-10T12:00:00+0000"}], "paging": {"next": "present"}},
            self.metrics_response(),
        ]

        result = self._process_content_batch()

        self.state.refresh_from_db()
        self.content_work.refresh_from_db()
        self.assertEqual(result["content_status"], InsightsSyncStatus.PARTIAL)
        self.assertNotIn("continue", result)
        self.assertEqual(self.state.error_code, "pagination_unavailable")
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.TERMINAL)

    @override_settings(INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT=2)
    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_page_checkpoint_retains_ceiling_metadata_across_page_handoff(self, graph_get):
        graph_get.side_effect = [
            self.media_page(["media-1"], next_cursor="next"),
            self.metrics_response(),
        ]

        from .sync_service import process_content_sync_batch

        result = self._process_content_batch()
        self.state.refresh_from_db()
        self.assertEqual(result["status"], InsightsSyncStatus.SYNCING)
        self.assertEqual(
            self.state.checkpoint,
            {"pages_fetched": 1, "max_pages": 2, "automatic_continuations": 0},
        )
        self.assertEqual(self.state.provider_cursor, "next")

    def test_duplicate_sync_request_reuses_the_active_state(self):
        from .sync_service import request_insights_sync

        with patch("apps.insights.sync_service._dispatch_sync_tasks") as dispatch:
            with self.captureOnCommitCallbacks(execute=True):
                first = request_insights_sync(
                    social_account_id=self.account.id,
                    since=self.since,
                    until=self.until,
                )
            with self.captureOnCommitCallbacks(execute=True):
                second = request_insights_sync(
                    social_account_id=self.account.id,
                    since=self.since,
                    until=self.until,
                )

        self.assertEqual(first["sync_state_id"], second["sync_state_id"])
        self.assertEqual(
            InsightsSyncState.objects.filter(
                social_account=self.account,
                since=self.since,
                until=self.until,
                status__in=(InsightsSyncStatus.QUEUED, InsightsSyncStatus.SYNCING),
            ).count(),
            1,
        )
        self.assertEqual(dispatch.call_count, 0)

    def test_stage_work_claim_is_atomic_and_duplicate_delivery_is_ignored(self):
        from .sync_service import claim_stage_work

        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
            celery_task_id="first-delivery",
        )

        self.assertIsNotNone(claim)
        self.assertIsNone(claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
            celery_task_id="duplicate-delivery",
        ))
        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.CLAIMED)
        self.assertEqual(self.content_work.celery_task_id, "first-delivery")
        self.assertIsNotNone(self.content_work.claim_token)
        self.assertGreater(self.content_work.lease_expires_at, self.content_work.claimed_at)

    def test_reconciler_recovers_expired_claim_with_new_generation_and_checkpoint_intact(self):
        from .sync_service import claim_stage_work, reconcile_insights_sync_work

        self.state.checkpoint = {
            "max_pages": 1,
            "pages_fetched": 1,
            "pending_media_ids": ["media-pending"],
            "offset": 2,
            "provider_cursor": "opaque-next",
            "next_cursor": "opaque-next",
            "has_more": True,
        }
        self.state.provider_cursor = "opaque-current"
        self.state.save(update_fields=("checkpoint", "provider_cursor", "updated_at"))
        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )
        self.content_work.refresh_from_db()
        stale_claimed_at = timezone.now() - timedelta(minutes=46)
        self.content_work.claimed_at = stale_claimed_at
        self.content_work.heartbeat_at = stale_claimed_at
        self.content_work.lease_expires_at = stale_claimed_at + timedelta(minutes=40)
        self.content_work.save(
            update_fields=("claimed_at", "heartbeat_at", "lease_expires_at", "updated_at")
        )

        with patch("apps.insights.sync_service.dispatch_stage_work", return_value=True) as dispatch:
            result = reconcile_insights_sync_work()

        self.content_work.refresh_from_db()
        self.state.refresh_from_db()
        self.assertEqual(result["published"], 1)
        self.assertEqual(self.content_work.generation, claim["generation"] + 1)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertIsNone(self.content_work.claim_token)
        self.assertEqual(self.state.checkpoint["max_pages"], 1)
        self.assertEqual(self.state.checkpoint["pending_media_ids"], ["media-pending"])
        self.assertEqual(self.state.checkpoint["offset"], 2)
        self.assertEqual(self.state.provider_cursor, "opaque-current")
        dispatch.assert_called_once_with(self.content_work.id)

    def test_reconciler_does_not_take_over_unexpired_legitimate_claim(self):
        from .sync_service import claim_stage_work, reconcile_insights_sync_work

        self.content_work.status = InsightsSyncWorkStatus.DISPATCHED
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )

        with patch("apps.insights.sync_service.dispatch_stage_work") as dispatch:
            result = reconcile_insights_sync_work()

        self.content_work.refresh_from_db()
        self.assertEqual(result["candidates"], 0)
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.CLAIMED)
        self.assertEqual(self.content_work.generation, claim["generation"])
        dispatch.assert_not_called()

    def test_dispatch_failure_keeps_due_intent_for_bounded_retry(self):
        from .sync_service import dispatch_stage_work
        from .tasks import sync_instagram_content_batch_task

        with patch.object(
            sync_instagram_content_batch_task,
            "apply_async",
            side_effect=ConnectionError("broker unavailable"),
        ):
            self.assertFalse(dispatch_stage_work(self.content_work.id))

        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.content_work.dispatch_attempt, 1)
        self.assertGreater(self.content_work.next_attempt_at, timezone.now())
        self.assertEqual(self.content_work.last_error_code, "broker_publish_failed")

    def test_reconciler_never_redispatches_terminal_sync_state(self):
        from .sync_service import reconcile_insights_sync_work

        self.state.status = InsightsSyncStatus.COMPLETE
        self.state.content_status = InsightsSyncStatus.COMPLETE
        self.state.save(update_fields=("status", "content_status", "updated_at"))
        self.content_work.status = InsightsSyncWorkStatus.PENDING
        self.content_work.next_attempt_at = timezone.now() - timedelta(seconds=1)
        self.content_work.save(update_fields=("status", "next_attempt_at", "updated_at"))

        with patch("apps.insights.sync_service.dispatch_stage_work") as dispatch:
            reconcile_insights_sync_work()

        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        dispatch.assert_not_called()

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_transient_provider_error_is_classified_without_losing_checkpoint(self, graph_get):
        graph_get.return_value = self.media_page(["media-1"])

        from .sync_service import process_content_sync_batch

        graph_get.side_effect = InstagramAPIError(
            "Temporary provider failure",
            status_code=429,
            error_payload={"error": {"code": 4, "message": "Rate limited"}},
        )
        result = self._process_content_batch()

        self.assertTrue(result["retryable"])
        self.assertEqual(result["error_code"], "rate_limited")
        self.state.refresh_from_db()
        self.assertEqual(self.state.status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.items_processed, 0)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_transient_error_uses_durable_bounded_retry(self, graph_get):
        from .tasks import sync_instagram_content_batch_task

        graph_get.side_effect = InstagramAPIError(
            "Temporary provider failure",
            status_code=503,
            error_payload={"error": {"code": 999, "message": "Temporary outage"}},
        )
        self.content_work.status = InsightsSyncWorkStatus.PUBLISHING
        self.content_work.save(update_fields=("status", "updated_at"))
        result = sync_instagram_content_batch_task.run(
            work_id=str(self.content_work.id), generation=self.content_work.generation,
        )
        self.assertEqual(result["status"], "retrying")
        self.content_work.refresh_from_db()
        self.assertEqual(self.content_work.status, InsightsSyncWorkStatus.PENDING)
        self.assertEqual(self.content_work.provider_retry_count, 1)
        self.assertIsNotNone(self.content_work.next_attempt_at)
        self.state.refresh_from_db()
        self.assertEqual(self.state.status, InsightsSyncStatus.SYNCING)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.SYNCING)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_disconnected_account_fails_without_provider_request(self, graph_get):
        from .sync_service import process_content_sync_batch

        self.account.status = SocialAccountStatus.DISCONNECTED
        self.account.save(update_fields=("status",))
        result = self._process_content_batch()

        self.assertEqual(result["status"], InsightsSyncStatus.FAILED)
        graph_get.assert_not_called()

    def test_task_arguments_and_state_do_not_contain_credentials(self):
        from .tasks import sync_account_insights_task, sync_instagram_content_batch_task

        args = repr((
            sync_account_insights_task.name,
            sync_instagram_content_batch_task.name,
            str(self.account.id),
            str(self.state.id),
            self.since.isoformat(),
            self.until.isoformat(),
        ))
        state_values = repr(self.state.checkpoint)
        self.assertNotIn("mock-token", args + state_values)
        self.assertNotIn("encrypted-test-value", args + state_values)

    @patch("apps.insights.tasks.process_content_sync_batch", side_effect=ValueError("private-token Authorization provider-body"))
    def test_unexpected_content_exception_logs_safe_task_context_and_traceback(
        self, _process
    ):
        from .tasks import sync_instagram_content_batch_task

        with self.assertLogs("apps.insights.tasks", level="ERROR") as captured:
            self.content_work.status = InsightsSyncWorkStatus.PUBLISHING
            self.content_work.save(update_fields=("status", "updated_at"))
            sync_instagram_content_batch_task.push_request(id="insights-task-test-id")
            try:
                with self.assertRaises(ValueError):
                    sync_instagram_content_batch_task.run(
                        work_id=str(self.content_work.id), generation=self.content_work.generation,
                    )
            finally:
                sync_instagram_content_batch_task.pop_request()

        output = "\n".join(captured.output)
        self.assertIn("Traceback (most recent call last)", output)
        self.assertIn("[exception message redacted]", output)
        self.assertNotIn("private-token", output)
        self.assertNotIn("Authorization", output)
        self.assertNotIn("provider-body", output)
        record = captured.records[0]
        self.assertEqual(record.exception_type, "ValueError")
        self.assertEqual(record.sync_state_id, str(self.state.id))
        self.assertEqual(record.task_name, sync_instagram_content_batch_task.name)
        self.assertEqual(record.task_id, "insights-task-test-id")
        self.state.refresh_from_db()
        self.assertEqual(self.state.content_status, InsightsSyncStatus.FAILED)
        self.assertEqual(self.state.status, InsightsSyncStatus.FAILED)

    def _assert_stage_order(self, first_field, first_status, second_field, second_status, expected):
        from .sync_service import _update_sync_state

        InsightsSyncState.objects.filter(id=self.state.id).update(
            status=InsightsSyncStatus.QUEUED,
            account_status=InsightsSyncStatus.QUEUED,
            content_status=InsightsSyncStatus.QUEUED,
            started_at=None,
            completed_at=None,
        )
        _update_sync_state(self.state.id, **{first_field: first_status})
        self.state.refresh_from_db()
        self.assertEqual(self.state.status, InsightsSyncStatus.SYNCING)
        self.assertIsNone(self.state.completed_at)
        _update_sync_state(self.state.id, **{second_field: second_status})
        self.state.refresh_from_db()
        self.assertEqual(self.state.status, expected)
        if expected in {
            InsightsSyncStatus.COMPLETE,
            InsightsSyncStatus.PARTIAL,
            InsightsSyncStatus.FAILED,
        }:
            self.assertIsNotNone(self.state.completed_at)

    def test_content_completes_before_account_keeps_overall_syncing(self):
        self._assert_stage_order(
            "content_status", InsightsSyncStatus.COMPLETE,
            "account_status", InsightsSyncStatus.COMPLETE,
            InsightsSyncStatus.COMPLETE,
        )

    def test_account_completes_before_content_keeps_overall_syncing(self):
        self._assert_stage_order(
            "account_status", InsightsSyncStatus.COMPLETE,
            "content_status", InsightsSyncStatus.COMPLETE,
            InsightsSyncStatus.COMPLETE,
        )

    def test_account_failure_wins_after_content_completes(self):
        self._assert_stage_order(
            "account_status", InsightsSyncStatus.FAILED,
            "content_status", InsightsSyncStatus.COMPLETE,
            InsightsSyncStatus.FAILED,
        )

    def test_content_failure_wins_after_account_completes(self):
        self._assert_stage_order(
            "content_status", InsightsSyncStatus.FAILED,
            "account_status", InsightsSyncStatus.COMPLETE,
            InsightsSyncStatus.FAILED,
        )

    def test_both_partial_stages_produce_partial_overall_state(self):
        self._assert_stage_order(
            "account_status", InsightsSyncStatus.PARTIAL,
            "content_status", InsightsSyncStatus.PARTIAL,
            InsightsSyncStatus.PARTIAL,
        )

    def test_one_active_and_one_terminal_stage_remains_syncing(self):
        from .sync_service import _update_sync_state

        _update_sync_state(
            self.state.id,
            account_status=InsightsSyncStatus.SYNCING,
            content_status=InsightsSyncStatus.COMPLETE,
        )
        self.state.refresh_from_db()
        self.assertEqual(self.state.status, InsightsSyncStatus.SYNCING)
        self.assertIsNone(self.state.completed_at)

    @patch("apps.insights.sync_service._instagram_graph_get")
    def test_content_worker_completion_does_not_finalize_queued_account_stage(self, graph_get):
        self.state.account_status = InsightsSyncStatus.QUEUED
        self.state.save(update_fields=("account_status", "updated_at"))
        graph_get.side_effect = [
            self.media_page(["media-1"]),
            self.metrics_response(),
        ]

        from .sync_service import process_content_sync_batch

        result = self._process_content_batch()
        self.state.refresh_from_db()

        self.assertEqual(result["content_status"], InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.status, InsightsSyncStatus.SYNCING)
        self.assertIsNone(self.state.completed_at)

    def test_late_stage_update_does_not_overwrite_terminal_overall_state(self):
        from .sync_service import _update_sync_state

        InsightsSyncState.objects.filter(id=self.state.id).update(
            status=InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            completed_at=timezone.now(),
        )
        _update_sync_state(self.state.id, content_status=InsightsSyncStatus.SYNCING)
        self.state.refresh_from_db()

        self.assertEqual(self.state.status, InsightsSyncStatus.COMPLETE)
        self.assertEqual(self.state.content_status, InsightsSyncStatus.COMPLETE)

    def test_sql_timing_collector_classifies_nested_media_storage_and_logs_no_sql_or_params(self):
        from .sync_service import (
            _InsightsSqlTimingCollector,
            _fenced_stage_transaction,
            _store_media_metrics_with_timing,
            claim_stage_work,
        )

        InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="instrumentation-media",
            api_version="v26.0",
            metrics={"likes": {"value": 1, "availability": "available"}},
        )
        collector = _InsightsSqlTimingCollector()
        self.content_work.status = InsightsSyncWorkStatus.PUBLISHING
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )
        self.assertIsNotNone(claim)
        sql_secret = "instrumentation-private-sql"
        parameter_secret = "instrumentation-private-parameter"
        with self.assertLogs("apps.insights.sync_service", level="DEBUG") as captured:
            with _fenced_stage_transaction(**claim, _timing_collector=collector) as (locked, _work):
                _store_media_metrics_with_timing(
                    timing_collector=collector,
                    account=self.account,
                    media_id="instrumentation-media",
                    metrics={"reach": {"value": 17, "availability": "available"}},
                    sync_state=locked,
                )
                collector.set_phase("checkpoint")
                locked.checkpoint = {"instrumentation_probe": True}
                locked.save(update_fields=("checkpoint", "updated_at"))
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 'instrumentation-private-sql'")
                    cursor.execute("SELECT %s", [parameter_secret])

        summary = collector.snapshot()
        helper_sql = summary["sql"]["helper"]
        self.assertNotIn("fence_reference_lookup", summary["sql"])
        self.assertEqual(summary["sql"]["fence_state_lock"]["other_safe_sql"]["count"], 1)
        self.assertEqual(summary["sql"]["fence_work_lock"]["other_safe_sql"]["count"], 1)
        self.assertEqual(helper_sql.get("savepoint_create", {}).get("count", 0), 0)
        self.assertEqual(helper_sql.get("savepoint_release", {}).get("count", 0), 0)
        self.assertEqual(helper_sql["select_for_update_media"]["count"], 1)
        self.assertEqual(helper_sql["update_media"]["count"], 1)
        self.assertEqual(helper_sql["select_for_update_content"]["count"], 1)
        self.assertEqual(helper_sql["insert_content"]["count"], 1)
        self.assertEqual(helper_sql["update_content"]["count"], 1)
        self.assertEqual(summary["sql"]["checkpoint"]["checkpoint_update"]["count"], 1)
        self.assertEqual(summary["measurements"]["helper"]["store_media_metrics_wall_seconds"]["count"], 1)
        self.assertEqual(summary["measurements"]["helper"]["non_sql_residual"]["count"], 1)
        self.assertEqual(summary["measurements"]["outer_transaction"]["outer_transaction_wall_seconds"]["count"], 1)
        self.assertEqual(summary["measurements"]["outer_transaction"]["outer_atomic_exit_seconds"]["count"], 1)
        rendered_logs = "\n".join(captured.output)
        self.assertNotIn(sql_secret, rendered_logs)
        self.assertNotIn(parameter_secret, rendered_logs)
        self.assertNotIn("SELECT %s", rendered_logs)

        media = InsightsMediaSnapshot.objects.get(provider_media_id="instrumentation-media")
        self.assertEqual(media.metrics["reach"]["value"], 17)
        content_item = InsightsContentSnapshotItem.objects.get(
            sync_state=self.state,
            provider_media_id="instrumentation-media",
        )
        self.assertEqual(content_item.metrics["reach"]["value"], 17)

    def test_sql_timing_wrapper_preserves_fenced_rollback_when_helper_fails(self):
        from .sync_service import (
            _InsightsSqlTimingCollector,
            _fenced_stage_transaction,
            _store_media_metrics_with_timing,
            claim_stage_work,
        )

        media = InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="instrumentation-rollback-media",
            api_version="v26.0",
            metrics={"reach": {"value": 3, "availability": "available"}},
        )
        content_item = InsightsContentSnapshotItem.objects.create(
            sync_state=self.state,
            provider_media_id=media.provider_media_id,
            api_version=self.state.api_version,
            metrics={"reach": {"value": 3, "availability": "available"}},
        )
        collector = _InsightsSqlTimingCollector()
        self.content_work.status = InsightsSyncWorkStatus.PUBLISHING
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )
        self.assertIsNotNone(claim)

        class RaiseAfterContentUpdate:
            def __call__(self, execute, sql, params, many, context):
                result = execute(sql, params, many, context)
                if collector._classify(sql) == "update_content":
                    raise RuntimeError("instrumentation rollback probe")
                return result

        with connection.execute_wrapper(collector), connection.execute_wrapper(RaiseAfterContentUpdate()):
            with self.assertRaisesRegex(RuntimeError, "instrumentation rollback probe"):
                with _fenced_stage_transaction(**claim, _timing_collector=collector) as (locked, _work):
                    locked.checkpoint = {"rollback_probe": True}
                    locked.items_discovered += 1
                    locked.items_processed += 1
                    locked.save(update_fields=(
                        "checkpoint", "items_discovered", "items_processed", "updated_at",
                    ))
                    _store_media_metrics_with_timing(
                        timing_collector=collector,
                        account=self.account,
                        media_id=media.provider_media_id,
                        metrics={"reach": {"value": 99, "availability": "available"}},
                        sync_state=locked,
                    )

        media.refresh_from_db()
        self.assertEqual(media.metrics["reach"]["value"], 3)
        content_item.refresh_from_db()
        self.assertEqual(content_item.metrics["reach"]["value"], 3)
        self.state.refresh_from_db()
        self.assertNotIn("rollback_probe", self.state.checkpoint)
        self.assertEqual(self.state.items_discovered, 0)
        self.assertEqual(self.state.items_processed, 0)
        helper_sql = collector.snapshot()["sql"]["helper"]
        self.assertEqual(helper_sql.get("savepoint_create", {}).get("count", 0), 0)
        self.assertEqual(helper_sql.get("savepoint_release", {}).get("count", 0), 0)

    def test_fence_uses_claim_state_id_and_rejects_mismatched_state(self):
        from .sync_service import (
            StaleInsightsWorkClaim,
            _InsightsSqlTimingCollector,
            _fenced_stage_transaction,
            claim_stage_work,
        )

        self.content_work.status = InsightsSyncWorkStatus.PUBLISHING
        self.content_work.save(update_fields=("status", "updated_at"))
        claim = claim_stage_work(
            work_id=self.content_work.id,
            generation=self.content_work.generation,
        )
        self.assertIsNotNone(claim)

        wrong_state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=self.since - timedelta(days=1),
            until=self.until,
            api_version="v26.0",
        )
        mismatched_claim = {**claim, "sync_state_id": str(wrong_state.id)}
        with self.assertRaises(StaleInsightsWorkClaim):
            with _fenced_stage_transaction(**mismatched_claim):
                self.fail("A claim with a mismatched state ID must not enter the fence")

        collector = _InsightsSqlTimingCollector()
        claim_without_state_id = {
            name: value for name, value in claim.items() if name != "sync_state_id"
        }
        with _fenced_stage_transaction(
            **claim_without_state_id, _timing_collector=collector,
        ) as (locked, _work):
            self.assertEqual(locked.id, self.state.id)
        self.assertEqual(
            collector.snapshot()["sql"]["fence_reference_lookup"]["other_safe_sql"]["count"],
            1,
        )


class InsightsSqlTimingStandaloneTests(TransactionTestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="insights-db-timing@example.com",
            first_name="Timing Owner",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INS-DB-TIMING",
            name="Insights DB Timing Org",
            slug="insights-db-timing-org",
            industry="Retail",
            created_by=self.owner,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="ig-db-timing",
            username="ig-db-timing",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        self.state = InsightsSyncState.objects.create(
            social_account=self.account,
            since=date(2026, 8, 27),
            until=date(2026, 9, 25),
            api_version="v26.0",
            account_status=InsightsSyncStatus.COMPLETE,
        )

    def test_standalone_helper_is_measured_without_a_nested_savepoint(self):
        from .sync_service import _InsightsSqlTimingCollector, _store_media_metrics_with_timing

        media = InsightsMediaSnapshot.objects.create(
            social_account=self.account,
            provider_media_id="standalone-instrumentation-media",
            api_version="v26.0",
            metrics={},
        )
        self.assertFalse(connection.in_atomic_block)
        collector = _InsightsSqlTimingCollector()
        with connection.execute_wrapper(collector):
            _store_media_metrics_with_timing(
                timing_collector=collector,
                account=self.account,
                media_id=media.provider_media_id,
                metrics={"reach": {"value": 24, "availability": "available"}},
                sync_state=self.state,
            )
        self.assertFalse(connection.in_atomic_block)
        summary = collector.snapshot()
        helper_sql = summary["sql"]["helper"]
        self.assertEqual(helper_sql.get("savepoint_create", {}).get("count", 0), 0)
        self.assertEqual(helper_sql.get("savepoint_release", {}).get("count", 0), 0)
        self.assertEqual(helper_sql["update_media"]["count"], 1)
        self.assertEqual(helper_sql["insert_content"]["count"], 1)
        media.refresh_from_db()
        self.assertEqual(media.metrics["reach"]["value"], 24)
        content_item = InsightsContentSnapshotItem.objects.get(
            sync_state=self.state,
            provider_media_id=media.provider_media_id,
        )
        self.assertEqual(content_item.metrics["reach"]["value"], 24)

class InsightsAPIAccessTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="insights-owner@example.com",
            first_name="Insights Owner",
            password="password",
        )
        self.other_user = User.objects.create_user(
            email="insights-other@example.com",
            first_name="Other User",
            password="password",
        )
        self.organization = self.create_organization(
            "ORG-INSIGHTS-OWNER", "Insights Owner Org", self.owner,
        )
        self.other_organization = self.create_organization(
            "ORG-INSIGHTS-OTHER", "Insights Other Org", self.other_user,
        )
        self.account = self.create_account(
            self.organization,
            name="Owner Instagram",
            platform=SocialPlatform.INSTAGRAM,
        )
        self.foreign_account = self.create_account(
            self.other_organization,
            name="Other Facebook",
            platform=SocialPlatform.FACEBOOK,
        )
        self.accounts_url = reverse(
            "insights-organization-account-list",
            kwargs={"organization_id": self.organization.organization_id},
        )
        self.data_url = reverse(
            "insights-account-data",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": self.account.id,
            },
        )

    @staticmethod
    def create_organization(organization_id, name, owner):
        return Organization.objects.create(
            organization_id=organization_id,
            name=name,
            slug=organization_id.lower(),
            industry="Retail",
            created_by=owner,
        )

    @staticmethod
    def create_account(organization, *, name, platform, **overrides):
        values = {
            "organization": organization,
            "platform": platform,
            "platform_account_id": f"provider-{name.lower().replace(' ', '-')}",
            "account_name": name,
            "status": SocialAccountStatus.CONNECTED,
            "is_valid": True,
        }
        values.update(overrides)
        return SocialAccount.objects.create(**values)

    def test_insights_endpoints_require_authentication(self):
        for url in (
            reverse("insights-organization-list"),
            self.accounts_url,
            self.data_url,
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 401)

    def test_organization_discovery_returns_only_owned_organizations(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get(reverse("insights-organization-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]],
            [self.organization.organization_id],
        )

    def test_account_discovery_returns_connected_valid_accounts_and_filters_platform(self):
        self.client.force_authenticate(self.owner)
        facebook_account = self.create_account(
            self.organization,
            name="Owner Facebook",
            platform=SocialPlatform.FACEBOOK,
        )
        self.create_account(
            self.organization,
            name="Disconnected Instagram",
            platform=SocialPlatform.INSTAGRAM,
            status=SocialAccountStatus.DISCONNECTED,
        )
        self.create_account(
            self.organization,
            name="Invalid Instagram",
            platform=SocialPlatform.INSTAGRAM,
            is_valid=False,
        )

        response = self.client.get(self.accounts_url, {"platform": "INSTAGRAM"})

        self.assertEqual(response.status_code, 200)
        accounts = response.data["data"]
        self.assertEqual(len(accounts), 1)
        self.assertEqual(str(accounts[0]["id"]), str(self.account.id))
        self.assertNotEqual(str(accounts[0]["id"]), str(facebook_account.id))

    def test_account_data_contract_is_scoped_to_selected_account(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get(self.data_url)

        self.assertEqual(response.status_code, 200)
        payload = response.data["data"]
        self.assertEqual(str(payload["account"]["id"]), str(self.account.id))
        self.assertEqual(payload["account"]["platform"], SocialPlatform.INSTAGRAM)
        self.assertEqual(payload["filters"]["organization_id"], self.organization.organization_id)
        self.assertEqual(payload["metrics"]["followers"]["reason"], "invalid_credential")
        self.assertEqual(payload["follower_growth"]["availability"], "unavailable")
        self.assertEqual(
            payload["account_performance"]["metrics"]["followers"]["reason"],
            "invalid_credential",
        )
        self.assertEqual(payload["content_performance"]["results"], [])

    def test_account_from_different_organization_is_not_selectable(self):
        self.client.force_authenticate(self.owner)
        url = reverse(
            "insights-account-data",
            kwargs={
                "organization_id": self.organization.organization_id,
                "social_account_id": self.foreign_account.id,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_discover_accounts_for_another_users_organization(self):
        self.client.force_authenticate(self.owner)
        url = reverse(
            "insights-organization-account-list",
            kwargs={"organization_id": self.other_organization.organization_id},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_disconnected_and_invalid_accounts_are_not_selectable(self):
        self.client.force_authenticate(self.owner)
        disconnected = self.create_account(
            self.organization,
            name="Disconnected Account",
            platform=SocialPlatform.INSTAGRAM,
            status=SocialAccountStatus.DISCONNECTED,
        )
        invalid = self.create_account(
            self.organization,
            name="Invalid Account",
            platform=SocialPlatform.INSTAGRAM,
            is_valid=False,
        )

        for account in (disconnected, invalid):
            url = reverse(
                "insights-account-data",
                kwargs={
                    "organization_id": self.organization.organization_id,
                    "social_account_id": account.id,
                },
            )
            with self.subTest(account=account.account_name):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_unknown_platform_filter_is_rejected(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get(self.accounts_url, {"platform": "unknown"})

        self.assertEqual(response.status_code, 400)

    def test_account_data_rejects_invalid_and_future_date_ranges(self):
        self.client.force_authenticate(self.owner)
        today = timezone.localdate()
        for params in (
            {"since": today.isoformat(), "until": (today - timedelta(days=1)).isoformat()},
            {"since": today.isoformat(), "until": (today + timedelta(days=1)).isoformat()},
            {"since": (today - timedelta(days=90)).isoformat(), "until": today.isoformat()},
        ):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(self.data_url, params).status_code, 400)


class InsightsProviderTests(SimpleTestCase):
    since = date(2026, 9, 1)
    until = date(2026, 9, 25)

    @staticmethod
    def account(platform, account_id="provider-account"):
        return SimpleNamespace(
            id=f"local-{account_id}",
            platform=platform,
            platform_account_id=account_id,
            organization=SimpleNamespace(organization_id="ORG-OWNER"),
        )

    @patch(
        "apps.integrations.meta.client.requests.get",
        side_effect=requests.ConnectionError(
            "Request URL contained access_token=SECRET_ACCESS_TOKEN"
        ),
    )
    def test_meta_get_transport_failure_does_not_log_access_token(self, _get):
        with self.assertLogs("apps.integrations.meta.client", level="ERROR") as captured:
            with self.assertRaises(MetaAPIError):
                MetaAPIClient().get(
                    "/page-id",
                    access_token="SECRET_ACCESS_TOKEN",
                )

        self.assertNotIn("SECRET_ACCESS_TOKEN", "\n".join(captured.output))

    @patch("apps.insights.providers._resolve_instagram_token", return_value="test-ig-token")
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_instagram_fetches_account_native_media_and_normalizes_available_metrics(
        self, client_class, _resolve_token,
    ):
        client = client_class.return_value
        client.graph_get.side_effect = [
            {"id": "ig-1", "username": "sample", "name": "Sample", "followers_count": 42, "media_count": 2},
            {"data": [
                {"name": "reach", "total_value": {"value": 100}},
                {"name": "views", "total_value": {"value": 180}},
                {"name": "total_interactions", "total_value": {"value": 25}},
                {"name": "accounts_engaged", "total_value": {"value": 18}},
            ]},
            {"data": [{"name": "follows_and_unfollows", "total_value": {"value": {"follows": 5, "unfollows": 2}}}]},
            {"data": [{
                "id": "ig-media-1",
                "caption": "Native Instagram post",
                "media_type": "IMAGE",
                "permalink": "https://instagram.example/p/1",
                "timestamp": "2026-09-10T12:00:00+0000",
                "like_count": 17,
                "comments_count": 3,
            }, {
                "id": "ig-media-2",
                "caption": "Native Instagram post without interactions metric",
                "media_type": "VIDEO",
                "permalink": "https://instagram.example/p/2",
                "timestamp": "2026-09-11T12:00:00+0000",
                "like_count": 1,
                "comments_count": 0,
            }], "paging": {}},
            {"data": [
                {"name": "reach", "values": [{"value": 40}]},
                {"name": "views", "values": [{"value": 70}]},
                {"name": "shares", "values": [{"value": 4}]},
                {"name": "saved", "values": [{"value": 3}]},
                {"name": "total_interactions", "values": [{"value": 1}]},
            ]},
            {"data": [
                {"name": "reach", "values": [{"value": 5}]},
                {"name": "views", "values": [{"value": 8}]},
                {"name": "shares", "values": [{"value": 0}]},
                {"name": "saved", "values": [{"value": 0}]},
            ]},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.INSTAGRAM, "ig-1"),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(client.graph_get.call_count, 6)
        args, kwargs = client.graph_get.call_args_list[3]
        self.assertEqual(args[0], "ig-1/media")
        self.assertEqual(kwargs["params"]["limit"], CONTENT_PAGE_SIZE)
        self.assertEqual(data["content_performance"]["results"][0]["content_id"], "ig-media-1")
        item_metrics = data["content_performance"]["results"][0]["metrics"]
        self.assertEqual(item_metrics["likes"]["value"], 17)
        self.assertEqual(item_metrics["comments"]["value"], 3)
        self.assertEqual(item_metrics["reach"]["value"], 40)
        self.assertEqual(item_metrics["shares"]["value"], 4)
        self.assertEqual(item_metrics["saves"]["value"], 3)
        self.assertEqual(item_metrics["engagement"]["value"], 1)
        self.assertEqual(item_metrics["engagement"]["provider_metric"], "total_interactions")
        self.assertEqual(item_metrics["engagement"]["availability"], "available")
        engagement_request = client.graph_get.call_args_list[4].kwargs["params"]["metric"]
        self.assertIn("total_interactions", engagement_request.split(","))
        missing_engagement = data["content_performance"]["results"][1]["metrics"]["engagement"]
        self.assertIsNone(missing_engagement["value"])
        self.assertEqual(missing_engagement["availability"], "unavailable")
        self.assertEqual(missing_engagement["reason"], "metric_not_returned")
        self.assertEqual(
            data["provider_metadata"]["provider_account_id"],
            "ig-1",
        )
        self.assertEqual(
            data["content_performance"]["results"][0]["field_availability"]["permalink"],
            "available",
        )
        self.assertEqual(data["metrics"]["reach"]["value"], 100)
        self.assertEqual(data["metrics"]["views"]["value"], 180)
        self.assertEqual(data["metrics"]["engagement"]["value"], 25)
        self.assertEqual(data["follower_growth"]["change"]["value"], 3)
        self.assertEqual(data["metrics"]["impressions"]["availability"], "not_supported")
        self.assertEqual(item_metrics["likes"]["source"], "instagram")
        self.assertEqual(data["follower_growth"]["availability"], "available")

    @patch("apps.insights.providers._resolve_facebook_token", return_value="test-fb-token")
    @patch("apps.insights.providers.MetaAPIClient")
    def test_facebook_fetches_page_insights_and_native_posts(self, client_class, _resolve_token):
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-1", "name": "Page", "followers_count": 1234},
            {"data": [
                {"name": "page_follows", "period": "day", "values": [
                    {"value": 500, "end_time": "2026-08-26T07:00:00+0000"},
                    {"value": 1200, "end_time": "2026-09-01T07:00:00+0000"},
                    {"value": 1234, "end_time": "2026-09-25T07:00:00+0000"},
                    {"value": 1500, "end_time": "2026-09-26T07:00:00+0000"},
                ]},
                {"name": "page_post_engagements", "period": "day", "values": [
                    {"value": 25, "end_time": "2026-09-25T07:00:00+0000"},
                ]},
                {"name": "page_media_view", "period": "day", "values": [
                    {"value": 800, "end_time": "2026-09-25T07:00:00+0000"},
                ]},
                {"name": "page_total_media_view_unique", "period": "day", "values": [
                    {"value": 500, "end_time": "2026-09-25T07:00:00+0000"},
                ]},
            ]},
            {"data": [{
                "id": "fb-post-1",
                "message": "Native Page post",
                "created_time": "2026-09-10T12:00:00+0000",
                "permalink_url": "https://facebook.example/posts/1",
                "shares": {"count": 4},
                "comments": {"summary": {"total_count": 2}},
                "reactions": {"summary": {"total_count": 8}},
            }]},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.FACEBOOK, "page-1"),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(client.get.call_count, 3)
        insights_call = client.get.call_args_list[1]
        self.assertEqual(insights_call.args[0], "/page-1/insights")
        self.assertEqual(insights_call.kwargs["params"]["since"], "2026-09-01")
        self.assertEqual(insights_call.kwargs["params"]["until"], "2026-09-25")
        self.assertEqual(data["metrics"]["media_views"]["value"], 800)
        self.assertEqual(data["metrics"]["media_views"]["availability"], "available")
        self.assertEqual(data["metrics"]["unique_media_views"]["value"], 500)
        self.assertEqual(data["metrics"]["reach"]["availability"], "not_supported")
        self.assertEqual(data["metrics"]["impressions"]["availability"], "not_supported")
        self.assertEqual(data["follower_growth"]["change"]["value"], 34)
        self.assertEqual(data["follower_growth"]["points"][0]["date"], "2026-09-01")
        self.assertEqual(data["follower_growth"]["points"][-1]["date"], "2026-09-25")
        self.assertEqual(data["content_performance"]["results"][0]["content_id"], "fb-post-1")
        self.assertEqual(data["provider_metadata"]["account_name"], "Page")
        self.assertEqual(data["provider_metadata"]["provider_account_id"], "page-1")
        self.assertEqual(data["content_performance"]["results"][0]["metrics"]["reactions"]["value"], 8)

    @patch("apps.insights.providers._resolve_facebook_token", return_value="test-fb-token")
    @patch("apps.insights.providers.MetaAPIClient")
    def test_unsupported_metric_is_not_reported_as_zero(self, client_class, _resolve_token):
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-1", "name": "Page"},
            MetaAPIError(
                "Provider response contains private details.",
                status_code=400,
                error_payload={"error": {"code": 100, "message": "Unsupported metric requested."}},
            ),
            {"data": []},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.FACEBOOK, "page-1"),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(data["metrics"]["media_views"]["availability"], "not_supported")
        self.assertIsNone(data["metrics"]["media_views"]["value"])

    @patch("apps.insights.providers._resolve_instagram_token", return_value="test-ig-token")
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_missing_instagram_insights_permission_is_structured(self, client_class, _resolve_token):
        client_class.return_value.graph_get.side_effect = [
            {"id": "provider-account", "username": "sample", "followers_count": 42},
            InstagramAPIError(
                "Permission unavailable.",
                status_code=403,
                error_payload={"error": {"code": 10, "message": "Application does not have permission."}},
            ),
            {"data": [], "paging": {}},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.INSTAGRAM),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(data["account_performance"]["availability"], "available")
        self.assertEqual(
            data["metrics"]["reach"]["reason"],
            "instagram_business_manage_insights",
        )
        self.assertEqual(data["metrics"]["reach"]["label"], "Reach")
        self.assertEqual(data["metrics"]["reach"]["provider_metric"], "reach")
        self.assertEqual(data["metrics"]["views"]["availability"], "permission_required")
        self.assertEqual(data["metrics"]["impressions"]["availability"], "not_supported")
        self.assertEqual(client_class.return_value.graph_get.call_count, 3)

    @patch("apps.insights.providers._resolve_instagram_token", return_value="test-ig-token")
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_instagram_date_filtering_is_inclusive_and_local_for_native_media(
        self, client_class, _resolve_token,
    ):
        client = client_class.return_value
        client.graph_get.side_effect = [
            {"id": "provider-account", "username": "sample", "followers_count": 42},
            {"data": [
                {"name": "reach", "total_value": {"value": 20}},
                {"name": "views", "total_value": {"value": 30}},
                {"name": "total_interactions", "total_value": {"value": 4}},
                {"name": "accounts_engaged", "total_value": {"value": 3}},
            ]},
            {"data": []},
            {"data": [
                {"id": "before", "media_type": "IMAGE", "timestamp": "2026-08-31T23:59:59+0000"},
                {"id": "inside-start", "media_type": "IMAGE", "timestamp": "2026-09-01T00:00:00+0000"},
                {"id": "inside-end", "media_type": "VIDEO", "timestamp": "2026-09-25T23:59:59+0000"},
                {"id": "after", "media_type": "VIDEO", "timestamp": "2026-09-26T00:00:00+0000"},
            ], "paging": {}},
            {"data": [{"name": "reach", "values": [{"value": 1}]}]},
            {"data": [{"name": "reach", "values": [{"value": 2}]}]},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.INSTAGRAM),
            since=date(2026, 9, 1),
            until=date(2026, 9, 25),
        )

        self.assertEqual(
            [item["content_id"] for item in data["content_performance"]["results"]],
            ["inside-start", "inside-end"],
        )
        self.assertEqual(client.graph_get.call_args_list[1].kwargs["params"]["since"], "2026-09-01")
        self.assertEqual(client.graph_get.call_args_list[1].kwargs["params"]["until"], "2026-09-25")

    @patch("apps.insights.providers._resolve_facebook_token", return_value="test-fb-token")
    @patch("apps.insights.providers.MetaAPIClient")
    def test_provider_errors_are_normalized(self, client_class, _resolve_token):
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-1", "name": "Page"},
            MetaAPIError(
                "Temporary provider outage.",
                status_code=503,
                error_payload={"error": {"code": 999, "message": "Temporary outage."}},
            ),
            {"data": []},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.FACEBOOK, "page-1"),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(data["metrics"]["engagement"]["availability"], "provider_error")
        self.assertEqual(data["metrics"]["engagement"]["reason"], "provider_temporary_error")

    @patch("apps.insights.providers._resolve_facebook_token", return_value="test-fb-token")
    @patch("apps.insights.providers.MetaAPIClient")
    def test_facebook_post_content_permission_is_explicit(self, client_class, _resolve_token):
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-1", "name": "Page", "followers_count": 10},
            {"data": [
                {"name": "page_follows", "period": "day", "values": [
                    {"value": 10, "end_time": "2026-09-25T07:00:00+0000"},
                ]},
            ]},
            MetaAPIError(
                "Page read permission required.",
                status_code=403,
                error_payload={"error": {"code": 200, "message": "Permissions error: access denied."}},
            ),
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.FACEBOOK, "page-1"),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(data["content_performance"]["availability"], "permission_required")
        self.assertEqual(data["content_performance"]["reason"], "pages_read_engagement")
        self.assertEqual(data["content_performance"]["results"], [])

    @patch("apps.insights.providers._resolve_facebook_token", return_value="test-fb-token")
    @patch("apps.insights.providers.MetaAPIClient")
    def test_facebook_content_date_filter_and_pagination_are_bounded(
        self, client_class, _resolve_token,
    ):
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-1", "name": "Page", "followers_count": 10},
            {"data": []},
            {"data": [
                {"id": "old", "created_time": "2026-08-31T12:00:00+0000"},
                {"id": "inside-one", "created_time": "2026-09-02T12:00:00+0000", "message": "One"},
            ], "paging": {"next": "https://provider.invalid/?after=page-1", "cursors": {"after": "page-1"}}},
            {"data": [
                {"id": "inside-two", "created_time": "2026-09-20T12:00:00+0000", "message": "Two"},
                {"id": "future", "created_time": "2026-09-26T12:00:00+0000"},
            ], "paging": {"next": "https://provider.invalid/?after=page-2", "cursors": {"after": "page-2"}}},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.FACEBOOK, "page-1"),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(client.get.call_count, MAX_CONTENT_PAGES_PER_REQUEST + 2)
        self.assertEqual(
            [item["content_id"] for item in data["content_performance"]["results"]],
            ["inside-one", "inside-two"],
        )
        self.assertTrue(data["content_performance"]["next"])
        self.assertEqual(client.get.call_args_list[2].kwargs["params"]["limit"], CONTENT_PAGE_SIZE)
        self.assertEqual(client.get.call_args_list[3].kwargs["params"]["after"], "page-1")

    @patch("apps.insights.providers._resolve_instagram_token", side_effect=InstagramIntegrationError("secret token value"))
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_invalid_instagram_credential_does_not_call_provider(self, client_class, _resolve_token):
        data = fetch_provider_insights(
            account=self.account(SocialPlatform.INSTAGRAM),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(data["content_performance"]["availability"], "unavailable")
        self.assertEqual(data["content_performance"]["reason"], "invalid_credential")
        client_class.return_value.graph_get.assert_not_called()

    @patch("apps.insights.providers._resolve_instagram_token", return_value="test-ig-token")
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_cursor_is_bound_to_the_selected_account(self, client_class, _resolve_token):
        first_account = self.account(SocialPlatform.INSTAGRAM, "ig-1")
        other_account = self.account(SocialPlatform.INSTAGRAM, "ig-2")
        cursor = _make_content_cursor(
            after="provider-cursor",
            account=other_account,
            since=self.since,
            until=self.until,
        )

        with self.assertRaises(ValidationError):
            fetch_provider_insights(
                account=first_account,
                since=self.since,
                until=self.until,
                cursor=cursor,
            )
        client_class.return_value.graph_get.assert_not_called()

    @patch("apps.insights.providers._resolve_instagram_token", return_value="VERY_SECRET_TOKEN")
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_content_pagination_is_bounded_and_cursor_does_not_contain_token(
        self, client_class, _resolve_token,
    ):
        client = client_class.return_value
        client.graph_get.side_effect = [
            {"id": "provider-account", "username": "sample", "followers_count": 42},
            {"data": [
                {"name": "reach", "total_value": {"value": 0}},
                {"name": "views", "total_value": {"value": 0}},
                {"name": "total_interactions", "total_value": {"value": 0}},
                {"name": "accounts_engaged", "total_value": {"value": 0}},
            ]},
            {"data": []},
            {"data": [], "paging": {"next": "https://provider.invalid/?after=cursor-1", "cursors": {"after": "cursor-1"}}},
            {"data": [], "paging": {"next": "https://provider.invalid/?after=cursor-2", "cursors": {"after": "cursor-2"}}},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.INSTAGRAM),
            since=self.since,
            until=self.until,
        )

        self.assertEqual(client.graph_get.call_count, MAX_CONTENT_PAGES_PER_REQUEST + 3)
        self.assertEqual(data["content_performance"]["next"] is not None, True)
        self.assertNotIn("VERY_SECRET_TOKEN", data["content_performance"]["next"])
        self.assertEqual(client.graph_get.call_args_list[4].kwargs["params"]["after"], "cursor-1")

    @patch("apps.insights.providers._resolve_facebook_token", return_value="SECRET_ACCESS_TOKEN")
    @patch("apps.insights.providers.MetaAPIClient")
    def test_error_payload_secrets_are_not_returned(self, client_class, _resolve_token):
        client = client_class.return_value
        client.get.side_effect = [
            {"id": "page-1", "name": "Page"},
            MetaAPIError(
                "SECRET_ACCESS_TOKEN leaked in provider message",
                status_code=503,
                error_payload={"error": {"code": 999, "message": "SECRET_ACCESS_TOKEN"}},
            ),
            {"data": []},
        ]

        data = fetch_provider_insights(
            account=self.account(SocialPlatform.FACEBOOK, "page-1"),
            since=self.since,
            until=self.until,
        )

        self.assertNotIn("SECRET_ACCESS_TOKEN", json.dumps(data))

    @patch("apps.insights.providers._resolve_instagram_token", return_value="VERY_SECRET_TOKEN")
    @patch("apps.insights.providers.InstagramAPIClient")
    def test_instagram_transport_errors_are_redacted_and_not_logged(
        self, client_class, _resolve_token,
    ):
        client = client_class.return_value
        client.graph_get.side_effect = [
            {"id": "ig-1", "username": "sample", "followers_count": 42},
            {"data": [
                {"name": "reach", "total_value": {"value": 10}},
                {"name": "views", "total_value": {"value": 20}},
                {"name": "total_interactions", "total_value": {"value": 3}},
                {"name": "accounts_engaged", "total_value": {"value": 2}},
            ]},
            {"data": []},
            requests.ConnectionError(
                "Request to graph.instagram.com failed with access_token=VERY_SECRET_TOKEN"
            ),
        ]

        with self.assertNoLogs("apps.insights.providers", level="WARNING"):
            data = fetch_provider_insights(
                account=self.account(SocialPlatform.INSTAGRAM, "ig-1"),
                since=self.since,
                until=self.until,
            )

        self.assertEqual(data["content_performance"]["availability"], "provider_error")
        self.assertNotIn("VERY_SECRET_TOKEN", json.dumps(data))
