from datetime import date, datetime, timezone
from contextlib import contextmanager
from html import escape
from io import BytesIO
from pathlib import Path
import sys
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from apps.accounts.models import User
from apps.insights.models import (
    InsightsAccountSnapshot,
    InsightsContentSnapshotItem,
    InsightsSnapshotSlot,
    InsightsSyncState,
    InsightsSyncStatus,
)
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .rendering import (
    REPORT_VIEWPORT,
    ReportRenderError,
    _log_cgroup_memory,
    _read_cgroup_memory_bytes,
    render_report_png,
)


class InsightsReportApiTests(APITestCase):
    since = date(2026, 9, 1)
    until = date(2026, 9, 7)

    def setUp(self):
        self.owner = User.objects.create_user(
            email="reports-owner@example.com",
            first_name="Report Owner",
            password="password",
        )
        self.other_user = User.objects.create_user(
            email="reports-other@example.com",
            first_name="Other Owner",
            password="password",
        )
        self.organization = self.create_organization("ORG-REPORT-1", "Report Org", self.owner)
        self.other_organization = self.create_organization("ORG-REPORT-2", "Other Org", self.other_user)
        self.account = self.create_account(self.organization, "instagram", "report-ig")
        self.foreign_account = self.create_account(self.other_organization, "facebook", "foreign-fb")
        self.state = self.create_published_version(self.account, "instagram")
        self.url = reverse("insights-report-preview")
        self.client.force_authenticate(self.owner)

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
    def create_account(organization, platform, name):
        return SocialAccount.objects.create(
            organization=organization,
            platform=platform,
            platform_account_id=name,
            username=name,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )

    def create_published_version(self, account, platform):
        state = InsightsSyncState.objects.create(
            social_account=account,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            status=InsightsSyncStatus.COMPLETE,
            account_status=InsightsSyncStatus.COMPLETE,
            content_status=InsightsSyncStatus.COMPLETE,
            account_completed_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
            content_completed_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        )
        InsightsAccountSnapshot.objects.create(
            social_account=account,
            sync_state=state,
            since=self.since,
            until=self.until,
            api_version="v26.0",
            metrics={
                "followers": {"value": 12400, "availability": "available"},
                "reach": {"value": 84600, "availability": "available"},
                "engagement": {"value": 6800, "availability": "available"},
                "views": {"value": 126400, "availability": "available"},
            },
            fetched_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        )
        InsightsSnapshotSlot.objects.create(
            social_account=account,
            duration_days=7,
            published_account_sync_state=state,
            published_content_sync_state=state,
        )
        content_keys = (
            ("reach", "engagement", "likes", "comments", "shares")
            if platform == SocialPlatform.INSTAGRAM
            else ("reach", "views", "reactions", "comments", "clicks")
        )
        for index, reach in enumerate((15, 70, 35, 90, 25, 120, 55), start=1):
            values = {key: index * 3 for key in content_keys}
            values["reach"] = reach
            if "likes" in values:
                values["likes"] = index * 4
            InsightsContentSnapshotItem.objects.create(
                sync_state=state,
                provider_media_id=f"{account.platform_account_id}-post-{index}",
                media_type="IMAGE",
                caption=f"Saved post {index}",
                published_at=datetime(2026, 9, index, 12, tzinfo=timezone.utc),
                api_version="v26.0",
                metrics={key: {"value": value, "availability": "available"} for key, value in values.items()},
            )
        return state

    def payload(self, **overrides):
        data = {
            "organization_id": self.organization.organization_id,
            "social_account_id": str(self.account.id),
            "platform": self.account.platform,
            "since": self.since.isoformat(),
            "until": self.until.isoformat(),
            "mode": "current",
            "meta_ads": [],
        }
        data.update(overrides)
        return data

    def test_preview_uses_exact_published_range_stats_and_top_five_by_reach(self):
        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, 200)
        report = response.data["data"]["report"]
        self.assertEqual(report["date_range"]["since"], self.since.isoformat())
        self.assertEqual(report["date_range"]["until"], self.until.isoformat())
        self.assertEqual([item["label"] for item in report["stats"]], [
            "Total Reach", "Total Engagement", "Total Followers", "Total Views", "Total Posts",
        ])
        self.assertEqual([item["metric"]["value"] for item in report["stats"]], [84600, 6800, 12400, 126400, 7])
        self.assertEqual([item["provider_media_id"] for item in report["content_performance"]], [
            "report-ig-post-6", "report-ig-post-4", "report-ig-post-2", "report-ig-post-7", "report-ig-post-3",
        ])
        self.assertEqual([field["key"] for field in report["content_fields"]], [
            "reach", "engagement", "likes", "comments", "shares",
        ])
        self.assertEqual(report["daily_reach"][0]["value"], 15)
        self.assertEqual(report["mode"], "current")
        self.assertEqual(report["meta_ads"], [])
        self.assertTrue(response.data["data"]["render_token"])

    def test_preview_does_not_mix_accounts_or_organizations(self):
        response = self.client.post(self.url, self.payload(
            organization_id=self.other_organization.organization_id,
            social_account_id=str(self.foreign_account.id),
            platform=SocialPlatform.FACEBOOK,
        ), format="json")
        self.assertEqual(response.status_code, 404)

    def test_preview_uses_saved_snapshot_dates_when_calendar_date_changes(self):
        response = self.client.post(self.url, self.payload(
            since="2026-09-29",
            until="2026-10-05",
        ), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["report"]["date_range"], {
            "since": self.since.isoformat(),
            "until": self.until.isoformat(),
            "duration_days": 7,
        })

    def test_preview_rejects_unsupported_duration_and_missing_snapshots(self):
        unsupported = self.client.post(self.url, self.payload(until="2026-09-08"), format="json")
        self.assertEqual(unsupported.status_code, 400)

        InsightsSnapshotSlot.objects.filter(social_account=self.account).update(is_deleted=True)
        missing = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(missing.status_code, 409)

    def test_add_ads_validates_limit_dates_and_non_negative_leads(self):
        rows = [{"date": self.since.isoformat(), "total_leads": "2.50"} for _ in range(5)]
        valid = self.client.post(self.url, self.payload(mode="add_ads", meta_ads=rows), format="json")
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.data["data"]["report"]["meta_ads"][0], {
            "date": self.since.isoformat(), "total_leads": "2.50",
        })
        self.assertEqual([item["label"] for item in valid.data["data"]["report"]["stats"]], [
            "Total Reach", "Total Engagement", "Total Followers", "Total Views", "Total Posts",
        ])

        too_many = self.client.post(self.url, self.payload(mode="add_ads", meta_ads=rows + rows[:1]), format="json")
        self.assertEqual(too_many.status_code, 400)
        invalid_date = self.client.post(self.url, self.payload(
            mode="add_ads", meta_ads=[{"date": "not-a-date", "total_leads": "1"}],
        ), format="json")
        self.assertEqual(invalid_date.status_code, 400)
        invalid_leads = self.client.post(self.url, self.payload(
            mode="add_ads", meta_ads=[{"date": self.since.isoformat(), "total_leads": "-1"}],
        ), format="json")
        self.assertEqual(invalid_leads.status_code, 400)
        current_with_ads = self.client.post(self.url, self.payload(meta_ads=rows[:1]), format="json")
        self.assertEqual(current_with_ads.status_code, 400)

    def test_facebook_preview_uses_facebook_content_fields_and_fewer_than_five_rows(self):
        facebook_state = self.create_published_version(self.foreign_account, SocialPlatform.FACEBOOK)
        InsightsContentSnapshotItem.objects.filter(sync_state=facebook_state).exclude(
            provider_media_id="foreign-fb-post-1",
        ).delete()
        response = self.client.post(self.url, self.payload(
            organization_id=self.other_organization.organization_id,
            social_account_id=str(self.foreign_account.id),
            platform=SocialPlatform.FACEBOOK,
        ), format="json")

        self.assertEqual(response.status_code, 404)
        self.client.force_authenticate(self.other_user)
        response = self.client.post(self.url, self.payload(
            organization_id=self.other_organization.organization_id,
            social_account_id=str(self.foreign_account.id),
            platform=SocialPlatform.FACEBOOK,
        ), format="json")
        self.assertEqual(response.status_code, 200)
        report = response.data["data"]["report"]
        self.assertEqual(len(report["content_performance"]), 1)
        self.assertEqual([field["key"] for field in report["content_fields"]], [
            "reach", "views", "reactions", "comments", "clicks",
        ])

    def test_png_render_is_authenticated_and_returns_private_png(self):
        preview = self.client.post(self.url, self.payload(), format="json")
        render_url = reverse("insights-report-png")
        with patch("apps.reports.views.render_report_png", return_value=b"png-bytes") as renderer:
            response = self.client.post(render_url, {
                "render_token": preview.data["data"]["render_token"],
                "html": '<html><body><article id="report-document">report</article></body></html>',
            }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response.content, b"png-bytes")
        renderer.assert_called_once()

        self.client.force_authenticate(user=None)
        denied = self.client.post(render_url, {}, format="json")
        self.assertEqual(denied.status_code, 401)

    def test_png_renderer_failure_returns_safe_503(self):
        preview = self.client.post(self.url, self.payload(), format="json")
        with patch(
            "apps.reports.views.render_report_png",
            side_effect=ReportRenderError("Authorization: Bearer render-token-secret"),
        ):
            response = self.client.post(reverse("insights-report-png"), {
                "render_token": preview.data["data"]["render_token"],
                "html": '<html><body><article id="report-document">report</article></body></html>',
            }, format="json")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["message"], "The report image could not be generated. Please try again.")
        self.assertNotIn("render-token-secret", str(response.data))

    def test_png_endpoint_renders_real_snapshot_values_at_high_density_dimensions(self):
        preview = self.client.post(self.url, self.payload(), format="json")
        report = preview.data["data"]["report"]
        content_names = "".join(
            f"<tr><td>{escape(row['caption'])}</td><td>{escape(str(row['metrics']['reach']['value']))}</td></tr>"
            for row in report["content_performance"]
        )
        html = f"""<!doctype html><html><head><style>
            body {{ margin: 0; }}
            #report-document {{ width: 1200px; height: 760px; padding: 24px; box-sizing: border-box; overflow: hidden; }}
            .chart {{ width: 300px; height: 80px; background: linear-gradient(#f6cf6f,#f6cf6f); }}
            </style></head><body><article id="report-document">
            <h1>{escape(report['organization']['name'])}</h1>
            <p>{escape(report['account']['name'])} · {escape(report['date_range']['since'])} – {escape(report['date_range']['until'])}</p>
            <div class="chart" aria-label="Daily Reach"></div>
            <table>{content_names}</table>
            </article></body></html>"""
        response = self.client.post(reverse("insights-report-png"), {
            "render_token": preview.data["data"]["render_token"],
            "html": html,
        }, format="json")

        self.assertEqual(response.status_code, 200)
        png = response.content
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(int.from_bytes(png[16:20], "big"), 2400)
        self.assertEqual(int.from_bytes(png[20:24], "big"), 1520)
        with Image.open(BytesIO(png)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (2400, 1520))
            self.assertEqual(image.width / image.height, 1200 / 760)
            image.verify()
        self.assertIn("Report Org", html)
        self.assertIn("report-ig", html)
        self.assertIn("Saved post 6", html)


