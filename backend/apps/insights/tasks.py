"""Celery workers and the durable Insights work reconciler."""

import logging
import time

from celery import shared_task

from .daily_dispatch import dispatch_daily_insights_syncs
from .models import InsightsSyncStatus, InsightsSyncWorkStage
from .sync_service import (
    StaleInsightsWorkClaim,
    claim_stage_work,
    dispatch_stage_work,
    fail_claimed_stage,
    handle_retryable_stage_result,
    process_content_sync_batch,
    reconcile_insights_sync_work,
    sync_account_snapshot,
)

logger = logging.getLogger(__name__)


def _log_unexpected_failure(task, claim, exc):
    logger.exception(
        "Unexpected Insights stage worker failure.",
        exc_info=(type(exc), Exception("[exception message redacted]"), exc.__traceback__),
        extra={
            "sync_state_id": claim["sync_state_id"],
            "work_id": claim["work_id"],
            "work_generation": claim["generation"],
            "task_name": task.name,
            "task_id": task.request.id,
            "exception_type": type(exc).__name__,
        },
    )


@shared_task(bind=True)
def sync_account_insights_task(self, *, work_id, generation):
    try:
        claim = claim_stage_work(
            work_id=work_id,
            generation=generation,
            celery_task_id=self.request.id,
        )
    except Exception:
        claim_duration = time.monotonic() - claim_started
        logger.info(
            "INSIGHTS_CONTENT_TASK_CLAIM platform=instagram work_id=%s generation=%s duration_seconds=%.6f outcome=claim_error",
            work_id,
            generation,
            claim_duration,
        )
        logger.info(
            "INSIGHTS_CONTENT_TASK_END platform=instagram work_id=%s generation=%s total_duration_seconds=%.6f processed=unknown discovered=unknown total=unknown continue=false outcome=claim_error",
            work_id,
            generation,
            time.monotonic() - task_started,
        )
        raise
    if claim is None or claim["stage"] != InsightsSyncWorkStage.ACCOUNT:
        return {"status": "not_claimed"}
    try:
        from .models import InsightsSyncState

        state = InsightsSyncState.objects.select_related("social_account").get(
            id=claim["sync_state_id"],
        )
        result = sync_account_snapshot(
            claim=claim,
            social_account_id=str(state.social_account_id),
            since=state.since,
            until=state.until,
        )
        if result.get("retryable"):
            return handle_retryable_stage_result(claim, result)
        return result
    except StaleInsightsWorkClaim:
        return {"status": "fenced"}
    except Exception as exc:
        _log_unexpected_failure(self, claim, exc)
        try:
            fail_claimed_stage(
                claim,
                status=InsightsSyncStatus.FAILED,
                error_code="unexpected_sync_error",
                reason="account_worker_failed_unexpectedly",
            )
        except StaleInsightsWorkClaim:
            pass
        raise


@shared_task(bind=True)
def sync_instagram_content_batch_task(self, *, work_id, generation):
    task_started = time.monotonic()
    claim_started = time.monotonic()
    logger.info(
        "INSIGHTS_CONTENT_TASK_START platform=instagram work_id=%s generation=%s",
        work_id,
        generation,
    )
    claim = claim_stage_work(
        work_id=work_id,
        generation=generation,
        celery_task_id=self.request.id,
    )
    claim_duration = time.monotonic() - claim_started
    if claim is None or claim["stage"] != InsightsSyncWorkStage.CONTENT:
        logger.info(
            "INSIGHTS_CONTENT_TASK_CLAIM platform=instagram work_id=%s generation=%s duration_seconds=%.6f outcome=not_claimed",
            work_id,
            generation,
            claim_duration,
        )
        logger.info(
            "INSIGHTS_CONTENT_TASK_END platform=instagram work_id=%s generation=%s total_duration_seconds=%.6f processed=0 discovered=unknown total=unknown continue=false outcome=not_claimed",
            work_id,
            generation,
            time.monotonic() - task_started,
        )
        return {"status": "not_claimed"}
    logger.info(
        "INSIGHTS_CONTENT_TASK_CLAIM platform=instagram social_account_id=%s sync_state_id=%s work_id=%s generation=%s duration_seconds=%.6f outcome=claimed",
        "unknown",
        claim["sync_state_id"],
        claim["work_id"],
        claim["generation"],
        claim_duration,
    )
    outcome = "unexpected_failure"
    result = None
    try:
        result = process_content_sync_batch(claim=claim)
        retryable_result = bool(result.get("retryable"))
        if retryable_result:
            result = handle_retryable_stage_result(claim, result)
        if result.get("continue"):
            # The checkpoint and pending transition committed before publish.
            dispatch_stage_work(claim["work_id"])
        if retryable_result:
            outcome = "retryable_failure"
        elif result.get("status") in {InsightsSyncStatus.FAILED, InsightsSyncStatus.PARTIAL}:
            outcome = "terminal_failure"
        elif result.get("status") == InsightsSyncStatus.COMPLETE:
            outcome = "complete"
        else:
            outcome = result.get("status", "unknown")
        return result
    except StaleInsightsWorkClaim:
        outcome = "fenced"
        return {"status": "fenced"}
    except Exception as exc:
        _log_unexpected_failure(self, claim, exc)
        try:
            fail_claimed_stage(
                claim,
                status=InsightsSyncStatus.FAILED,
                error_code="unexpected_sync_error",
                reason="content_worker_failed_unexpectedly",
            )
        except StaleInsightsWorkClaim:
            pass
        raise
    finally:
        result = result or {}
        logger.info(
            "INSIGHTS_CONTENT_TASK_END platform=instagram social_account_id=unknown sync_state_id=%s work_id=%s generation=%s total_duration_seconds=%.6f processed=%s discovered=unknown total=%s continue=%s outcome=%s",
            claim["sync_state_id"],
            claim["work_id"],
            claim["generation"],
            time.monotonic() - task_started,
            result.get("processed", "unknown"),
            result.get("items_total", "unknown"),
            str(bool(result.get("continue"))).lower(),
            outcome,
        )


@shared_task(name="apps.insights.tasks.reconcile_insights_sync_work_task")
def reconcile_insights_sync_work_task():
    return reconcile_insights_sync_work()


@shared_task(name="apps.insights.tasks.daily_insights_dispatcher_task")
def daily_insights_dispatcher_task():
    return dispatch_daily_insights_syncs()
