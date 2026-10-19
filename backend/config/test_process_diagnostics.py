from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from . import celery_diagnostics, process_diagnostics


class ProcessMemoryDiagnosticsTests(SimpleTestCase):
    @staticmethod
    def add_process(root, pid, *, name, ppid, rss_kib, pss_kib, command):
        process_dir = Path(root) / str(pid)
        process_dir.mkdir()
        (process_dir / "status").write_text(
            f"Name:\t{name}\nPPid:\t{ppid}\nVmRSS:\t{rss_kib} kB\n",
            encoding="ascii",
        )
        (process_dir / "cmdline").write_bytes(command.encode("utf-8"))
        if pss_kib is not None:
            (process_dir / "smaps_rollup").write_text(
                f"Rss: {rss_kib} kB\nPss: {pss_kib} kB\n",
                encoding="ascii",
            )

    def test_collects_only_known_process_categories_and_optional_pss(self):
        with TemporaryDirectory() as proc_root:
            self.add_process(
                proc_root,
                100,
                name="gunicorn",
                ppid=1,
                rss_kib=4096,
                pss_kib=3000,
                command="gunicorn: master [config.wsgi:application]",
            )
            self.add_process(
                proc_root,
                101,
                name="node",
                ppid=100,
                rss_kib=2048,
                pss_kib=None,
                command="node playwright/driver/package/cli.js run-driver --token=private",
            )
            self.add_process(
                proc_root,
                102,
                name="chrome",
                ppid=100,
                rss_kib=8192,
                pss_kib=7000,
                command="chromium --user-data-dir=/tmp/private-profile",
            )
            self.add_process(
                proc_root,
                103,
                name="python",
                ppid=1,
                rss_kib=1024,
                pss_kib=900,
                command="celery -A config worker --concurrency=1",
            )
            self.add_process(
                proc_root,
                104,
                name="python",
                ppid=103,
                rss_kib=1024,
                pss_kib=900,
                command="celeryd: celery@worker ForkPoolWorker-1",
            )
            self.add_process(
                proc_root,
                105,
                name="python",
                ppid=1,
                rss_kib=768,
                pss_kib=640,
                command="celery -A config beat -l info",
            )
            self.add_process(
                proc_root,
                106,
                name="gunicorn",
                ppid=100,
                rss_kib=3072,
                pss_kib=2500,
                command="gunicorn: worker [config.wsgi:application]",
            )

            snapshots, truncated = process_diagnostics.collect_process_memory(
                proc_root=proc_root,
            )

        self.assertFalse(truncated)
        by_pid = {snapshot.pid: snapshot for snapshot in snapshots}
        self.assertEqual(
            {snapshot.category for snapshot in snapshots},
            {
                "gunicorn_master",
                "gunicorn_worker",
                "playwright_driver",
                "chromium",
                "celery_beat",
                "celery_worker_parent",
                "celery_worker_child",
            },
        )
        self.assertEqual(by_pid[100].ppid, 1)
        self.assertEqual(by_pid[100].rss_bytes, 4096 * 1024)
        self.assertEqual(by_pid[100].pss_bytes, 3000 * 1024)
        self.assertIsNone(by_pid[101].pss_bytes)

    def test_process_snapshot_logs_categories_without_command_arguments(self):
        with TemporaryDirectory() as proc_root:
            self.add_process(
                proc_root,
                222,
                name="chrome",
                ppid=2,
                rss_kib=512,
                pss_kib=256,
                command="chromium --token=do-not-log",
            )
            with self.assertLogs("config.process_diagnostics", level="INFO") as captured:
                process_diagnostics.log_process_memory_snapshot(
                    stage="page_create",
                    proc_root=proc_root,
                )

        output = "\n".join(captured.output)
        self.assertIn("stage=page_create pid=222 ppid=2", output)
        self.assertIn("process_category=chromium", output)
        self.assertIn("rss_bytes=524288 pss_bytes=262144", output)
        self.assertNotIn("do-not-log", output)

    def test_unavailable_procfs_is_safe(self):
        missing_root = Path("missing-test-proc-root")
        self.assertIsNone(
            process_diagnostics.read_process_memory(123, proc_root=missing_root)
        )
        self.assertEqual(
            process_diagnostics.collect_process_memory(proc_root=missing_root),
            ((), False),
        )
        with self.assertLogs("config.process_diagnostics", level="INFO") as captured:
            process_diagnostics.log_process_memory_snapshot(
                stage="browser_launch",
                proc_root=missing_root,
            )
        self.assertIn("outcome=unavailable process_count=0", "\n".join(captured.output))

    def test_celery_task_markers_include_safe_name_pid_duration_and_memory(self):
        task = SimpleNamespace(name="apps.posts.tasks.dispatch_due_posts_task")
        with (
            patch.object(celery_diagnostics, "log_current_process_memory") as memory_log,
            patch.object(celery_diagnostics, "log_process_memory_snapshot") as snapshot_log,
            self.assertLogs("config.process_diagnostics", level="INFO") as captured,
        ):
            celery_diagnostics.task_prerun_diagnostic(
                sender=task,
                task_id="sensitive-task-id",
                task=task,
                args=("private-argument",),
                kwargs={"token": "private-token"},
            )
            celery_diagnostics.task_postrun_diagnostic(
                sender=task,
                task_id="sensitive-task-id",
                task=task,
                state="SUCCESS",
                retval={"private": "result"},
            )

        output = "\n".join(captured.output)
        self.assertIn("event=start task_name=apps.posts.tasks.dispatch_due_posts_task", output)
        self.assertIn("event=end task_name=apps.posts.tasks.dispatch_due_posts_task", output)
        self.assertIn("timestamp=", output)
        self.assertIn("pid=", output)
        self.assertIn("ppid=", output)
        self.assertIn("duration_ms=", output)
        self.assertIn("state=SUCCESS", output)
        self.assertNotIn("sensitive-task-id", output)
        self.assertNotIn("private-argument", output)
        self.assertNotIn("private-token", output)
        self.assertNotIn("private-result", output)
        self.assertEqual(memory_log.call_count, 2)
        self.assertEqual(
            [call.kwargs for call in snapshot_log.call_args_list],
            [
                {"stage": "celery_task_start", "log": celery_diagnostics.logger},
                {"stage": "celery_task_end", "log": celery_diagnostics.logger},
            ],
        )

    def test_process_snapshot_failures_do_not_interrupt_celery_signals(self):
        task = SimpleNamespace(name="apps.posts.tasks.dispatch_due_posts_task")
        with (
            patch.object(celery_diagnostics, "log_current_process_memory"),
            patch.object(
                celery_diagnostics,
                "log_process_memory_snapshot",
                side_effect=RuntimeError("procfs unavailable"),
            ),
            self.assertLogs("config.process_diagnostics", level="INFO") as captured,
        ):
            celery_diagnostics.task_prerun_diagnostic(
                sender=task,
                task_id="snapshot-failure-test",
                task=task,
            )
            celery_diagnostics.task_postrun_diagnostic(
                sender=task,
                task_id="snapshot-failure-test",
                task=task,
                state="SUCCESS",
            )

        output = "\n".join(captured.output)
        self.assertIn("event=start task_name=apps.posts.tasks.dispatch_due_posts_task", output)
        self.assertIn("event=end task_name=apps.posts.tasks.dispatch_due_posts_task", output)

    def test_untrusted_task_names_are_suppressed(self):
        task = SimpleNamespace(name="unsafe task name with payload")
        with (
            patch.object(celery_diagnostics, "log_current_process_memory"),
            self.assertLogs("config.process_diagnostics", level="INFO") as captured,
        ):
            celery_diagnostics.task_prerun_diagnostic(
                sender=task,
                task_id="test-id-untrusted-name",
                task=task,
            )
            celery_diagnostics.task_postrun_diagnostic(
                sender=task,
                task_id="test-id-untrusted-name",
                task=task,
                state="SUCCESS",
            )

        output = "\n".join(captured.output)
        self.assertIn("task_name=unknown", output)
        self.assertNotIn("unsafe task name", output)