class InsightsReportRendererTests(SimpleTestCase):
    def test_read_cgroup_memory_bytes_supports_v2(self):
        memory_files = (Path("/cgroup/memory.current"),)
        with patch("apps.reports.rendering._CGROUP_MEMORY_USAGE_FILES", memory_files):
            with patch("apps.reports.rendering.Path.read_text", return_value="12345\n"):
                self.assertEqual(_read_cgroup_memory_bytes(), 12345)

    def test_read_cgroup_memory_bytes_supports_v1_after_v2_file_is_unavailable(self):
        memory_files = (
            Path("/cgroup/memory.current"),
            Path("/cgroup/memory/memory.usage_in_bytes"),
        )
        with patch("apps.reports.rendering._CGROUP_MEMORY_USAGE_FILES", memory_files):
            with patch(
                "apps.reports.rendering.Path.read_text",
                side_effect=[FileNotFoundError, "67890\n"],
            ):
                self.assertEqual(_read_cgroup_memory_bytes(), 67890)

    def test_cgroup_memory_reader_returns_unavailable_when_metrics_cannot_be_read(self):
        memory_files = (
            Path("/cgroup/memory.current"),
            Path("/cgroup/memory/memory.usage_in_bytes"),
            Path("/cgroup/memory.usage_in_bytes"),
        )
        with patch("apps.reports.rendering._CGROUP_MEMORY_USAGE_FILES", memory_files):
            with patch("apps.reports.rendering.Path.read_text", side_effect=PermissionError):
                self.assertIsNone(_read_cgroup_memory_bytes())

    def test_cgroup_memory_logs_only_stage_bytes_or_unavailable_and_elapsed_time(self):
        for memory_bytes, expected_value in ((24680, "memory_bytes=24680"), (None, "memory_bytes=unavailable")):
            with self.subTest(memory_bytes=memory_bytes):
                with patch(
                    "apps.reports.rendering._read_cgroup_memory_bytes",
                    return_value=memory_bytes,
                ):
                    with self.assertLogs("apps.reports.rendering", level="INFO") as captured:
                        _log_cgroup_memory(stage="page_create", render_started_at=0)

                self.assertRegex(
                    captured.output[0],
                    rf"report_png_renderer_memory stage=page_create {expected_value} "
                    r"elapsed_ms=\d+ scope=cgroup_aggregate$",
                )

    def test_report_diagnostic_loggers_emit_info_and_error_to_console(self):
        logging_config = settings.LOGGING
        handler = logging_config["handlers"]["report_diagnostics_console"]

        self.assertEqual(handler["class"], "logging.StreamHandler")
        self.assertEqual(handler["level"], "INFO")
        self.assertIn("credential_redaction", handler["filters"])
        self.assertEqual(
            logging_config["loggers"]["apps.reports.rendering"]["handlers"],
            ["report_diagnostics_console"],
        )
        self.assertEqual(
            logging_config["loggers"]["apps.reports.rendering"]["level"],
            "INFO",
        )
        self.assertFalse(
            logging_config["loggers"]["apps.reports.rendering"]["propagate"]
        )

    @contextmanager
    def png_view_patches(self, renderer):
        from apps.reports.serializers import InsightsReportRenderSerializer

        serializer = Mock(spec=InsightsReportRenderSerializer)
        serializer.is_valid.return_value = True
        serializer.validated_data = {
            "render_token": "render-token",
            "html": '<html><body><article id="report-document">report</article></body></html>',
        }
        render_claim = {
            "organization_id": "ORG-TEST",
            "social_account_id": "account-id",
            "since": "2026-09-01",
            "until": "2026-09-07",
            "duration_days": 7,
        }
        account = SimpleNamespace(platform="instagram")
        with (
            patch(
                "apps.reports.views.InsightsReportRenderSerializer",
                return_value=serializer,
            ),
            patch(
                "apps.reports.views.validate_report_render_token",
                return_value=render_claim,
            ),
            patch(
                "apps.reports.views.get_selected_account",
                return_value=(None, account),
            ),
            patch("apps.reports.views.get_duration_slot_days", return_value=7),
            patch("apps.reports.views.render_report_png", side_effect=renderer) as render_mock,
        ):
            yield render_mock

    def call_png_view(self):
        from apps.reports.views import InsightsReportPngAPIView

        request = APIRequestFactory().post(
            "/api/reports/insights/png/",
            {},
            format="json",
        )
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
        return InsightsReportPngAPIView.as_view()(request)

    def call_preview_view(self):
        from apps.reports.views import InsightsReportPreviewAPIView

        serializer = Mock()
        serializer.is_valid.return_value = True
        serializer.validated_data = {
            "organization_id": "ORG-TEST",
            "social_account_id": "account-id",
            "platform": "instagram",
            "since": date(2026, 9, 1),
            "until": date(2026, 9, 7),
            "mode": "current",
            "meta_ads": [],
        }
        request = APIRequestFactory().post("/api/reports/insights/preview/", {}, format="json")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
        with (
            patch(
                "apps.reports.views.InsightsReportPreviewSerializer",
                return_value=serializer,
            ),
            patch(
                "apps.reports.views.get_selected_account",
                return_value=(None, SimpleNamespace(platform="instagram")),
            ),
            patch("apps.reports.views.build_insights_report_payload", return_value={"ok": True}),
        ):
            return InsightsReportPreviewAPIView.as_view()(request)

    def test_renderer_unavailable_returns_safe_api_error(self):
        from apps.reports.views import InsightsReportPngAPIView

        serializer = Mock()
        serializer.is_valid.return_value = True
        serializer.validated_data = {"render_token": "render-token", "html": "<html></html>"}
        render_claim = {
            "organization_id": "ORG-TEST",
            "social_account_id": "account-id",
            "since": "2026-09-01",
            "until": "2026-09-07",
            "duration_days": 7,
        }
        account = SimpleNamespace(platform="instagram")
        request = APIRequestFactory().post(
            "/api/reports/insights/png/",
            {},
            format="json",
        )
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        with (
            patch(
                "apps.reports.views.InsightsReportRenderSerializer",
                return_value=serializer,
            ),
            patch(
                "apps.reports.views.validate_report_render_token",
                return_value=render_claim,
            ),
            patch(
                "apps.reports.views.get_selected_account",
                return_value=(None, account),
            ),
            patch("apps.reports.views.get_duration_slot_days", return_value=7),
            patch(
                "apps.reports.views.render_report_png",
                side_effect=ReportRenderError("internal path /srv/app and renderer secret"),
            ),
        ):
            response = InsightsReportPngAPIView.as_view()(request)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data["errors"]["render"],
            "The report image renderer is unavailable.",
        )
        self.assertNotIn("/srv/app", str(response.data))
        self.assertNotIn("renderer secret", str(response.data))

    def test_png_success_response_contract_and_lock_release_after_success_and_failure(self):
        from apps.reports.rendering import ReportRenderError

        with self.png_view_patches(
            Mock(side_effect=[b"first-png", ReportRenderError("safe failure"), b"third-png"])
        ) as renderer, self.assertLogs("apps.reports.views", level="INFO") as captured:
            first = self.call_png_view()
            failed = self.call_png_view()
            third = self.call_png_view()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first["Content-Type"], "image/png")
        self.assertEqual(first["Cache-Control"], "private, no-store")
        self.assertEqual(first["X-Content-Type-Options"], "nosniff")
        self.assertEqual(first["Content-Disposition"], 'inline; filename="insights-report.png"')
        self.assertEqual(first.content, b"first-png")
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(
            failed.data,
            {
                "success": False,
                "message": "The report image could not be generated. Please try again.",
                "errors": {"render": "The report image renderer is unavailable."},
            },
        )
        self.assertEqual(third.status_code, 200)
        self.assertEqual(third.content, b"third-png")
        self.assertEqual(renderer.call_count, 3)
        output = "\n".join(captured.output)
        self.assertEqual(output.count("report_png_request_enter"), 3)
        self.assertEqual(output.count("report_png_render_invoke"), 3)
        self.assertNotIn("render-token", output)
        self.assertNotIn("report-document", output)

    def test_second_png_render_is_rejected_without_blocking_preview_request(self):
        render_started = Event()
        allow_render_to_finish = Event()
        first_response = []
        worker_errors = []

        def blocking_renderer(**kwargs):
            render_started.set()
            if not allow_render_to_finish.wait(timeout=5):
                raise TimeoutError("test renderer release timed out")
            return b"first-png"

        with self.png_view_patches(blocking_renderer) as renderer:
            def render_first_request():
                try:
                    first_response.append(self.call_png_view())
                except Exception as exc:  # surfaced in the test thread below
                    worker_errors.append(exc)

            render_thread = Thread(target=render_first_request, daemon=True)
            render_thread.start()
            try:
                self.assertTrue(render_started.wait(timeout=3))
                second_response = self.call_png_view()
                preview_response = self.call_preview_view()
            finally:
                allow_render_to_finish.set()
                render_thread.join(timeout=6)

        self.assertFalse(render_thread.is_alive())
        self.assertEqual(worker_errors, [])
        self.assertEqual(len(first_response), 1)
        self.assertEqual(first_response[0].status_code, 200)
        self.assertEqual(second_response.status_code, 503)
        self.assertEqual(preview_response.status_code, 200)
        renderer.assert_called_once()

    def test_rendered_png_has_expected_dimensions(self):
        html = """<!doctype html><html><head><style>
            html, body { margin: 0; }
            #report-document { width: 1200px; height: 760px; overflow: hidden; }
            </style></head><body><article id="report-document">report</article></body></html>"""

        with self.assertLogs("apps.reports.rendering", level="INFO") as captured:
            png = render_report_png(html=html)

        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        with Image.open(BytesIO(png)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (2400, 1520))
            image.verify()
        output = "\n".join(captured.output)
        self.assertIn("report_png_renderer_start", output)
        self.assertIn("stage=browser_launch duration_ms=", output)
        self.assertIn("scope=cgroup_aggregate", output)
        for stage in ("browser_launch", "page_create"):
            self.assertRegex(
                output,
                rf"report_png_renderer_memory stage={stage} memory_bytes=(?:\d+|unavailable) elapsed_ms=\d+",
            )
        for stage in (
            "browser_context_create",
            "network_route_registration",
            "page_create",
            "page_set_content",
            "layout_readiness",
            "png_capture",
            "browser_cleanup",
        ):
            stage_logs = [line for line in output.splitlines() if f"stage={stage} " in line]
            self.assertTrue(any(
                "elapsed_ms=" in line and "outcome=starting" in line
                for line in stage_logs
            ))
            self.assertTrue(any(
                "duration_ms=" in line and "outcome=success" in line
                for line in stage_logs
            ))
        self.assertIn("stage=png_capture duration_ms=", output)
        self.assertIn("stage=browser_cleanup duration_ms=", output)
        self.assertIn(f"outcome=success duration_ms=", output)
        self.assertIn(f"png_bytes={len(png)}", output)
        self.assertNotIn("<article", output)

    def test_renderer_uses_compact_viewport_and_device_scale(self):
        patcher = patch("playwright.sync_api.sync_playwright")
        manager = patcher.start()
        self.addCleanup(patcher.stop)
        playwright = manager.return_value.__enter__.return_value
        playwright.chromium.executable_path = sys.executable
        page = playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value
        page.locator.return_value.bounding_box.return_value = {
            "width": 1200,
            "height": 760,
            "x": 0,
            "y": 0,
        }
        page.locator.return_value.screenshot.return_value = b"\x89PNG\r\n\x1a\nmock"

        self.assertEqual(REPORT_VIEWPORT, {"width": 1200, "height": 760})
        png = render_report_png(html="<html><body><article id='report-document'></article></body></html>")

        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        playwright.chromium.launch.return_value.new_context.assert_called_once_with(
            viewport={"width": 1200, "height": 760},
            device_scale_factor=2,
            java_script_enabled=False,
            service_workers="block",
            accept_downloads=False,
        )

    def test_missing_playwright_chromium_has_actionable_error_and_safe_log(self):
        patcher = patch("playwright.sync_api.sync_playwright")
        manager = patcher.start()
        self.addCleanup(patcher.stop)
        playwright = manager.return_value.__enter__.return_value
        playwright.chromium.executable_path = str(Path(sys.executable).parent / "missing-playwright-browser.exe")

        with self.assertLogs("apps.reports.rendering", level="ERROR") as captured:
            with self.assertRaisesRegex(ReportRenderError, "python -m playwright install chromium"):
                render_report_png(html="<html></html>")

        output = "\n".join(captured.output)
        self.assertIn("stage=browser_discovery", output)
        self.assertIn("browser_launch_status=missing", output)
        self.assertNotIn("missing-playwright-browser.exe", output)

    def test_browser_launch_failure_logs_no_credentials(self):
        patcher = patch("playwright.sync_api.sync_playwright")
        manager = patcher.start()
        self.addCleanup(patcher.stop)
        playwright = manager.return_value.__enter__.return_value
        playwright.chromium.executable_path = sys.executable
        playwright.chromium.launch.side_effect = RuntimeError(
            "Authorization: Bearer render-token-secret"
        )

        with self.assertLogs("apps.reports.rendering", level="INFO") as captured:
            with self.assertRaises(ReportRenderError):
                render_report_png(html="<html></html>")

        output = "\n".join(captured.output)
        self.assertIn("stage=browser_launch", output)
        self.assertIn("stage=browser_launch_start", output)
        self.assertIn("elapsed_ms=", output)
        self.assertIn("outcome=starting", output)
        self.assertIn("exception_type=RuntimeError", output)
        self.assertNotIn("render-token-secret", output)

    def test_page_content_failure_logs_stage_and_closes_browser_without_report_data(self):
        patcher = patch("playwright.sync_api.sync_playwright")
        manager = patcher.start()
        self.addCleanup(patcher.stop)
        playwright = manager.return_value.__enter__.return_value
        playwright.chromium.executable_path = sys.executable
        browser = playwright.chromium.launch.return_value
        page = browser.new_context.return_value.new_page.return_value
        page.set_content.side_effect = RuntimeError("page content failed")

        html = "<html><body>private-caption-marker</body></html>"
        with self.assertLogs("apps.reports.rendering", level="INFO") as captured:
            with self.assertRaises(ReportRenderError):
                render_report_png(html=html)

        output = "\n".join(captured.output)
        self.assertIn("stage=page_set_content elapsed_ms=", output)
        self.assertIn("outcome=starting", output)
        self.assertIn("outcome=failure stage=page_set_content", output)
        self.assertIn("stage=browser_cleanup elapsed_ms=", output)
        self.assertIn("stage=browser_cleanup duration_ms=", output)
        self.assertIn("outcome=success", output)
        self.assertNotIn("private-caption-marker", output)
        browser.close.assert_called_once_with()

    def test_browser_context_substage_failures_log_and_close_browser(self):
        html = "<html><body>private-caption-marker</body></html>"
        failure_targets = (
            ("browser_context_create", "new_context"),
            ("network_route_registration", "route"),
            ("page_create", "new_page"),
        )

        for stage, method_name in failure_targets:
            with self.subTest(stage=stage):
                patcher = patch("playwright.sync_api.sync_playwright")
                manager = patcher.start()
                self.addCleanup(patcher.stop)
                playwright = manager.return_value.__enter__.return_value
                playwright.chromium.executable_path = sys.executable
                browser = playwright.chromium.launch.return_value
                context = browser.new_context.return_value
                target = browser if method_name == "new_context" else context
                getattr(target, method_name).side_effect = RuntimeError("context step failed")

                with self.assertLogs("apps.reports.rendering", level="INFO") as captured:
                    with self.assertRaises(ReportRenderError):
                        render_report_png(html=html)

                output = "\n".join(captured.output)
                self.assertIn(f"stage={stage} elapsed_ms=", output)
                self.assertIn(f"outcome=failure stage={stage}", output)
                self.assertIn("stage=browser_cleanup elapsed_ms=", output)
                self.assertIn("stage=browser_cleanup duration_ms=", output)
                self.assertNotIn("private-caption-marker", output)
                browser.close.assert_called_once_with()
