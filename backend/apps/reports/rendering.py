"""Deterministic, network-isolated PNG rendering for report markup."""

import logging
import re
import time
from pathlib import Path

REPORT_VIEWPORT = {"width": 1600, "height": 1000}
REPORT_IMAGE_SIZE = {"width": 1200, "height": 760}
_CGROUP_MEMORY_USAGE_FILES = (
    Path("/sys/fs/cgroup/memory.current"),
    Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"),
    Path("/sys/fs/cgroup/memory.usage_in_bytes"),
)

logger = logging.getLogger(__name__)


class ReportRenderError(Exception):
    """The report image could not be rendered by the configured browser."""


def _read_cgroup_memory_bytes():
    """Return current cgroup memory usage for common Linux v1/v2 mounts."""
    for memory_file in _CGROUP_MEMORY_USAGE_FILES:
        try:
            memory_bytes = int(memory_file.read_text(encoding="ascii").strip())
        except (OSError, UnicodeError, ValueError):
            continue
        if memory_bytes >= 0:
            return memory_bytes
    return None


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


def _duration_ms(started_at):
    return max(0, int((time.monotonic() - started_at) * 1000))


def _log_renderer_stage(*, stage, started_at):
    logger.info(
        "report_png_renderer_stage stage=%s duration_ms=%s outcome=success",
        stage,
        _duration_ms(started_at),
    )


def _log_renderer_stage_start(*, stage, render_started_at):
    logger.info(
        "report_png_renderer_stage stage=%s elapsed_ms=%s outcome=starting",
        stage,
        _duration_ms(render_started_at),
    )


def _log_cgroup_memory(*, stage, render_started_at):
    memory_bytes = _read_cgroup_memory_bytes()
    logger.info(
        "report_png_renderer_memory stage=%s memory_bytes=%s elapsed_ms=%s",
        stage,
        memory_bytes if memory_bytes is not None else "unavailable",
        _duration_ms(render_started_at),
    )


def _log_renderer_failure(
    *, stage, exception, browser_launch_status, stage_started_at, render_started_at,
):
    logger.error(
        "report_png_renderer_end outcome=failure stage=%s stage_duration_ms=%s "
        "duration_ms=%s exception_type=%s message=%s browser_launch_status=%s",
        stage,
        _duration_ms(stage_started_at),
        _duration_ms(render_started_at),
        type(exception).__name__,
        _safe_exception_message(exception),
        browser_launch_status,
    )


def render_report_png(*, html):
    render_started_at = time.monotonic()
    logger.info("report_png_renderer_start")

    stage = "playwright_import"
    stage_started_at = time.monotonic()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        _log_renderer_failure(
            stage="playwright_import",
            exception=exc,
            browser_launch_status="not_attempted",
            stage_started_at=stage_started_at,
            render_started_at=render_started_at,
        )
        raise ReportRenderError(
            "The Playwright package is missing from the backend environment. Install backend requirements."
        ) from exc
    _log_renderer_stage(stage="playwright_import", started_at=stage_started_at)

    stage = "playwright_driver_start"
    stage_started_at = time.monotonic()
    browser_launch_status = "not_attempted"
    png = None
    try:
        with sync_playwright() as playwright:
            _log_renderer_stage(stage="playwright_driver_start", started_at=stage_started_at)

            stage = "browser_discovery"
            stage_started_at = time.monotonic()
            executable_path = Path(playwright.chromium.executable_path)
            if not executable_path.is_file():
                error = FileNotFoundError("Playwright-managed Chromium executable is not installed.")
                _log_renderer_failure(
                    stage=stage,
                    exception=error,
                    browser_launch_status="missing",
                    stage_started_at=stage_started_at,
                    render_started_at=render_started_at,
                )
                raise ReportRenderError(
                    "Playwright Chromium is missing in the backend environment. "
                    "Run `python -m playwright install chromium` with the same Python environment as Django."
                ) from error
            _log_renderer_stage(stage=stage, started_at=stage_started_at)

            stage = "browser_launch"
            stage_started_at = time.monotonic()
            browser_launch_status = "starting"
            try:
                logger.info(
                    "report_png_renderer_stage stage=browser_launch_start elapsed_ms=%s outcome=starting",
                    _duration_ms(render_started_at),
                )
                _log_cgroup_memory(stage=stage, render_started_at=render_started_at)
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
                    stage_started_at=stage_started_at,
                    render_started_at=render_started_at,
                )
                raise ReportRenderError(
                    "Playwright Chromium could not start. Verify its installation and the server's OS dependencies."
                ) from exc

            browser_launch_status = "started"
            _log_renderer_stage(stage=stage, started_at=stage_started_at)
            try:
                stage = "browser_context_create"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
                context = browser.new_context(
                    viewport=REPORT_VIEWPORT,
                    device_scale_factor=2,
                    java_script_enabled=False,
                    service_workers="block",
                    accept_downloads=False,
                )
                _log_renderer_stage(stage=stage, started_at=stage_started_at)

                stage = "network_route_registration"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
                context.route("**/*", lambda route: route.abort())

                _log_renderer_stage(stage=stage, started_at=stage_started_at)

                stage = "page_create"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
                _log_cgroup_memory(stage=stage, render_started_at=render_started_at)
                page = context.new_page()
                _log_renderer_stage(stage=stage, started_at=stage_started_at)

                stage = "page_set_content"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
                page.set_content(html, wait_until="load", timeout=15_000)
                _log_renderer_stage(stage=stage, started_at=stage_started_at)

                stage = "layout_readiness"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
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
                        stage_started_at=stage_started_at,
                        render_started_at=render_started_at,
                    )
                    raise ReportRenderError("The report layout is outside the supported dimensions.") from error
                _log_renderer_stage(stage=stage, started_at=stage_started_at)

                stage = "png_capture"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
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
                        stage_started_at=stage_started_at,
                        render_started_at=render_started_at,
                    )
                    raise ReportRenderError("Chromium returned an invalid report image.") from error
                _log_renderer_stage(stage=stage, started_at=stage_started_at)
            except ReportRenderError:
                raise
            except Exception as exc:
                _log_renderer_failure(
                    stage=stage,
                    exception=exc,
                    browser_launch_status=browser_launch_status,
                    stage_started_at=stage_started_at,
                    render_started_at=render_started_at,
                )
                raise ReportRenderError("Chromium could not render the report image.") from exc
            finally:
                stage = "browser_cleanup"
                stage_started_at = time.monotonic()
                _log_renderer_stage_start(stage=stage, render_started_at=render_started_at)
                browser.close()
                _log_renderer_stage(stage=stage, started_at=stage_started_at)
    except ReportRenderError:
        raise
    except Exception as exc:
        _log_renderer_failure(
            stage=stage,
            exception=exc,
            browser_launch_status=browser_launch_status,
            stage_started_at=stage_started_at,
            render_started_at=render_started_at,
        )
        raise ReportRenderError("The Playwright renderer could not initialize.") from exc

    logger.info(
        "report_png_renderer_end outcome=success duration_ms=%s png_bytes=%s",
        _duration_ms(render_started_at),
        len(png),
    )
    return png
