from datetime import date, datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path
import sys
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

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

from .rendering import ReportRenderError, render_report_png


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

        with self.assertLogs("apps.reports.rendering", level="ERROR") as captured:
            with self.assertRaises(ReportRenderError):
                render_report_png(html="<html></html>")

        output = "\n".join(captured.output)
        self.assertIn("stage=browser_launch", output)
        self.assertIn("exception_type=RuntimeError", output)
        self.assertNotIn("render-token-secret", output)
