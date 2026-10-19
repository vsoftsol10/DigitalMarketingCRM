"""Safe Celery task lifecycle diagnostics for correlating work with web requests."""

import logging
import os
import re
import threading
import time
from datetime import datetime, timezone

from celery.signals import task_postrun, task_prerun

from .process_diagnostics import (
    log_current_process_memory,
    log_process_memory_snapshot,
)

logger = logging.getLogger("config.process_diagnostics")

_TASK_STARTS = {}
_TASK_STARTS_LOCK = threading.Lock()
_TASK_STARTS_LIMIT = 256
_SAFE_TASK_NAME = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_SAFE_TASK_STATE = re.compile(r"^[A-Za-z_]{1,32}$")


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _task_name(sender, task):
    name = getattr(sender, "name", None) or getattr(task, "name", None)
    if isinstance(name, str) and _SAFE_TASK_NAME.fullmatch(name):
        return name
    return "unknown"


def _task_key(task_id):
    return os.getpid(), str(task_id or "unknown")


def task_prerun_diagnostic(*, sender=None, task_id=None, task=None, **_kwargs):
    """Emit one safe start marker per Celery task execution process."""
    started_at = time.monotonic()
    key = _task_key(task_id)
    try:
        with _TASK_STARTS_LOCK:
            if len(_TASK_STARTS) >= _TASK_STARTS_LIMIT and key not in _TASK_STARTS:
                _TASK_STARTS.pop(next(iter(_TASK_STARTS)))
            _TASK_STARTS[key] = started_at
        logger.info(
            "celery_task_diagnostic event=start task_name=%s timestamp=%s pid=%s ppid=%s",
            _task_name(sender, task),
            _timestamp(),
            os.getpid(),
            os.getppid(),
        )
        log_current_process_memory(
            event="start",
            stage="celery_task",
            category="celery_task_process",
            log=logger,
        )
        log_process_memory_snapshot(stage="celery_task_start", log=logger)
    except Exception:
        # Diagnostics are never allowed to change Celery task execution.
        pass


def task_postrun_diagnostic(*, sender=None, task_id=None, task=None, state=None, **_kwargs):
    """Emit one safe completion marker without logging task arguments/results."""
    key = _task_key(task_id)
    try:
        with _TASK_STARTS_LOCK:
            started_at = _TASK_STARTS.pop(key, None)
        duration_ms = (
            max(0, int((time.monotonic() - started_at) * 1000))
            if started_at is not None
            else "unavailable"
        )
        safe_state = state if isinstance(state, str) and _SAFE_TASK_STATE.fullmatch(state) else "unknown"
        logger.info(
            "celery_task_diagnostic event=end task_name=%s timestamp=%s duration_ms=%s "
            "state=%s pid=%s ppid=%s",
            _task_name(sender, task),
            _timestamp(),
            duration_ms,
            safe_state,
            os.getpid(),
            os.getppid(),
        )
        log_current_process_memory(
            event="end",
            stage="celery_task",
            category="celery_task_process",
            log=logger,
        )
        log_process_memory_snapshot(stage="celery_task_end", log=logger)
    except Exception:
        # Diagnostics are best-effort and must not mask task outcomes.
        pass


def connect_task_diagnostics():
    """Register guarded receivers once, even if Celery configuration reloads."""
    task_prerun.connect(
        task_prerun_diagnostic,
        weak=False,
        dispatch_uid="digital_marketing_process_diagnostics_task_prerun",
    )
    task_postrun.connect(
        task_postrun_diagnostic,
        weak=False,
        dispatch_uid="digital_marketing_process_diagnostics_task_postrun",
    )
