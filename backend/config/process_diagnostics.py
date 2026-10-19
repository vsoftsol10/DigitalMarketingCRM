"""Best-effort, low-volume process memory diagnostics for Linux deployments."""

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("config.process_diagnostics")

_PROCESS_LIMIT = 64
_PROCESS_SCAN_LIMIT = 256
_CGROUP_MEMORY_FILES = (
    Path("/sys/fs/cgroup/memory.current"),
    Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"),
    Path("/sys/fs/cgroup/memory.usage_in_bytes"),
)
_SAFE_PROCESS_NAME = re.compile(r"[^A-Za-z0-9_.:-]")


@dataclass(frozen=True)
class ProcessMemory:
    pid: int
    ppid: int | None
    process_name: str
    category: str
    rss_bytes: int | None
    pss_bytes: int | None


def _process_category(process_name, command_line):
    identity = f"{process_name} {command_line}".lower()
    if "chromium" in identity or "chrome" in identity:
        return "chromium"
    if "playwright" in identity or "run-driver" in identity:
        return "playwright_driver"
    if "gunicorn" in identity:
        if "master" in identity or "arbiter" in identity:
            return "gunicorn_master"
        return "gunicorn_worker"
    if "celery" in identity:
        if "beat" in identity:
            return "celery_beat"
        if any(marker in identity for marker in ("forkpoolworker", "poolworker", "celeryd:")):
            return "celery_worker_child"
        if "worker" in identity:
            return "celery_worker_parent"
    return None


def _read_status_fields(status_text):
    fields = {}
    for line in status_text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key in {"Name", "PPid", "VmRSS"}:
            fields[key] = value.strip()
    return fields


def read_process_memory(pid, *, proc_root="/proc", category=None):
    """Read one process's RSS and optional PSS; return None when it exits/unavailable."""
    process_dir = Path(proc_root) / str(pid)
    try:
        status_fields = _read_status_fields(
            (process_dir / "status").read_text(encoding="ascii", errors="replace")
        )
        process_name = status_fields.get("Name", "unknown")
        try:
            command_line = (process_dir / "cmdline").read_bytes()[:8192].replace(
                b"\0", b" "
            ).decode("utf-8", errors="ignore")
        except OSError:
            command_line = ""

        process_category = category or _process_category(process_name, command_line)
        if process_category is None:
            return None

        ppid = int(status_fields["PPid"]) if status_fields.get("PPid", "").isdigit() else None
        rss_kib = None
        rss_value = status_fields.get("VmRSS", "").split()
        if len(rss_value) >= 2 and rss_value[0].isdigit() and rss_value[1] == "kB":
            rss_kib = int(rss_value[0])

        pss_kib = None
        try:
            for line in (process_dir / "smaps_rollup").read_text(
                encoding="ascii", errors="replace"
            ).splitlines():
                key, separator, value = line.partition(":")
                if key == "Pss" and separator:
                    pss_value = value.strip().split()
                    if len(pss_value) >= 2 and pss_value[0].isdigit() and pss_value[1] == "kB":
                        pss_kib = int(pss_value[0])
                    break
        except OSError:
            pass

        safe_name = _SAFE_PROCESS_NAME.sub("_", process_name)[:32] or "unknown"
        return ProcessMemory(
            pid=int(pid),
            ppid=ppid,
            process_name=safe_name,
            category=process_category,
            rss_bytes=rss_kib * 1024 if rss_kib is not None else None,
            pss_bytes=pss_kib * 1024 if pss_kib is not None else None,
        )
    except (OSError, UnicodeError, ValueError):
        return None


def collect_process_memory(*, proc_root="/proc", limit=_PROCESS_LIMIT):
    """Collect bounded memory data for known service/browser processes only."""
    snapshots = []
    truncated = False
    scanned = 0
    try:
        with os.scandir(proc_root) as entries:
            for entry in entries:
                if not entry.name.isdecimal():
                    continue
                if scanned >= _PROCESS_SCAN_LIMIT:
                    truncated = True
                    break
                scanned += 1
                snapshot = read_process_memory(entry.name, proc_root=proc_root)
                if snapshot is None:
                    continue
                if len(snapshots) >= limit:
                    truncated = True
                    break
                snapshots.append(snapshot)
    except OSError:
        return (), False
    return tuple(snapshots), truncated


def read_cgroup_memory_bytes():
    """Return aggregate cgroup usage where a supported Linux file is mounted."""
    for memory_file in _CGROUP_MEMORY_FILES:
        try:
            memory_bytes = int(memory_file.read_text(encoding="ascii").strip())
        except (OSError, UnicodeError, ValueError):
            continue
        if memory_bytes >= 0:
            return memory_bytes
    return None


def _memory_field(value):
    return value if value is not None else "unavailable"


def log_process_memory_snapshot(*, stage, log=logger, proc_root="/proc"):
    """Log a single bounded snapshot without allowing diagnostics to break work."""
    try:
        snapshots, truncated = collect_process_memory(proc_root=proc_root)
        log.info(
            "process_memory_snapshot stage=%s outcome=%s process_count=%s truncated=%s",
            stage,
            "available" if snapshots else "unavailable",
            len(snapshots),
            str(truncated).lower(),
        )
        for process in snapshots:
            log.info(
                "process_memory stage=%s pid=%s ppid=%s process_name=%s "
                "process_category=%s rss_bytes=%s pss_bytes=%s",
                stage,
                process.pid,
                process.ppid if process.ppid is not None else "unavailable",
                process.process_name,
                process.category,
                _memory_field(process.rss_bytes),
                _memory_field(process.pss_bytes),
            )
    except Exception:
        # This must remain best-effort, including when procfs is restricted.
        try:
            log.info(
                "process_memory_snapshot stage=%s outcome=unavailable process_count=0 truncated=false",
                stage,
            )
        except Exception:
            pass


def log_current_process_memory(*, event, stage, category, log=logger):
    """Log the current task process, plus aggregate cgroup usage if available."""
    try:
        process = read_process_memory(os.getpid(), category=category)
        ppid = process.ppid if process and process.ppid is not None else os.getppid()
        log.info(
            "process_memory event=%s stage=%s pid=%s ppid=%s process_name=%s "
            "process_category=%s rss_bytes=%s pss_bytes=%s cgroup_memory_bytes=%s",
            event,
            stage,
            os.getpid(),
            ppid,
            process.process_name if process else "unavailable",
            category,
            _memory_field(process.rss_bytes if process else None),
            _memory_field(process.pss_bytes if process else None),
            _memory_field(read_cgroup_memory_bytes()),
        )
    except Exception:
        try:
            log.info(
                "process_memory event=%s stage=%s pid=%s ppid=%s process_name=unavailable "
                "process_category=%s rss_bytes=unavailable pss_bytes=unavailable "
                "cgroup_memory_bytes=unavailable",
                event,
                stage,
                os.getpid(),
                os.getppid(),
                category,
            )
        except Exception:
            pass
