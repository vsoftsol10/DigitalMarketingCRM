"""Deterministic, network-isolated PNG rendering for report markup."""

import logging
import re
from pathlib import Path

REPORT_VIEWPORT = {"width": 1600, "height": 1000}
REPORT_IMAGE_SIZE = {"width": 1200, "height": 760}

logger = logging.getLogger(__name__)


class ReportRenderError(Exception):
    """The report image could not be rendered by the configured browser."""


def _safe_exception_message(exception):
    """Keep useful exception context while excluding credentials and local paths."""
    message = str(exception).splitlines()[0][:300].strip()
    if not message:
        return "No exception message was provided."

    if re.search(
        r"(?i)\b(authorization|cookie|set-cookie|access[_ -]?token|refresh[_ -]?token|token|password|secret)\b",
        message,
    ):
        return "Sensitive renderer error details were suppressed."
    message = re.sub(r"(?i)\b[A-Z]:\\[^\"'<>]+", "<local path>", message)
    message = re.sub(r"(?<!:)\/(?:[^\s\"'<>]+)", "<local path>", message)
    return message


def _log_renderer_failure(*, stage, exception, browser_launch_status):
    logger.error(
        "report_png_renderer_failure stage=%s exception_type=%s message=%s browser_launch_status=%s",
        stage,
        type(exception).__name__,
        _safe_exception_message(exception),
        browser_launch_status,
    )


def render_report_png(*, html):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        _log_renderer_failure(
            stage="playwright_import",
            exception=exc,
            browser_launch_status="not_attempted",
        )
        raise ReportRenderError(
            "The Playwright package is missing from the backend environment. Install backend requirements."
        ) from exc

    stage = "playwright_driver_start"
    browser_launch_status = "not_attempted"
    try:
        with sync_playwright() as playwright:
            stage = "browser_discovery"
            executable_path = Path(playwright.chromium.executable_path)
            if not executable_path.is_file():
                error = FileNotFoundError("Playwright-managed Chromium executable is not installed.")
                _log_renderer_failure(
                    stage=stage,
                    exception=error,
                    browser_launch_status="missing",
                )
                raise ReportRenderError(
                    "Playwright Chromium is missing in the backend environment. "
                    "Run `python -m playwright install chromium` with the same Python environment as Django."
                ) from error

            stage = "browser_launch"
            browser_launch_status = "starting"
            try:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=["--no-sandbox"],
                )
            except Exception as exc:
                browser_launch_status = "failed"
                _log_renderer_failure(
                    stage=stage,
                    exception=exc,
                    browser_launch_status=browser_launch_status,
                )
                raise ReportRenderError(
                    "Playwright Chromium could not start. Verify its installation and the server's OS dependencies."
                ) from exc

            browser_launch_status = "started"
            try:
                stage = "browser_context"
                context = browser.new_context(
                    viewport=REPORT_VIEWPORT,
                    device_scale_factor=2,
                    java_script_enabled=False,
                    service_workers="block",
                    accept_downloads=False,
                )
                context.route("**/*", lambda route: route.abort())
                page = context.new_page()

                stage = "report_layout"
                page.set_content(html, wait_until="load", timeout=15_000)
                report = page.locator("#report-document")
                report.wait_for(state="visible", timeout=5_000)
                bounds = report.bounding_box()
                if (
                    bounds is None
                    or round(bounds["width"]) != REPORT_IMAGE_SIZE["width"]
                    or round(bounds["height"]) != REPORT_IMAGE_SIZE["height"]
                ):
                    error = ValueError("Report document dimensions are outside the supported size.")
                    _log_renderer_failure(
                        stage=stage,
                        exception=error,
                        browser_launch_status=browser_launch_status,
                    )
                    raise ReportRenderError("The report layout is outside the supported dimensions.") from error

                stage = "png_capture"
                png = report.screenshot(
                    type="png",
                    animations="disabled",
                    caret="hide",
                    scale="device",
                )
                if not isinstance(png, bytes) or not png.startswith(b"\x89PNG\r\n\x1a\n"):
                    error = ValueError("Chromium returned an invalid PNG image.")
                    _log_renderer_failure(
                        stage=stage,
                        exception=error,
                        browser_launch_status=browser_launch_status,
                    )
                    raise ReportRenderError("Chromium returned an invalid report image.") from error
                return png
            except ReportRenderError:
                raise
            except Exception as exc:
                _log_renderer_failure(
                    stage=stage,
                    exception=exc,
                    browser_launch_status=browser_launch_status,
                )
                raise ReportRenderError("Chromium could not render the report image.") from exc
            finally:
                browser.close()
    except ReportRenderError:
        raise
    except Exception as exc:
        _log_renderer_failure(
            stage=stage,
            exception=exc,
            browser_launch_status=browser_launch_status,
        )
        raise ReportRenderError("The Playwright renderer could not initialize.") from exc
