"""Bounded, resumable persistence workflow for Instagram Insights."""

import json
import logging
import math
import re
import time
import uuid
from contextlib import contextmanager, nullcontext
from datetime import date, timedelta

from django.conf import settings
from django.db import connection, models, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.integrations.instagram.client import InstagramAPIClient
from apps.integrations.instagram.constants import INSTAGRAM_GRAPH_API_VERSION
from apps.integrations.instagram.crypto import decrypt_token
from apps.integrations.instagram.exceptions import (
    InstagramAPIError,
    InstagramIntegrationError,
    InstagramOAuthConfigurationError,
)
from apps.integrations.instagram.selectors import get_active_instagram_credential
from apps.integrations.meta.client import MetaAPIClient
from apps.integrations.meta.credentials import MetaCredentialService
from apps.integrations.meta.exceptions import MetaAPIError, MetaIntegrationError
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

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
    INSTAGRAM_INSIGHTS_PERMISSION,
    _failure_status,
    _insight_error_metrics,
    _insight_results,
    _insight_total_value,
    _instagram_graph_get,
    _media_is_in_range,
    _metric,
    _normalize_content_item,
    _unavailable_metric,
    _fetch_instagram_account_insights,
    _metric_values_from_insights,
    FACEBOOK_CONTENT_PERMISSION,
    FACEBOOK_INSIGHTS_PERMISSION,
)

CONTENT_INSIGHTS_BATCH_SIZE = 5
FACEBOOK_POST_INSIGHT_METRICS = (
    ("reach", "post_total_media_view_unique", "Reach", "number", "unique_media_viewers"),
    ("views", "post_media_view", "Views", "number", ""),
    ("reactions_by_type", "post_reactions_by_type_total", "Reactions by type", "breakdown", ""),
    ("clicks", "post_clicks", "Clicks", "number", ""),
    ("clicks_by_type", "post_clicks_by_type", "Clicks by type", "breakdown", ""),
)
FACEBOOK_REQUIRED_POST_INSIGHT_OUTPUTS = ("reach", "views", "clicks")
FACEBOOK_POST_INSIGHTS_METRIC_PARAM = ",".join(
    provider_metric
    for output_name, provider_metric, _, _, _ in FACEBOOK_POST_INSIGHT_METRICS
    if output_name in FACEBOOK_REQUIRED_POST_INSIGHT_OUTPUTS
)
INSIGHTS_WORK_LEASE_SECONDS = 40 * 60
INSIGHTS_WORK_RECOVERY_MARGIN_SECONDS = 5 * 60
INSIGHTS_WORK_DISPATCH_TIMEOUT_SECONDS = 5 * 60
INSIGHTS_WORK_HEARTBEAT_INTERVAL_SECONDS = 2 * 60
INSIGHTS_WORK_RECONCILE_INTERVAL_SECONDS = 60
INSIGHTS_WORK_RECONCILE_BATCH_SIZE = 100
INSIGHTS_WORK_RECONCILE_PUBLISH_LIMIT = 50
ACTIVE_SYNC_STATUSES = (InsightsSyncStatus.QUEUED, InsightsSyncStatus.SYNCING)
TERMINAL_SYNC_STATUSES = (
    InsightsSyncStatus.COMPLETE,
    InsightsSyncStatus.PARTIAL,
    InsightsSyncStatus.FAILED,
)
RETRYABLE_REASONS = {"rate_limited", "provider_temporary_error"}
MEDIA_INSIGHT_SPECS = (
    ("reach", "reach", "Reach"),
    ("views", "views", "Views"),
    ("shares", "shares", "Shares"),
    ("saves", "saved", "Saves"),
    ("engagement", "total_interactions", "Engagement"),
)
AUTOMATIC_CONTENT_CONTINUATIONS_KEY = "automatic_continuations"
logger = logging.getLogger(__name__)

_META_ERROR_MESSAGE_MAX_LENGTH = 300
_META_ERROR_SECRET_ASSIGNMENT = re.compile(
    r"(?i)([\"']?\b(?:access[_ -]?token|refresh[_ -]?token|token|"
    r"authorization|oauth[_ -]?code|state|password|client[_ -]?secret|"
    r"api[_ -]?key|secret|cookie|credential)\b[\"']?\s*[:=]\s*[\"']?)"
    r"(?:(?:bearer|oauth)\s+)?[^\s,;\"'&}]+"
)
_META_ERROR_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*")
_META_ERROR_URL = re.compile(r"(?i)https?://\S+")
_META_ERROR_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_META_ERROR_JWT = re.compile(
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
)
_META_ERROR_OPAQUE_VALUE = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])")
_META_ERROR_NUMERIC_ID = re.compile(r"\b\d{12,}\b")


def _log_instagram_content_event(event, *, claim, account, state, level="info", **fields):
    """Emit bounded content-sync diagnostics without provider or user content."""
    details = {
        "platform": "instagram",
        "social_account_id": str(account.id),
        "sync_state_id": str(state.id),
        "work_id": str(claim["work_id"]),
        "generation": claim["generation"],
        **fields,
    }
    rendered = " ".join(
        f"{name}={'null' if value is None else str(value).lower() if isinstance(value, bool) else value}"
        for name, value in details.items()
    )
    log_method = logger.debug if level == "debug" else logger.info
    log_method("INSIGHTS_CONTENT_%s %s", event, rendered)


def _instagram_client_timing(client, field, default=0.0):
    provider_client = getattr(client, "_client", None)
    value = getattr(provider_client, field, default)
    return float(value) if isinstance(value, (int, float)) else default


class _InsightsSqlTimingCollector:
    """Aggregate safe SQL classifications without retaining SQL or parameters."""

    INITIAL_PHASE = "fence"

    def __init__(self):
        self.phase = self.INITIAL_PHASE
        self._sql = {}
        self._measurements = {}

    @staticmethod
    def _table_in_sql(sql, model):
        normalized = sql.lower()
        table = model._meta.db_table.lower()
        return table in normalized

    @classmethod
    def _classify(cls, sql):
        statement = " ".join(str(sql).strip().upper().split())
        first_word = statement.partition(" ")[0]
        if first_word == "RELEASE" and "SAVEPOINT" in statement:
            return "savepoint_release"
        if first_word == "ROLLBACK" and "TO SAVEPOINT" in statement:
            return "savepoint_rollback"
        if first_word == "SAVEPOINT":
            return "savepoint_create"
        if first_word == "SELECT":
            if cls._table_in_sql(sql, InsightsMediaSnapshot):
                return "select_for_update_media"
            if cls._table_in_sql(sql, InsightsContentSnapshotItem):
                return "select_for_update_content"
        if first_word == "UPDATE":
            if cls._table_in_sql(sql, InsightsMediaSnapshot):
                return "update_media"
            if cls._table_in_sql(sql, InsightsContentSnapshotItem):
                return "update_content"
            if cls._table_in_sql(sql, InsightsSyncState):
                return "checkpoint_update"
        if first_word == "INSERT":
            if cls._table_in_sql(sql, InsightsContentSnapshotItem):
                return "insert_content"
        return "other_safe_sql"

    def __call__(self, execute, sql, params, many, context):
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            # Instrumentation must not affect statement success or exception behavior.
            try:
                self._record_sql(self.phase, self._classify(sql), time.perf_counter() - started)
            except Exception:
                pass

    @staticmethod
    def _record(aggregate, key, elapsed):
        entry = aggregate.setdefault(key, {"count": 0, "total_seconds": 0.0, "max_seconds": 0.0})
        entry["count"] += 1
        entry["total_seconds"] += elapsed
        entry["max_seconds"] = max(entry["max_seconds"], elapsed)

    def _record_sql(self, phase, classification, elapsed):
        self._record(self._sql.setdefault(phase, {}), classification, elapsed)

    def record_measurement(self, phase, name, elapsed):
        try:
            self._record(self._measurements.setdefault(phase, {}), name, elapsed)
        except Exception:
            pass

    def set_phase(self, phase):
        self.phase = phase

    def sql_total_seconds(self, phase):
        return sum(
            item["total_seconds"]
            for item in self._sql.get(phase, {}).values()
        )

    def snapshot(self):
        return {
            "measurements": self._measurements,
            "sql": self._sql,
        }


def _sanitize_meta_error_message(message):
    if not isinstance(message, str):
        return ""

    sanitized = _META_ERROR_URL.sub("[redacted-url]", message)
    sanitized = _META_ERROR_SECRET_ASSIGNMENT.sub(r"\1[redacted]", sanitized)
    sanitized = _META_ERROR_BEARER.sub("Bearer [redacted]", sanitized)
    sanitized = _META_ERROR_EMAIL.sub("[redacted-email]", sanitized)
    sanitized = _META_ERROR_JWT.sub("[redacted-token]", sanitized)
    sanitized = _META_ERROR_OPAQUE_VALUE.sub("[redacted-value]", sanitized)
    sanitized = _META_ERROR_NUMERIC_ID.sub("[redacted-id]", sanitized)
    sanitized = re.sub(r"[\r\n\t\x00-\x1f\x7f]+", " ", sanitized)
    return sanitized[:_META_ERROR_MESSAGE_MAX_LENGTH]


def _safe_meta_error_number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _safe_meta_error_label(value, *, max_length=80):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or len(value) > max_length or not re.fullmatch(r"[A-Za-z0-9_.:-]+", value):
        return ""
    return value


def _render_meta_diagnostic_value(value):
    return "unknown" if value is None or value == "" else str(value)


# Temporary allowlisted diagnostics for the next controlled Facebook sync test.
def _log_facebook_content_provider_error(*, claim, social_account_id, error, classification):
    payload = error.error_payload if isinstance(error.error_payload, dict) else {}
    details = payload.get("error", payload)
    if not isinstance(details, dict):
        details = {}

    sanitized_message = _sanitize_meta_error_message(details.get("message")) or None
    stage = _safe_meta_error_label(claim.get("stage"), max_length=16)
    fields = (
        ("operation", "facebook_page_posts"),
        (
            "social_account_id",
            _safe_meta_error_label(
                str(social_account_id) if social_account_id is not None else None,
                max_length=64,
            ),
        ),
        (
            "sync_state_id",
            _safe_meta_error_label(str(claim.get("sync_state_id") or ""), max_length=64),
        ),
        ("work_id", _safe_meta_error_label(str(claim.get("work_id") or ""), max_length=64)),
        ("stage", stage.upper() if stage else None),
        ("http_status", _safe_meta_error_number(error.status_code)),
        ("meta_error_code", _safe_meta_error_number(details.get("code"))),
        ("meta_error_subcode", _safe_meta_error_number(details.get("error_subcode"))),
        ("meta_error_type", _safe_meta_error_label(details.get("type"))),
        ("meta_error_message", sanitized_message),
        ("fbtrace_id", _safe_meta_error_label(details.get("fbtrace_id"), max_length=128)),
        ("normalized_classification", _safe_meta_error_label(classification, max_length=40)),
    )
    rendered_fields = " ".join(
        (
            f"{name}={json.dumps(value, ensure_ascii=True)}"
            if name == "meta_error_message"
            else f"{name}={_render_meta_diagnostic_value(value)}"
        )
        for name, value in fields
    )
    logger.warning(
        "Facebook Insights provider request failed. %s",
        rendered_fields,
    )


class InsightsSyncValidationError(ValueError):
    """A safe error indicating invalid sync inputs or account state."""


def _parse_range(since, until):
    try:
        since_date = since if isinstance(since, date) else date.fromisoformat(str(since))
        until_date = until if isinstance(until, date) else date.fromisoformat(str(until))
    except (TypeError, ValueError) as exc:
        raise InsightsSyncValidationError("invalid_date_range") from exc
    if since_date > until_date or (until_date - since_date).days > 89:
        raise InsightsSyncValidationError("invalid_date_range")
    return since_date, until_date


def _account_is_syncable(account):
    return bool(
        account
        and not account.is_deleted
        and account.platform in {SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK}
        and account.status == SocialAccountStatus.CONNECTED
        and account.is_valid
    )


def _duration_slot_days(*, account, since, until):
    duration_days = (until - since).days + 1
    supported = {
        SocialPlatform.INSTAGRAM: {7, 30},
        SocialPlatform.FACEBOOK: {7, 28},
    }.get(account.platform, set())
    return duration_days if duration_days in supported else None


def request_insights_sync(*, social_account_id, since, until):
    """Create one attempt per explicit refresh and dispatch its stage work."""
    since_date, until_date = _parse_range(since, until)

    with transaction.atomic():
        account = (
            SocialAccount.objects.select_for_update()
            .filter(id=social_account_id, is_deleted=False)
            .first()
        )
        if account is None:
            return {"status": "not_found", "sync_state_id": None}

        slot_days = _duration_slot_days(
            account=account,
            since=since_date,
            until=until_date,
        )
        slot = None
        if slot_days is not None:
            slot, _ = InsightsSnapshotSlot.objects.get_or_create(
                social_account=account,
                duration_days=slot_days,
                is_deleted=False,
            )
            slot = InsightsSnapshotSlot.objects.select_for_update().get(id=slot.id)
            active_state = None
            if slot.active_sync_state_id:
                active_state = InsightsSyncState.objects.select_for_update().filter(
                    id=slot.active_sync_state_id,
                    is_deleted=False,
                    status__in=ACTIVE_SYNC_STATUSES,
                ).first()
            if active_state is None:
                # Adopt an in-flight pre-slot attempt before allowing another
                # refresh for this duration.
                active_states = InsightsSyncState.objects.select_for_update().filter(
                    social_account=account,
                    is_deleted=False,
                    status__in=ACTIVE_SYNC_STATUSES,
                ).order_by("-requested_at", "-id")
                active_state = next((
                    candidate for candidate in active_states
                    if (candidate.until - candidate.since).days + 1 == slot_days
                ), None)
                if active_state is not None:
                    slot.active_sync_state = active_state
                    slot.save(update_fields=("active_sync_state", "updated_at"))
            if active_state is not None:
                return {
                    "status": active_state.status,
                    "sync_state_id": str(active_state.id),
                    "already_active": True,
                }
            if slot.active_sync_state_id:
                slot.active_sync_state = None
                slot.save(update_fields=("active_sync_state", "updated_at"))

        # The account lock serializes attempts even when the requested range
        # is not one of the supported duration slots.
        active_state = InsightsSyncState.objects.select_for_update().filter(
            social_account=account,
            since=since_date,
            until=until_date,
            is_deleted=False,
            status__in=ACTIVE_SYNC_STATUSES,
        ).order_by("-requested_at", "-id").first()
        if active_state is not None:
            return {
                "status": active_state.status,
                "sync_state_id": str(active_state.id),
                "already_active": True,
            }

        state = InsightsSyncState.objects.create(
            social_account=account,
            since=since_date,
            until=until_date,
            api_version=_api_version_for_platform(account.platform),
        )
        _create_stage_work(state)
        if slot is not None:
            slot.active_sync_state = state
            slot.save(update_fields=("active_sync_state", "updated_at"))

        if not _account_is_syncable(account):
            state.status = InsightsSyncStatus.FAILED
            state.account_status = InsightsSyncStatus.FAILED
            state.content_status = InsightsSyncStatus.FAILED
            state.error_code = "account_unavailable"
            state.error_reason = "account_not_connected_or_invalid"
            state.account_error_code = state.error_code
            state.account_error_reason = state.error_reason
            now = timezone.now()
            state.completed_at = now
            state.account_completed_at = now
            state.content_completed_at = now
            state.save()
            InsightsSyncWork.objects.filter(sync_state=state).update(
                status=InsightsSyncWorkStatus.TERMINAL,
                claim_token=None,
                claimed_at=None,
                heartbeat_at=None,
                lease_expires_at=None,
                dispatch_expires_at=None,
                updated_at=timezone.now(),
            )
            if slot is not None and slot.active_sync_state_id == state.id:
                slot.active_sync_state = None
                slot.save(update_fields=("active_sync_state", "updated_at"))
            return {
                "status": state.status,
                "sync_state_id": str(state.id),
                "already_active": False,
            }

        state_id = str(state.id)
        account_id = str(account.id)
        since_value = since_date.isoformat()
        until_value = until_date.isoformat()

        transaction.on_commit(
            lambda: _dispatch_sync_tasks(
                state_id=state_id,
                account_id=account_id,
                since=since_value,
                until=until_value,
            )
        )

    return {
        "status": state.status,
        "sync_state_id": str(state.id),
        "already_active": False,
    }


def _create_stage_work(state):
    for stage in (InsightsSyncWorkStage.ACCOUNT, InsightsSyncWorkStage.CONTENT):
        InsightsSyncWork.objects.create(
            sync_state=state,
            stage=stage,
            generation=1,
            status=InsightsSyncWorkStatus.PENDING,
            next_attempt_at=timezone.now(),
        )


def _api_version_for_platform(platform):
    return (
        settings.META_GRAPH_API_VERSION
        if platform == SocialPlatform.FACEBOOK
        else INSTAGRAM_GRAPH_API_VERSION
    )


def _clear_work_claim(work):
    work.claim_token = None
    work.claimed_at = None
    work.heartbeat_at = None
    work.lease_expires_at = None


def _reserve_work_for_publish(work_id, *, allow_expired=False):
    ref = InsightsSyncWork.objects.filter(id=work_id).values("sync_state_id").first()
    if ref is None:
        return None
    with transaction.atomic():
        state = InsightsSyncState.objects.select_for_update().filter(
            id=ref["sync_state_id"], is_deleted=False,
        ).first()
        if state is None or state.status in TERMINAL_SYNC_STATUSES:
            return None
        work = InsightsSyncWork.objects.select_for_update().filter(
            id=work_id, sync_state=state,
        ).first()
        if work is None or work.status in {
            InsightsSyncWorkStatus.CLAIMED,
            InsightsSyncWorkStatus.TERMINAL,
            InsightsSyncWorkStatus.MIGRATION_HOLD,
        }:
            return None
        now = timezone.now()
        due = work.status == InsightsSyncWorkStatus.PENDING and (
            work.next_attempt_at is None or work.next_attempt_at <= now
        )
        timed_out = allow_expired and work.status in {
            InsightsSyncWorkStatus.PUBLISHING,
            InsightsSyncWorkStatus.DISPATCHED,
        } and work.dispatch_expires_at is not None and work.dispatch_expires_at <= now
        if not due and not timed_out:
            return None
        work.status = InsightsSyncWorkStatus.PUBLISHING
        work.dispatch_attempt += 1
        work.next_attempt_at = None
        work.dispatch_expires_at = now + timedelta(seconds=INSIGHTS_WORK_DISPATCH_TIMEOUT_SECONDS)
        work.celery_task_id = ""
        work.save(update_fields=(
            "status", "dispatch_attempt", "next_attempt_at", "dispatch_expires_at",
            "celery_task_id", "updated_at",
        ))
        return str(work.id), work.generation, work.stage


def _record_publish_result(*, work_id, generation, published=False, task_id="", error_code="dispatch_failed"):
    ref = InsightsSyncWork.objects.filter(id=work_id).values("sync_state_id").first()
    if ref is None:
        return
    with transaction.atomic():
        state = InsightsSyncState.objects.select_for_update().filter(
            id=ref["sync_state_id"], is_deleted=False,
        ).first()
        if state is None:
            return
        work = InsightsSyncWork.objects.select_for_update().filter(
            id=work_id, sync_state=state,
        ).first()
        if (
            work is None or work.generation != generation
            or work.status != InsightsSyncWorkStatus.PUBLISHING
        ):
            return
        if published:
            work.status = InsightsSyncWorkStatus.DISPATCHED
            work.celery_task_id = str(task_id)[:255]
            work.last_error_code = ""
            work.last_error_reason = ""
        else:
            work.status = InsightsSyncWorkStatus.PENDING
            delay = min(30 * (2 ** max(work.dispatch_attempt - 1, 0)), 5 * 60)
            work.next_attempt_at = timezone.now() + timedelta(seconds=delay)
            work.dispatch_expires_at = None
            work.last_error_code = error_code[:64]
            work.last_error_reason = "broker_publish_failed"
        work.save()


def dispatch_stage_work(work_id, *, allow_expired=False):
    work_ref = InsightsSyncWork.objects.select_related("sync_state__social_account").filter(id=work_id).first()
    if work_ref is None:
        return False
    reservation = _reserve_work_for_publish(work_id, allow_expired=allow_expired)
    if reservation is None:
        return False
    work_id, generation, stage = reservation
    from .tasks import sync_account_insights_task, sync_instagram_content_batch_task

    task = (
        sync_account_insights_task
        if stage == InsightsSyncWorkStage.ACCOUNT
        else sync_instagram_content_batch_task
    )
    try:
        result = task.apply_async(kwargs={"work_id": work_id, "generation": generation})
    except Exception:
        _record_publish_result(
            work_id=work_id,
            generation=generation,
            error_code="broker_publish_failed",
        )
        return False
    _record_publish_result(
        work_id=work_id, generation=generation, published=True, task_id=result.id or "",
    )
    return True


def dispatch_sync_state_work(sync_state_id):
    work_ids = list(
        InsightsSyncWork.objects.filter(
            sync_state_id=sync_state_id,
            status=InsightsSyncWorkStatus.PENDING,
        ).order_by("stage").values_list("id", flat=True)
    )
    for work_id in work_ids:
        dispatch_stage_work(work_id)


def _dispatch_sync_tasks(*, state_id, account_id=None, since=None, until=None):
    """Compatibility name for the now durable stage-work dispatcher."""
    return dispatch_sync_state_work(state_id)


def reconcile_insights_sync_work():
    """Recover due dispatch intents and expired worker leases in bounded batches."""
    now = timezone.now()
    candidates = list(
        InsightsSyncWork.objects.filter(
            models.Q(
                status=InsightsSyncWorkStatus.PENDING,
            ) & (models.Q(next_attempt_at__isnull=True) | models.Q(next_attempt_at__lte=now))
            | models.Q(
                status__in=(InsightsSyncWorkStatus.PUBLISHING, InsightsSyncWorkStatus.DISPATCHED),
                dispatch_expires_at__lte=now,
            )
            | models.Q(
                status=InsightsSyncWorkStatus.CLAIMED,
                lease_expires_at__lte=now - timedelta(seconds=INSIGHTS_WORK_RECOVERY_MARGIN_SECONDS),
            )
        ).order_by("updated_at").values_list("id", flat=True)[:INSIGHTS_WORK_RECONCILE_BATCH_SIZE]
    )
    publish_attempts = 0
    publish_successes = 0
    for work_id in candidates:
        ref = InsightsSyncWork.objects.filter(id=work_id).values("sync_state_id").first()
        if ref is None:
            continue
        with transaction.atomic():
            state = InsightsSyncState.objects.select_for_update().filter(
                id=ref["sync_state_id"], is_deleted=False,
            ).first()
            if state is None or state.status in TERMINAL_SYNC_STATUSES:
                continue
            work = InsightsSyncWork.objects.select_for_update().filter(
                id=work_id, sync_state=state,
            ).first()
            if work is None or work.status in {
                InsightsSyncWorkStatus.TERMINAL,
                InsightsSyncWorkStatus.MIGRATION_HOLD,
            }:
                continue
            now = timezone.now()
            if work.status == InsightsSyncWorkStatus.CLAIMED:
                if not work.lease_expires_at or work.lease_expires_at + timedelta(
                    seconds=INSIGHTS_WORK_RECOVERY_MARGIN_SECONDS
                ) > now:
                    continue
                work.generation += 1
                work.status = InsightsSyncWorkStatus.PENDING
                _clear_work_claim(work)
                work.dispatch_expires_at = None
                work.celery_task_id = ""
                work.next_attempt_at = now
                work.save()
            elif work.status in {
                InsightsSyncWorkStatus.PUBLISHING,
                InsightsSyncWorkStatus.DISPATCHED,
            }:
                if not work.dispatch_expires_at or work.dispatch_expires_at > now:
                    continue
                work.status = InsightsSyncWorkStatus.PENDING
                work.next_attempt_at = now
                work.dispatch_expires_at = None
                work.save()
            elif work.status == InsightsSyncWorkStatus.PENDING:
                if work.next_attempt_at and work.next_attempt_at > now:
                    continue
            else:
                continue
        if publish_attempts < INSIGHTS_WORK_RECONCILE_PUBLISH_LIMIT:
            publish_attempts += 1
            publish_successes += int(dispatch_stage_work(work_id) is True)
    return {"candidates": len(candidates), "publish_attempts": publish_attempts, "published": publish_successes}


class StaleInsightsWorkClaim(RuntimeError):
    """Raised when a worker no longer owns the current stage generation."""


@contextmanager
def _fenced_stage_transaction(
    *, work_id, generation, claim_token, _timing_collector=None, **_claim_metadata,
):
    """Lock in state -> work order and validate ownership for every write."""
    wrapper_scope = (
        connection.execute_wrapper(_timing_collector)
        if _timing_collector is not None
        else nullcontext()
    )
    with wrapper_scope:
        if _timing_collector is not None:
            _timing_collector.set_phase("fence")
        sync_state_id = _claim_metadata.get("sync_state_id")
        if not sync_state_id:
            if _timing_collector is not None:
                _timing_collector.set_phase("fence_reference_lookup")
            ref = InsightsSyncWork.objects.filter(id=work_id).values("sync_state_id").first()
            if ref is None:
                raise StaleInsightsWorkClaim("stage work is missing")
            sync_state_id = ref["sync_state_id"]
        outer_started = time.perf_counter()
        atomic_exit_started = None
        try:
            with transaction.atomic():
                if _timing_collector is not None:
                    _timing_collector.set_phase("fence_state_lock")
                state = InsightsSyncState.objects.select_for_update().filter(
                    id=sync_state_id, is_deleted=False,
                ).first()
                if state is None:
                    raise StaleInsightsWorkClaim("sync state is missing")
                if _timing_collector is not None:
                    _timing_collector.set_phase("fence_work_lock")
                work = InsightsSyncWork.objects.select_for_update().filter(
                    id=work_id, sync_state=state,
                ).first()
                now = timezone.now()
                if (
                    work is None
                    or work.generation != generation
                    or work.status != InsightsSyncWorkStatus.CLAIMED
                    or work.claim_token != claim_token
                    or work.lease_expires_at is None
                    or work.lease_expires_at <= now
                    or state.status in TERMINAL_SYNC_STATUSES
                ):
                    raise StaleInsightsWorkClaim("stage claim is no longer current")
                try:
                    yield state, work
                finally:
                    if _timing_collector is not None:
                        atomic_exit_started = time.perf_counter()
                        _timing_collector.set_phase("outer_atomic_exit")
        finally:
            if _timing_collector is not None:
                atomic_finished = time.perf_counter()
                _timing_collector.record_measurement(
                    "outer_transaction", "outer_transaction_wall_seconds",
                    atomic_finished - outer_started,
                )
                if atomic_exit_started is not None:
                    _timing_collector.record_measurement(
                        "outer_transaction", "outer_atomic_exit_seconds",
                        atomic_finished - atomic_exit_started,
                    )
                _timing_collector.set_phase("fence")
                try:
                    logger.debug(
                        "INSIGHTS_CONTENT_DB_TIMINGS platform=instagram sync_state_id=%s work_id=%s generation=%s timing_summary=%s",
                        _claim_metadata.get("sync_state_id", "unknown"),
                        work_id,
                        generation,
                        json.dumps(_timing_collector.snapshot(), sort_keys=True, separators=(",", ":")),
                    )
                except Exception:
                    pass


def claim_stage_work(*, work_id, generation, celery_task_id=""):
    """Atomically acquire one published work generation."""
    ref = InsightsSyncWork.objects.filter(id=work_id).values("sync_state_id").first()
    if ref is None:
        return None
    with transaction.atomic():
        state = InsightsSyncState.objects.select_for_update().filter(
            id=ref["sync_state_id"], is_deleted=False,
        ).first()
        if state is None or state.status in TERMINAL_SYNC_STATUSES:
            return None
        work = InsightsSyncWork.objects.select_for_update().filter(
            id=work_id, sync_state=state,
        ).first()
        if (
            work is None
            or work.generation != generation
            or work.status not in {
                InsightsSyncWorkStatus.PUBLISHING,
                InsightsSyncWorkStatus.DISPATCHED,
            }
            or work.stage not in {InsightsSyncWorkStage.ACCOUNT, InsightsSyncWorkStage.CONTENT}
        ):
            return None
        stage_field = (
            "account_status" if work.stage == InsightsSyncWorkStage.ACCOUNT
            else "content_status"
        )
        if getattr(state, stage_field) in TERMINAL_SYNC_STATUSES:
            work.status = InsightsSyncWorkStatus.TERMINAL
            work.dispatch_expires_at = None
            work.save(update_fields=("status", "dispatch_expires_at", "updated_at"))
            return None
        now = timezone.now()
        work.status = InsightsSyncWorkStatus.CLAIMED
        work.claim_token = uuid.uuid4()
        work.claimed_at = now
        work.heartbeat_at = now
        work.lease_expires_at = now + timedelta(seconds=INSIGHTS_WORK_LEASE_SECONDS)
        work.dispatch_expires_at = None
        if celery_task_id:
            work.celery_task_id = str(celery_task_id)[:255]
        work.save(update_fields=(
            "status", "claim_token", "claimed_at", "heartbeat_at", "lease_expires_at",
            "dispatch_expires_at", "celery_task_id", "updated_at",
        ))
        setattr(state, stage_field, InsightsSyncStatus.SYNCING)
        if not state.started_at:
            state.started_at = now
        _aggregate_overall_status(state)
        state.save(update_fields=(stage_field, "status", "started_at", "completed_at", "updated_at"))
        return {
            "work_id": str(work.id),
            "sync_state_id": str(state.id),
            "stage": work.stage,
            "generation": work.generation,
            "claim_token": work.claim_token,
        }


def heartbeat_stage_work(claim):
    with _fenced_stage_transaction(**claim) as (state, work):
        now = timezone.now()
        work.heartbeat_at = now
        work.lease_expires_at = now + timedelta(seconds=INSIGHTS_WORK_LEASE_SECONDS)
        work.save(update_fields=("heartbeat_at", "lease_expires_at", "updated_at"))
    return True


def _finish_claimed_stage(claim, *, status, state_fields, before_terminal=None):
    with _fenced_stage_transaction(**claim) as (state, work):
        for name, value in state_fields.items():
            setattr(state, name, value)
        stage_field = "account_status" if work.stage == InsightsSyncWorkStage.ACCOUNT else "content_status"
        completion_field = "account_completed_at" if work.stage == InsightsSyncWorkStage.ACCOUNT else "content_completed_at"
        if status in TERMINAL_SYNC_STATUSES and not getattr(state, completion_field):
            setattr(state, completion_field, timezone.now())
        if before_terminal is not None:
            before_terminal(state, work)
        setattr(state, stage_field, status)
        _aggregate_overall_status(state)
        state.save(update_fields=tuple(dict.fromkeys((
            *state_fields.keys(), completion_field, stage_field, "status", "started_at", "completed_at", "updated_at",
        ))))
        work.status = InsightsSyncWorkStatus.TERMINAL
        _clear_work_claim(work)
        work.next_attempt_at = None
        work.dispatch_expires_at = None
        work.save(update_fields=(
            "status", "claim_token", "claimed_at", "heartbeat_at", "lease_expires_at",
            "next_attempt_at", "dispatch_expires_at", "updated_at",
        ))
        _update_snapshot_slot_for_terminal_stage(state, work.stage, status)
        return state


def _update_snapshot_slot_for_terminal_stage(state, stage, stage_status):
    """Publish only successful stage pointers and clear terminal active attempts."""
    slot_days = (state.until - state.since).days + 1
    slot = InsightsSnapshotSlot.objects.select_for_update().filter(
        social_account=state.social_account,
        duration_days=slot_days,
        is_deleted=False,
        active_sync_state=state,
    ).first()
    if slot is None:
        return

    update_fields = []
    if stage_status == InsightsSyncStatus.COMPLETE:
        if stage == InsightsSyncWorkStage.ACCOUNT:
            slot.published_account_sync_state = state
            update_fields.append("published_account_sync_state")
        elif stage == InsightsSyncWorkStage.CONTENT:
            slot.published_content_sync_state = state
            update_fields.append("published_content_sync_state")
    if state.status in TERMINAL_SYNC_STATUSES:
        slot.active_sync_state = None
        update_fields.append("active_sync_state")
    if update_fields:
        slot.save(update_fields=(*update_fields, "updated_at"))


def fail_claimed_stage(claim, *, status, error_code, reason):
    if claim["stage"] == InsightsSyncWorkStage.ACCOUNT:
        state_fields = {}
        state_fields.update({
            "account_error_code": error_code[:64],
            "account_error_reason": reason[:255],
            "account_completed_at": timezone.now(),
        })
    else:
        state_fields = {"error_code": error_code[:64], "error_reason": reason[:255]}
    return _finish_claimed_stage(claim, status=status, state_fields=state_fields)


def rearm_claimed_work(
    claim, *, delay_seconds=0, state_fields=None, stage_status=None,
    provider_retry_count=None,
):
    """Persist optional progress and make this exact generation dispatchable."""
    with _fenced_stage_transaction(**claim) as (state, work):
        for name, value in (state_fields or {}).items():
            setattr(state, name, value)
        stage_field = "account_status" if work.stage == InsightsSyncWorkStage.ACCOUNT else "content_status"
        state_fields = dict(state_fields or {})
        if stage_status is not None:
            setattr(state, stage_field, stage_status)
            state_fields[stage_field] = stage_status
            _aggregate_overall_status(state)
            state_fields.update({"status": state.status, "started_at": state.started_at, "completed_at": state.completed_at})
        if state_fields:
            state.save(update_fields=(*state_fields.keys(), "updated_at"))
        work.status = InsightsSyncWorkStatus.PENDING
        _clear_work_claim(work)
        work.dispatch_expires_at = None
        work.celery_task_id = ""
        work.next_attempt_at = timezone.now() + timedelta(seconds=max(delay_seconds, 0))
        if provider_retry_count is not None:
            work.provider_retry_count = provider_retry_count
        work.save(update_fields=(
            "status", "claim_token", "claimed_at", "heartbeat_at", "lease_expires_at",
            "dispatch_expires_at", "celery_task_id", "next_attempt_at",
            *( ("provider_retry_count",) if provider_retry_count is not None else () ),
            "updated_at",
        ))
    return True


def _work_for_claim(claim):
    return InsightsSyncWork.objects.filter(
        id=claim["work_id"], generation=claim["generation"],
        claim_token=claim["claim_token"], status=InsightsSyncWorkStatus.CLAIMED,
    ).first()


def _update_sync_state(sync_state_id, **fields):
    with transaction.atomic():
        state = InsightsSyncState.objects.select_for_update().get(
            id=sync_state_id,
            is_deleted=False,
        )
        stage_fields = {"account_status", "content_status"}.intersection(fields)
        if stage_fields and state.status in TERMINAL_SYNC_STATUSES:
            # A late worker must not rewrite a state after another worker has
            # already finalized this sync. A deliberate retry resets the row
            # directly in request_insights_sync above.
            return state
        for name, value in fields.items():
            setattr(state, name, value)
        update_fields = list(fields)
        if stage_fields:
            _aggregate_overall_status(state)
            update_fields.extend(("status", "started_at", "completed_at"))
        state.save(update_fields=(*dict.fromkeys(update_fields), "updated_at"))
        if "account_status" in stage_fields:
            _update_snapshot_slot_for_terminal_stage(
                state, InsightsSyncWorkStage.ACCOUNT, state.account_status,
            )
        if "content_status" in stage_fields:
            _update_snapshot_slot_for_terminal_stage(
                state, InsightsSyncWorkStage.CONTENT, state.content_status,
            )
        return state


def _aggregate_overall_status(state):
    """Derive public overall state from the independently persisted stages."""
    account = state.account_status
    content = state.content_status
    active = set(ACTIVE_SYNC_STATUSES)
    terminal = set(TERMINAL_SYNC_STATUSES)

    if account == content == InsightsSyncStatus.QUEUED:
        overall = InsightsSyncStatus.QUEUED
    elif account in active or content in active:
        overall = InsightsSyncStatus.SYNCING
    elif account in terminal and content in terminal:
        if InsightsSyncStatus.FAILED in (account, content):
            overall = InsightsSyncStatus.FAILED
        elif InsightsSyncStatus.PARTIAL in (account, content):
            overall = InsightsSyncStatus.PARTIAL
        else:
            overall = InsightsSyncStatus.COMPLETE
    else:
        # Defensive handling for invalid legacy values: do not advertise
        # completion until both stages are recognized terminal states.
        overall = InsightsSyncStatus.SYNCING

    state.status = overall
    if overall == InsightsSyncStatus.SYNCING:
        state.started_at = state.started_at or timezone.now()
        state.completed_at = None
    elif overall in TERMINAL_SYNC_STATUSES:
        state.completed_at = state.completed_at or timezone.now()
    else:
        state.completed_at = None


def mark_account_sync_terminal(*, sync_state_id, status, error_code, reason):
    _update_sync_state(
        sync_state_id,
        account_status=status,
        account_error_code=error_code[:64],
        account_error_reason=reason[:255],
        account_completed_at=timezone.now(),
    )


class _HeartbeatInstagramClient:
    """Call the existing provider client while renewing the DB lease at safe points."""

    def __init__(self, client, claim):
        self._client = client
        self._claim = claim

    def graph_get(self, path, *, access_token, params=None):
        heartbeat_stage_work(self._claim)
        try:
            return self._client.graph_get(path, access_token=access_token, params=params)
        finally:
            heartbeat_stage_work(self._claim)


class _HeartbeatMetaClient:
    """Use the Meta client while refreshing the durable work lease."""

    def __init__(self, client, claim):
        self._client = client
        self._claim = claim

    def get(self, path, *, access_token, params=None):
        heartbeat_stage_work(self._claim)
        try:
            return self._client.get(path, access_token=access_token, params=params)
        finally:
            heartbeat_stage_work(self._claim)


def _facebook_metric_unavailable(
    *, label, provider_metric, reason="metric_not_returned",
    availability="unavailable", period="day", measurement="",
    aggregation="",
):
    metric = _unavailable_metric(
        label=label,
        source="facebook",
        availability=availability,
        reason=reason,
        provider_metric=provider_metric,
        period=period,
    )
    if measurement:
        metric["measurement"] = measurement
    if aggregation:
        metric["aggregation"] = aggregation
    return metric


def _facebook_daily_metric_sum(points, *, provider_metric, label, since, until):
    aggregation = "selected_range_daily_sum"
    if not points:
        return _facebook_metric_unavailable(
            label=label,
            provider_metric=provider_metric,
            reason="metric_not_returned",
            period="selected_range",
            aggregation=aggregation,
        )

    expected_days = (until - since).days + 1
    values_by_date = {}
    for point in points:
        point_date = point.get("date") if isinstance(point, dict) else None
        metric = point.get("value") if isinstance(point, dict) else None
        value = metric.get("value") if isinstance(metric, dict) else None
        if isinstance(metric, dict) and metric.get("availability") != "available":
            return _facebook_metric_unavailable(
                label=label,
                provider_metric=provider_metric,
                reason=metric.get("reason") or "metric_not_returned",
                period="selected_range",
                aggregation=aggregation,
            )
        if (
            not isinstance(point_date, str)
            or point_date in values_by_date
            or not isinstance(metric, dict)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            return _facebook_metric_unavailable(
                label=label,
                provider_metric=provider_metric,
                reason="malformed_metric_response",
                period="selected_range",
                aggregation=aggregation,
            )
        values_by_date[point_date] = value

    expected_dates = {
        (since + timedelta(days=offset)).isoformat()
        for offset in range(expected_days)
    }
    if set(values_by_date) != expected_dates:
        return _facebook_metric_unavailable(
            label=label,
            provider_metric=provider_metric,
            reason="incomplete_date_coverage",
            period="selected_range",
            aggregation=aggregation,
        )

    return {
        "value": sum(values_by_date.values()),
        "label": label,
        "unit": "count",
        "availability": "available",
        "source": "facebook",
        "provider_metric": provider_metric,
        "period": "selected_range",
        "aggregation": aggregation,
        "reason": "",
    }


def _facebook_native_metric(
    points, *, provider_metric, label, native_period, until, measurement="",
):
    until_date = until.isoformat() if isinstance(until, date) else str(until)
    candidates = [
        point for point in points
        if isinstance(point, dict) and point.get("date") == until_date
    ]
    if len(candidates) != 1:
        return _facebook_metric_unavailable(
            label=label,
            provider_metric=provider_metric,
            reason=(
                "native_window_not_returned"
                if not candidates
                else "ambiguous_native_aggregate"
            ),
            period=native_period,
            measurement=measurement,
        )
    point = candidates[0]
    metric = point.get("value") if isinstance(point, dict) else None
    value = metric.get("value") if isinstance(metric, dict) else None
    if isinstance(metric, dict) and metric.get("availability") != "available":
        return _facebook_metric_unavailable(
            label=label,
            provider_metric=provider_metric,
            reason=metric.get("reason") or "metric_not_returned",
            period=native_period,
            measurement=measurement,
        )
    if (
        not isinstance(metric, dict)
        or metric.get("period") != native_period
        or isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        return _facebook_metric_unavailable(
            label=label,
            provider_metric=provider_metric,
            reason="malformed_metric_response",
            period=native_period,
            measurement=measurement,
        )
    result = dict(metric)
    result.update({
        "label": label,
        "source": "facebook",
        "provider_metric": provider_metric,
        "period": native_period,
    })
    result["date"] = point.get("date")
    if measurement:
        result["measurement"] = measurement
    return result


def _facebook_native_reach_metric(points, *, provider_metric, native_period, until):
    return _facebook_native_metric(
        points,
        provider_metric=provider_metric,
        label="Reach",
        native_period=native_period,
        until=until,
        measurement="unique_media_viewers",
    )


def _sync_facebook_account_snapshot(*, claim, account, since, until):
    daily_metrics = (
        ("page_post_engagements", "engagement", "Engagement"),
        ("page_media_view", "views", "Views"),
    )
    metrics = {
        output_name: _facebook_metric_unavailable(
            label=label,
            provider_metric=provider_metric,
            period="selected_range",
            aggregation="selected_range_daily_sum",
        )
        for provider_metric, output_name, label in daily_metrics
    }
    current_followers = _unavailable_metric(
        label="Current followers",
        source="facebook",
        availability="unavailable",
        reason="metric_not_returned",
        provider_metric="followers_count",
        period="current",
    )
    profile_metadata = {"availability": "unavailable", "reason": "profile_not_returned"}
    range_days = (until - since).days + 1
    native_reach_period = {7: "week", 28: "days_28"}.get(range_days)
    metrics["reach"] = _facebook_metric_unavailable(
        label="Reach",
        provider_metric="page_total_media_view_unique",
        reason=(
            "metric_not_returned"
            if native_reach_period
            else "no_exact_native_aggregate_for_selected_range"
        ),
        availability="unavailable" if native_reach_period else "not_supported",
        period=native_reach_period,
        measurement="unique_media_viewers",
    )
    metrics["followers"] = current_followers
    client = _HeartbeatMetaClient(MetaAPIClient(), claim)

    try:
        token = MetaCredentialService.get_access_token(social_account=account)
    except MetaIntegrationError:
        _finish_claimed_stage(
            claim,
            status=InsightsSyncStatus.FAILED,
            state_fields={
                "account_error_code": "invalid_credential",
                "account_error_reason": "credential_unavailable_or_configuration_error",
                "account_completed_at": timezone.now(),
            },
        )
        return {"status": "failed", "error_code": "invalid_credential"}

    try:
        profile = client.get(
            f"/{account.platform_account_id}",
            access_token=token,
            params={"fields": "id,name,username,followers_count,picture"},
        )
        if str(profile.get("id") or "") != str(account.platform_account_id):
            _finish_claimed_stage(
                claim,
                status=InsightsSyncStatus.FAILED,
                state_fields={
                    "account_error_code": "invalid_account",
                    "account_error_reason": "provider_account_id_mismatch",
                    "account_completed_at": timezone.now(),
                },
            )
            return {"status": "failed", "error_code": "invalid_account"}
        picture = profile.get("picture") if isinstance(profile.get("picture"), dict) else {}
        picture_data = picture.get("data") if isinstance(picture.get("data"), dict) else {}
        profile_metadata = {
            "availability": "available",
            "reason": "",
            "id": str(profile.get("id") or ""),
            "name": str(profile.get("name") or ""),
            "username": str(profile.get("username") or ""),
            "profile_image": str(picture_data.get("url") or ""),
        }
        if "followers_count" in profile and profile["followers_count"] is not None:
            profile_metadata["followers_count"] = profile["followers_count"]
            current_followers = _metric(
                value=profile["followers_count"],
                label="Current followers",
                source="facebook",
                period="current",
                provider_metric="followers_count",
            )
        profile_error = None
    except MetaAPIError as exc:
        availability, reason = _failure_status(exc)
        if reason == "invalid_credential":
            _finish_claimed_stage(
                claim,
                status=InsightsSyncStatus.FAILED,
                state_fields={
                    "account_error_code": reason,
                    "account_error_reason": reason,
                    "account_completed_at": timezone.now(),
                },
            )
            return {"status": "failed", "error_code": reason}
        if reason in RETRYABLE_REASONS:
            return {"status": "retryable", "retryable": True, "error_code": reason}
        if availability == "permission_required":
            reason = FACEBOOK_CONTENT_PERMISSION
        profile_error = reason
        current_followers = _unavailable_metric(
            label="Current followers",
            source="facebook",
            availability=availability,
            reason=reason,
            provider_metric="followers_count",
            period="current",
        )
        profile_metadata["reason"] = reason

    native_account_metrics = {
        "page_post_engagements": ("engagement", "Engagement"),
        "page_media_view": ("views", "Views"),
    }
    requested_daily_metrics = (
        () if native_reach_period else daily_metrics
    )
    daily_metric_names = ["page_follows"]
    if not native_reach_period:
        daily_metric_names.extend(provider_metric for provider_metric, _, _ in daily_metrics)

    try:
        insights = client.get(
            f"/{account.platform_account_id}/insights",
            access_token=token,
            params={
                "metric": ",".join(daily_metric_names),
                "period": "day",
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
        )
        normalized = _metric_values_from_insights(
            insights,
            source="facebook",
            since=since,
            until=until,
        )
        follower_points = normalized.get("page_follows", [])
        for provider_metric, output_name, label in requested_daily_metrics:
            metrics[output_name] = _facebook_daily_metric_sum(
                normalized.get(provider_metric, []),
                provider_metric=provider_metric,
                label=label,
                since=since,
                until=until,
            )
        insights_error = None
    except MetaAPIError as exc:
        availability, reason = _failure_status(exc)
        if reason == "invalid_credential":
            _finish_claimed_stage(
                claim,
                status=InsightsSyncStatus.FAILED,
                state_fields={
                    "account_error_code": reason,
                    "account_error_reason": reason,
                    "account_completed_at": timezone.now(),
                },
            )
            return {"status": "failed", "error_code": reason}
        if reason in RETRYABLE_REASONS:
            return {"status": "retryable", "retryable": True, "error_code": reason}
        if availability == "permission_required":
            reason = FACEBOOK_INSIGHTS_PERMISSION
        metrics.update({
            output_name: _facebook_metric_unavailable(
                label=label,
                provider_metric=provider_metric,
                reason=reason,
                availability=availability,
                period="selected_range",
                aggregation="selected_range_daily_sum",
            )
            for provider_metric, output_name, label in requested_daily_metrics
        })
        follower_points = []
        insights_error = reason

    reach_error = None
    if native_reach_period:
        try:
            native_response = client.get(
                f"/{account.platform_account_id}/insights",
                access_token=token,
                params={
                    "metric": (
                        "page_total_media_view_unique,page_post_engagements,page_media_view"
                    ),
                    "period": native_reach_period,
                    "since": since.isoformat(),
                    "until": until.isoformat(),
                },
            )
            native_normalized = _metric_values_from_insights(
                native_response,
                source="facebook",
                since=since,
                until=until,
            )
            metrics["reach"] = _facebook_native_reach_metric(
                native_normalized.get("page_total_media_view_unique", []),
                provider_metric="page_total_media_view_unique",
                native_period=native_reach_period,
                until=until,
            )
            for provider_metric, (output_name, label) in native_account_metrics.items():
                metrics[output_name] = _facebook_native_metric(
                    native_normalized.get(provider_metric, []),
                    provider_metric=provider_metric,
                    label=label,
                    native_period=native_reach_period,
                    until=until,
                )
        except MetaAPIError as exc:
            availability, reason = _failure_status(exc)
            if reason == "invalid_credential":
                _finish_claimed_stage(
                    claim,
                    status=InsightsSyncStatus.FAILED,
                    state_fields={
                        "account_error_code": reason,
                        "account_error_reason": reason,
                        "account_completed_at": timezone.now(),
                    },
                )
                return {"status": "failed", "error_code": reason}
            if reason in RETRYABLE_REASONS:
                return {"status": "retryable", "retryable": True, "error_code": reason}
            if availability == "permission_required":
                reason = FACEBOOK_INSIGHTS_PERMISSION
            reach_error = reason
            metrics["reach"] = _facebook_metric_unavailable(
                label="Reach",
                provider_metric="page_total_media_view_unique",
                reason=reason,
                availability=availability,
                period=native_reach_period,
                measurement="unique_media_viewers",
            )
            for provider_metric, (output_name, label) in native_account_metrics.items():
                metrics[output_name] = _facebook_metric_unavailable(
                    label=label,
                    provider_metric=provider_metric,
                    reason=reason,
                    availability=availability,
                    period=native_reach_period,
                )

    metrics["followers"] = current_followers

    follower_growth_availability = "available" if follower_points else "unavailable"
    follower_growth_reason = "" if follower_points else insights_error or "metric_not_returned"
    follower_growth = {
        "availability": follower_growth_availability,
        "reason": follower_growth_reason,
        "current_value": current_followers,
        "change": _unavailable_metric(
            label="Follower change",
            source="facebook",
            availability="unavailable",
            reason="range_change_not_computed",
            period="selected_range",
            provider_metric="page_follows",
        ),
        "points": follower_points,
    }
    provider_failure = profile_error or insights_error or reach_error
    preserve_existing_snapshot = bool(provider_failure)
    account_partial = bool(provider_failure)
    final_status = InsightsSyncStatus.PARTIAL if account_partial else InsightsSyncStatus.COMPLETE
    _finish_claimed_stage(
        claim,
        status=final_status,
        state_fields={
            "account_error_code": "provider_request_failed" if account_partial else "",
            "account_error_reason": provider_failure or "",
            "account_completed_at": timezone.now(),
        },
        before_terminal=lambda locked_state, *_: _save_account_snapshot(
            account=account,
            sync_state=locked_state,
            since=since,
            until=until,
            metrics=metrics,
            follower_growth=follower_growth,
            profile=profile_metadata,
            preserve_existing=preserve_existing_snapshot,
            merge_available_metrics=True,
            api_version=settings.META_GRAPH_API_VERSION,
        ),
    )
    return {
        "status": "partial" if account_partial else "complete",
        "insights_available": any(metric.get("availability") == "available" for metric in metrics.values()),
    }


def _account_snapshot_failure_metrics(reason, availability):
    names = (
        ("followers", "Followers", "followers_count", "current"),
        ("reach", "Reach", "reach", "selected_range"),
        ("views", "Views", "views", "selected_range"),
        ("engagement", "Total interactions", "total_interactions", "selected_range"),
        ("accounts_engaged", "Accounts engaged", "accounts_engaged", "selected_range"),
    )
    metrics = {
        name: _unavailable_metric(
            label=label,
            source="instagram",
            availability=availability,
            reason=reason,
            provider_metric=provider_metric,
            period=period,
        )
        for name, label, provider_metric, period in names
    }
    metrics["impressions"] = _unavailable_metric(
        label="Impressions",
        source="instagram",
        availability="not_supported",
        reason="metric_deprecated",
        provider_metric="impressions",
    )
    return metrics


def _merge_metric_envelopes_preserving_available(existing_metrics, new_metrics):
    """Keep valid Facebook metric envelopes when a refresh omits that metric."""
    existing = existing_metrics if isinstance(existing_metrics, dict) else {}
    incoming = new_metrics if isinstance(new_metrics, dict) else {}
    merged = dict(existing)
    for name, new_metric in incoming.items():
        old_metric = existing.get(name)
        if (
            isinstance(old_metric, dict)
            and old_metric.get("availability") == "available"
            and (
                not isinstance(new_metric, dict)
                or new_metric.get("availability") != "available"
            )
        ):
            continue
        merged[name] = new_metric
    return merged


def _save_account_snapshot(
    *, account, since, until, metrics, follower_growth, profile, sync_state=None,
    preserve_existing=False, merge_available_metrics=False,
    api_version=INSTAGRAM_GRAPH_API_VERSION,
):
    snapshot_query = InsightsAccountSnapshot.objects.filter(
        social_account=account,
        since=since,
        until=until,
        is_deleted=False,
    )
    if preserve_existing and snapshot_query.exists():
        return
    existing_snapshot = snapshot_query.filter(api_version=api_version).first()
    if existing_snapshot is not None and merge_available_metrics:
        metrics = _merge_metric_envelopes_preserving_available(
            existing_snapshot.metrics,
            metrics,
        )
        existing_follower_growth = existing_snapshot.follower_growth
        if (
            isinstance(existing_follower_growth, dict)
            and existing_follower_growth.get("availability") == "available"
            and isinstance(follower_growth, dict)
            and follower_growth.get("availability") != "available"
        ):
            follower_growth = existing_follower_growth
        existing_profile = existing_snapshot.profile_metadata
        if isinstance(existing_profile, dict) and isinstance(profile, dict):
            profile = {**existing_profile, **profile}
    lookup = {
        "social_account": account,
        "since": since,
        "until": until,
        "api_version": api_version,
        "is_deleted": False,
    }
    if sync_state is not None:
        lookup["sync_state"] = sync_state
    InsightsAccountSnapshot.objects.update_or_create(
        **lookup,
        defaults={
            "metrics": metrics,
            "follower_growth": follower_growth,
            "profile_metadata": profile,
            "fetched_at": (
                sync_state.account_completed_at
                if sync_state is not None and sync_state.account_completed_at
                else timezone.now()
            ),
        },
    )


def sync_account_snapshot(*, claim, social_account_id, since, until):
    """Fetch account metrics and persist them only under the current work fence."""
    since_date, until_date = _parse_range(since, until)
    state = InsightsSyncState.objects.select_related("social_account").filter(
        id=claim["sync_state_id"], is_deleted=False,
    ).first()
    account = SocialAccount.objects.filter(id=social_account_id, is_deleted=False).first()
    if state is None:
        return {"status": "not_found"}
    if account is None or not _account_is_syncable(account):
        _finish_claimed_stage(
            claim,
            status=InsightsSyncStatus.FAILED,
            state_fields={
                "account_error_code": "account_unavailable",
                "account_error_reason": "account_not_connected_or_invalid",
                "account_completed_at": timezone.now(),
            },
        )
        return {"status": "failed", "error_code": "account_unavailable"}

    with _fenced_stage_transaction(**claim) as (locked, work):
        locked.account_started_at = locked.account_started_at or timezone.now()
        locked.account_error_code = ""
        locked.account_error_reason = ""
        locked.save(update_fields=("account_started_at", "account_error_code", "account_error_reason", "updated_at"))

    if account.platform == SocialPlatform.FACEBOOK:
        return _sync_facebook_account_snapshot(
            claim=claim,
            account=account,
            since=since_date,
            until=until_date,
        )

    try:
        credential = get_active_instagram_credential(social_account=account)
        if credential is None:
            raise InstagramIntegrationError("Instagram credential is unavailable.")
        token = decrypt_token(credential.encrypted_access_token)
        client = _HeartbeatInstagramClient(InstagramAPIClient(), claim)
        profile = _instagram_graph_get(
            client,
            account.platform_account_id,
            access_token=token,
            params={"fields": "id,username,name,profile_picture_url,followers_count,media_count"},
        )
        if str(profile.get("id") or "") != str(account.platform_account_id):
            _finish_claimed_stage(
                claim, status=InsightsSyncStatus.FAILED,
                state_fields={
                    "account_error_code": "invalid_account",
                    "account_error_reason": "provider_account_id_mismatch",
                    "account_completed_at": timezone.now(),
                },
            )
            return {"status": "failed", "error_code": "invalid_account"}

        profile_metadata = {
            key: profile.get(key)
            for key in ("id", "username", "name", "profile_picture_url", "media_count")
            if profile.get(key) is not None
        }
        followers = (
            _metric(
                value=profile["followers_count"], label="Followers", source="instagram",
                period="current", provider_metric="followers_count",
            )
            if "followers_count" in profile else _unavailable_metric(
                label="Followers", source="instagram", availability="unavailable",
                reason="metric_not_returned", period="current", provider_metric="followers_count",
            )
        )
        metrics, follower_growth, insights_available = _fetch_instagram_account_insights(
            client=client, account=account, token=token, since=since_date,
            until=until_date, current_followers=followers,
        )
        transient_reasons = {
            metric.get("reason") for metric in metrics.values() if isinstance(metric, dict)
        }
        transient_reasons.add(follower_growth.get("reason"))
        retryable_reason = next((reason for reason in RETRYABLE_REASONS if reason in transient_reasons), "")
        account_partial = any(
            metric.get("availability") in {"unavailable", "permission_required", "provider_error"}
            for metric in metrics.values() if isinstance(metric, dict)
        ) or follower_growth.get("availability") in {"permission_required", "provider_error"}
        if retryable_reason:
            return {"status": "retryable", "retryable": True, "error_code": retryable_reason}

        final_status = InsightsSyncStatus.PARTIAL if account_partial else InsightsSyncStatus.COMPLETE
        _finish_claimed_stage(
            claim,
            status=final_status,
            state_fields={
                "account_error_code": "metric_unavailable" if account_partial else "",
                "account_error_reason": "one_or_more_metrics_unavailable" if account_partial else "",
                "account_completed_at": timezone.now(),
            },
            before_terminal=lambda locked_state, *_: _save_account_snapshot(
                account=account, sync_state=locked_state, since=since_date, until=until_date, metrics=metrics,
                follower_growth=follower_growth, profile=profile_metadata,
                preserve_existing=account_partial,
            ),
        )
        return {
            "status": "partial" if account_partial else "complete",
            "insights_available": insights_available,
        }
    except InstagramAPIError as exc:
        availability, reason = _failure_status(exc)
        if reason in RETRYABLE_REASONS:
            return {"status": "retryable", "retryable": True, "error_code": reason}
        snapshot = None
        final_status = InsightsSyncStatus.FAILED
        if availability == "permission_required":
            snapshot = {
                "account": account, "since": since_date, "until": until_date,
                "sync_state": state,
                "metrics": _account_snapshot_failure_metrics(reason, availability),
                "follower_growth": {"availability": availability, "reason": reason, "points": []},
                "profile": {},
            }
            final_status = InsightsSyncStatus.PARTIAL
        _finish_claimed_stage(
            claim, status=final_status,
            state_fields={
                "account_error_code": reason, "account_error_reason": reason,
                "account_completed_at": timezone.now(),
            },
            before_terminal=(
                lambda locked_state, *_: _save_account_snapshot(
                    **{**snapshot, "sync_state": locked_state},
                    preserve_existing=True,
                )
            ) if snapshot else None,
        )
        return {"status": final_status, "error_code": reason}
    except (InstagramIntegrationError, InstagramOAuthConfigurationError):
        _finish_claimed_stage(
            claim, status=InsightsSyncStatus.FAILED,
            state_fields={
                "account_error_code": "invalid_credential",
                "account_error_reason": "credential_unavailable_or_configuration_error",
                "account_completed_at": timezone.now(),
            },
        )
        return {"status": "failed", "error_code": "invalid_credential"}


def _safe_published_at(value):
    parsed = parse_datetime(str(value or ""))
    if parsed is not None and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def _upsert_content_snapshot_item(*, state, provider_media_id, metadata, metrics=None, fetched_at=None):
    """Persist this attempt's media data independently from the mutable cache row."""
    item, created = InsightsContentSnapshotItem.objects.get_or_create(
        sync_state=state,
        provider_media_id=provider_media_id,
        is_deleted=False,
        defaults={
            **metadata,
            "api_version": state.api_version,
            "metrics": metrics or {},
            "fetched_at": fetched_at,
        },
    )
    if created:
        return item
    changed = []
    for field in ("media_type", "caption", "permalink", "published_at"):
        value = metadata.get(field)
        if getattr(item, field) != value:
            setattr(item, field, value)
            changed.append(field)
    if item.api_version != state.api_version:
        item.api_version = state.api_version
        changed.append("api_version")
    if changed:
        item.save(update_fields=(*changed, "updated_at"))
    return item


def _persist_media_page(*, state, account, page, since, until):
    raw_items = page.get("data", [])
    if not isinstance(raw_items, list):
        raise InstagramAPIError("Instagram returned an invalid media response.")
    eligible = []
    for item in raw_items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        if not _media_is_in_range(item, since=since, until=until):
            continue
        normalized = _normalize_content_item(
            item=item,
            source="instagram",
            since=since,
            until=until,
            supports_insights=True,
            permission=INSTAGRAM_INSIGHTS_PERMISSION,
        )
        media_id = normalized["content_id"]
        eligible.append(media_id)
        published_at = _safe_published_at(normalized.get("published_at"))
        metadata = {
            "media_type": normalized["media_type"],
            "caption": normalized["caption"],
            "permalink": normalized["permalink"],
            "published_at": published_at,
        }
        _upsert_content_snapshot_item(
            state=state,
            provider_media_id=media_id,
            metadata=metadata,
            metrics=normalized["metrics"],
        )
        media, created = InsightsMediaSnapshot.objects.get_or_create(
            social_account=account,
            provider_media_id=media_id,
            is_deleted=False,
            defaults={
                "media_type": normalized["media_type"],
                "caption": normalized["caption"],
                "permalink": normalized["permalink"],
                "published_at": published_at,
                "api_version": INSTAGRAM_GRAPH_API_VERSION,
                "metrics": normalized["metrics"],
                "fetched_at": None,
            },
        )
        if not created:
            media.media_type = normalized["media_type"]
            media.caption = normalized["caption"]
            media.permalink = normalized["permalink"]
            media.published_at = published_at
            media.api_version = INSTAGRAM_GRAPH_API_VERSION
            # Keep the last actual metric response until fresh metrics arrive.
            media.save(update_fields=(
                "media_type", "caption", "permalink", "published_at",
                "api_version", "updated_at",
            ))

    paging = page.get("paging") if isinstance(page.get("paging"), dict) else {}
    cursors = paging.get("cursors") if isinstance(paging.get("cursors"), dict) else {}
    next_cursor = str(cursors.get("after") or "") if paging.get("next") else ""
    return eligible, next_cursor, bool(paging.get("next"))


def _metric_error_values(error):
    return _insight_error_metrics(
        source="instagram",
        labels=tuple(
            (output_name, label, provider_name)
            for output_name, provider_name, label in MEDIA_INSIGHT_SPECS
        ),
        error=error,
        permission=INSTAGRAM_INSIGHTS_PERMISSION,
    )[0]


def _parse_media_metrics(response):
    values = _insight_results(response)
    metrics = {}
    for output_name, provider_name, label in MEDIA_INSIGHT_SPECS:
        result = values.get(provider_name)
        metric_value = None
        returned = False
        if isinstance(result, dict):
            provider_values = result.get("values") or []
            if (
                provider_values
                and isinstance(provider_values[0], dict)
                and "value" in provider_values[0]
            ):
                metric_value = provider_values[0]["value"]
                returned = True
            else:
                metric_value, returned = _insight_total_value(result)
        metrics[output_name] = _metric(
            value=metric_value,
            label=label,
            source="instagram",
            period="lifetime",
            availability="available" if returned else "unavailable",
            reason="" if returned else "metric_not_returned",
            provider_metric=provider_name,
        )
    return metrics


def _metric_error_is_retryable(metrics):
    return any(
        metric.get("reason") in RETRYABLE_REASONS
        for metric in metrics.values()
        if isinstance(metric, dict)
    )


def _store_media_metrics(*, account, media_id, metrics, preserve_available=False, sync_state=None):
    with transaction.atomic(savepoint=False):
        media = InsightsMediaSnapshot.objects.select_for_update().get(
            social_account=account,
            provider_media_id=media_id,
            is_deleted=False,
        )
        merged = dict(media.metrics or {})
        updates = metrics
        if preserve_available:
            updates = {
                name: value
                for name, value in metrics.items()
                if not (
                    isinstance(value, dict)
                    and value.get("availability") != "available"
                    and isinstance(merged.get(name), dict)
                    and merged[name].get("availability") == "available"
                )
            }
        if updates:
            merged.update(updates)
            media.metrics = merged
            media.fetched_at = timezone.now()
            media.save(update_fields=("metrics", "fetched_at", "updated_at"))
        if sync_state is not None:
            item = InsightsContentSnapshotItem.objects.select_for_update().filter(
                sync_state=sync_state,
                provider_media_id=media_id,
                is_deleted=False,
            ).first()
            if item is None:
                item = InsightsContentSnapshotItem.objects.create(
                    sync_state=sync_state,
                    provider_media_id=media_id,
                    media_type=media.media_type,
                    caption=media.caption,
                    permalink=media.permalink,
                    published_at=media.published_at,
                    api_version=sync_state.api_version,
                    metrics={},
                )
            item_metrics = dict(item.metrics or {})
            item_updates = metrics
            if preserve_available:
                item_updates = {
                    name: value
                    for name, value in metrics.items()
                    if not (
                        isinstance(value, dict)
                        and value.get("availability") != "available"
                        and isinstance(item_metrics.get(name), dict)
                        and item_metrics[name].get("availability") == "available"
                    )
                }
            if item_updates:
                item_metrics.update(item_updates)
                item.metrics = item_metrics
                item.fetched_at = timezone.now()
                item.save(update_fields=("metrics", "fetched_at", "updated_at"))
        return bool(updates or (sync_state is not None and item_updates))


def _store_media_metrics_with_timing(*, timing_collector, **kwargs):
    """Time one helper call while the caller's scoped SQL wrapper is active."""
    timing_collector.set_phase("helper")
    started = time.perf_counter()
    sql_before = timing_collector.sql_total_seconds("helper")
    try:
        return _store_media_metrics(**kwargs)
    finally:
        helper_wall = time.perf_counter() - started
        helper_sql = timing_collector.sql_total_seconds("helper") - sql_before
        timing_collector.record_measurement("helper", "store_media_metrics_wall_seconds", helper_wall)
        timing_collector.record_measurement(
            "helper", "non_sql_residual", max(0.0, helper_wall - helper_sql),
        )


def _save_batch_checkpoint(claim, *, checkpoint, provider_cursor=None, **fields):
    with _fenced_stage_transaction(**claim) as (state, work):
        if work.stage != InsightsSyncWorkStage.CONTENT:
            raise StaleInsightsWorkClaim("non-content claim cannot write content checkpoint")
        state.checkpoint = checkpoint
        if provider_cursor is not None:
            state.provider_cursor = provider_cursor
        for name, value in fields.items():
            setattr(state, name, value)
        state.save(update_fields=(
            "checkpoint", "provider_cursor", *fields.keys(), "updated_at",
        ))
        return state


def _record_media_failure(
    *, claim, account, state, media_id, error_code, reason, availability,
    timings=None, timing_collector=None,
):
    failed_metrics = {
        output_name: _unavailable_metric(
            label=label,
            source="instagram",
            availability=availability,
            reason=reason,
            provider_metric=provider_name,
            period="lifetime",
        )
        for output_name, provider_name, label in MEDIA_INSIGHT_SPECS
    }
    with _fenced_stage_transaction(
        **claim, _timing_collector=timing_collector,
    ) as (locked, work):
        store_metrics = (
            _store_media_metrics_with_timing
            if timing_collector is not None
            else _store_media_metrics
        )
        store_kwargs = dict(
            account=account,
            media_id=media_id,
            metrics=failed_metrics,
            preserve_available=True,
            sync_state=locked,
        )
        if timing_collector is not None:
            store_kwargs["timing_collector"] = timing_collector
        store_metrics(**store_kwargs)
        checkpoint = dict(locked.checkpoint or {})
        checkpoint["offset"] = int(checkpoint.get("offset", 0)) + 1
        locked.checkpoint = checkpoint
        locked.items_processed += 1
        locked.error_code = locked.error_code or error_code
        locked.error_reason = locked.error_reason or reason
        checkpoint_started = time.monotonic()
        if timing_collector is not None:
            timing_collector.set_phase("checkpoint")
        locked.save(update_fields=(
            "checkpoint", "items_processed", "error_code", "error_reason", "updated_at",
        ))
        if timings is not None:
            timings["checkpoint_persistence_seconds"] += time.monotonic() - checkpoint_started


def mark_content_sync_terminal(*, claim, status, error_code, reason):
    return _finish_claimed_stage(
        claim,
        status=status,
        state_fields={"error_code": error_code[:64], "error_reason": reason[:255]},
    )


def _facebook_content_metric_unavailable(*, label, reason="metric_not_fetched"):
    return _unavailable_metric(
        label=label,
        source="facebook",
        availability="unavailable",
        reason=reason,
        period="lifetime",
    )


def _facebook_post_insight_metric(
    *, value, output_name, provider_metric, label, measurement="",
):
    metric = _metric(
        value=value,
        label=label,
        source="facebook",
        period="lifetime",
        provider_metric=provider_metric,
    )
    if measurement:
        metric["measurement"] = measurement
    return metric


def _facebook_post_insight_unavailable(
    *, output_name, provider_metric, label, reason, availability="unavailable",
    measurement="",
):
    metric = _unavailable_metric(
        label=label,
        source="facebook",
        availability=availability,
        reason=reason,
        period="lifetime",
        provider_metric=provider_metric,
    )
    if measurement:
        metric["measurement"] = measurement
    return metric


def _facebook_post_insight_shape_diagnostic(
    *, provider_metric, period, values, point, duplicate_name, classification,
):
    """Log bounded breakdown structure without provider values or unsafe keys."""
    reaction_category_keys = {"LIKE", "LOVE", "WOW", "HAHA", "SAD", "ANGRY"}
    type_labels = ("dict", "list", "numeric", "string", "null", "boolean", "other")
    max_depth = 2
    max_nodes = 500
    safe_period = period if period == "lifetime" else "unknown"
    values_is_list = isinstance(values, list)
    values_length = len(values) if values_is_list else "unknown"
    value_key_exists = isinstance(point, dict) and "value" in point
    metric_value = point.get("value") if value_key_exists else None

    if isinstance(metric_value, dict):
        value_shape = "dict"
        children = metric_value.values()
    elif isinstance(metric_value, list):
        value_shape = "list"
        children = metric_value
    elif metric_value is None:
        value_shape = "null"
        children = ()
    elif isinstance(metric_value, bool):
        value_shape = "scalar"
        children = ()
    elif isinstance(metric_value, (int, float, str)):
        value_shape = "scalar"
    else:
        value_shape = "other"

    def safe_type(value):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, dict):
            return "dict"
        if isinstance(value, list):
            return "list"
        if isinstance(value, (int, float)):
            return "numeric"
        if isinstance(value, str):
            return "string"
        return "other"

    top_level_key_count = len(metric_value) if isinstance(metric_value, dict) else 0
    def is_known_reaction_key(key):
        return isinstance(key, str) and key.upper() in reaction_category_keys

    if isinstance(metric_value, dict) and not metric_value:
        top_level_key_names = "empty"
    elif (
        provider_metric == "post_reactions_by_type_total"
        and isinstance(metric_value, dict)
        and all(is_known_reaction_key(key) for key in metric_value)
    ):
        top_level_key_names = ",".join(sorted(key.upper() for key in metric_value))
    else:
        top_level_key_names = "omitted"

    type_counts = {label: 0 for label in type_labels}
    nested_dict_count = 0
    nested_list_count = 0
    numeric_leaf_count = 0
    string_leaf_count = 0
    null_leaf_count = 0
    observed_max_depth = 0
    depth_truncated = False
    list_lengths = []
    category_keys_seen = []
    stack = []

    def push_children(children, depth):
        available_slots = max(0, max_nodes - len(stack))
        for child in children:
            if len(stack) >= available_slots:
                break
            stack.append((child, depth))

    if isinstance(metric_value, dict):
        category_keys_seen.extend(metric_value.keys())
        push_children(metric_value.values(), 1)
    elif isinstance(metric_value, list):
        list_lengths.append((0, len(metric_value)))
        push_children(metric_value, 1)

    visited = 0
    while stack and visited < max_nodes:
        child, depth = stack.pop()
        visited += 1
        observed_max_depth = max(observed_max_depth, min(depth, max_depth))
        child_type = safe_type(child)
        type_counts[child_type] += 1
        if child_type == "dict":
            nested_dict_count += 1
            category_keys_seen.extend(child.keys())
        elif child_type == "list":
            nested_list_count += 1
            list_lengths.append((depth, len(child)))
        elif child_type == "numeric":
            if not isinstance(child, bool) and (
                not isinstance(child, float) or math.isfinite(child)
            ):
                numeric_leaf_count += 1
        elif child_type == "string":
            string_leaf_count += 1
        elif child_type == "null":
            null_leaf_count += 1

        if depth < max_depth:
            if isinstance(child, dict):
                push_children(child.values(), depth + 1)
            elif isinstance(child, list):
                push_children(child, depth + 1)
        elif isinstance(child, (dict, list)) and child:
            depth_truncated = True

    if provider_metric == "post_reactions_by_type_total":
        nested_category_result = str(
            bool(category_keys_seen)
            and all(is_known_reaction_key(key) for key in category_keys_seen)
        ).lower()
    else:
        nested_category_result = "not_applicable"

    child_type_counts = ",".join(
        f"{label}={type_counts[label]}" for label in type_labels
    )
    bounded_list_lengths = ",".join(
        f"depth{depth}:{length}" for depth, length in list_lengths[:20]
    ) or "none"
    if len(list_lengths) > 20:
        bounded_list_lengths += ",truncated"
    logger.warning(
        "Facebook post Insights breakdown response shape. "
        "metric=%s period=%s values_type=%s values_is_list=%s "
        "values_length=%s value_key_exists=%s value_type=%s "
        "value_shape=%s top_level_key_count=%s top_level_key_names=%s "
        "child_type_counts=%s nested_dict_count=%s nested_list_count=%s "
        "numeric_leaf_count=%s string_leaf_count=%s null_leaf_count=%s "
        "max_depth=%s list_lengths=%s nested_keys_known_metric_categories=%s "
        "duplicate_metric_name=%s "
        "normalized_classification=%s",
        provider_metric,
        safe_period,
        safe_type(values),
        str(values_is_list).lower(),
        values_length,
        str(value_key_exists).lower(),
        safe_type(metric_value),
        value_shape,
        top_level_key_count,
        top_level_key_names,
        child_type_counts,
        nested_dict_count,
        nested_list_count,
        numeric_leaf_count,
        string_leaf_count,
        null_leaf_count,
        f"{observed_max_depth}+" if depth_truncated else observed_max_depth,
        bounded_list_lengths,
        nested_category_result,
        str(duplicate_name).lower(),
        classification,
    )


def _parse_facebook_post_insights(response):
    """Normalize the supported scalar and by-type lifetime post metrics."""
    data = response.get("data") if isinstance(response, dict) else None
    if not isinstance(data, list):
        return {
            output_name: _facebook_post_insight_unavailable(
                output_name=output_name,
                provider_metric=provider_metric,
                label=label,
                reason="malformed_insights_response",
                measurement=measurement,
            )
            for output_name, provider_metric, label, _, measurement
            in FACEBOOK_POST_INSIGHT_METRICS
        }

    entries = {}
    duplicate_names = set()
    expected_names = {spec[1] for spec in FACEBOOK_POST_INSIGHT_METRICS}
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name not in expected_names:
            continue
        if name in entries:
            duplicate_names.add(name)
        entries[name] = item

    normalized = {}
    for output_name, provider_metric, label, value_kind, measurement in FACEBOOK_POST_INSIGHT_METRICS:
        result = entries.get(provider_metric)
        reason = ""
        value = None
        values = None
        point = None
        if provider_metric in duplicate_names:
            reason = "malformed_metric_response"
        elif result is None:
            reason = "metric_not_returned"
        elif result.get("period") not in (None, "lifetime"):
            reason = "malformed_metric_response"
        else:
            values = result.get("values")
            point = values[0] if isinstance(values, list) and values else None
            if not isinstance(point, dict) or "value" not in point:
                reason = "metric_not_returned"
            else:
                value = point.get("value")
                if value_kind == "number":
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or (isinstance(value, float) and not math.isfinite(value))
                        or value < 0
                    ):
                        reason = "malformed_metric_response" if value is not None else "metric_not_returned"
                elif (
                    not isinstance(value, dict)
                    or not value
                    or any(
                        not isinstance(key, str)
                        or isinstance(count, bool)
                        or not isinstance(count, (int, float))
                        or (isinstance(count, float) and not math.isfinite(count))
                        or count < 0
                        for key, count in value.items()
                    )
                ):
                    reason = "malformed_metric_response" if value is not None else "metric_not_returned"

        if value_kind == "breakdown" and reason == "malformed_metric_response":
            diagnostic_values = (
                values if values is not None
                else result.get("values") if isinstance(result, dict)
                else None
            )
            diagnostic_point = point
            if diagnostic_point is None and isinstance(diagnostic_values, list) and diagnostic_values:
                diagnostic_point = diagnostic_values[0]
            _facebook_post_insight_shape_diagnostic(
                provider_metric=provider_metric,
                period=result.get("period") if isinstance(result, dict) else None,
                values=diagnostic_values,
                point=diagnostic_point if result is not None else None,
                duplicate_name=provider_metric in duplicate_names,
                classification=reason,
            )

        if reason:
            normalized[output_name] = _facebook_post_insight_unavailable(
                output_name=output_name,
                provider_metric=provider_metric,
                label=label,
                reason=reason,
                measurement=measurement,
            )
        else:
            normalized[output_name] = _facebook_post_insight_metric(
                value=value,
                output_name=output_name,
                provider_metric=provider_metric,
                label=label,
                measurement=measurement,
            )
    return normalized


def _merge_media_metric_values(existing, updates):
    """Merge metrics independently, retaining an available value on omission."""
    merged = dict(existing or {})
    for name, metric in (updates or {}).items():
        current = merged.get(name)
        if (
            isinstance(metric, dict)
            and metric.get("availability") != "available"
            and isinstance(current, dict)
            and current.get("availability") == "available"
        ):
            continue
        merged[name] = metric
    return merged


def _facebook_post_insight_unavailable_metrics(*, availability, reason):
    return {
        output_name: _facebook_post_insight_unavailable(
            output_name=output_name,
            provider_metric=provider_metric,
            label=label,
            availability=availability,
            reason=reason,
            measurement=measurement,
        )
        for output_name, provider_metric, label, _, measurement
        in FACEBOOK_POST_INSIGHT_METRICS
    }


def _normalize_facebook_post(item, *, since, until):
    normalized = _normalize_content_item(
        item=item,
        source="facebook",
        since=since,
        until=until,
        supports_insights=True,
        permission=FACEBOOK_INSIGHTS_PERMISSION,
    )
    metrics = normalized["metrics"]
    reactions = item.get("reactions")
    reaction_summary = reactions.get("summary") if isinstance(reactions, dict) else None
    if isinstance(reaction_summary, dict) and "total_count" in reaction_summary:
        metrics["reactions"] = _metric(
            value=reaction_summary["total_count"],
            label="Reactions",
            source="facebook",
            period="lifetime",
        )
    else:
        metrics["reactions"] = _unavailable_metric(
            label="Reactions",
            source="facebook",
            availability="unavailable",
            reason="metric_not_returned",
            period="lifetime",
        )

    # The Page /posts response does not provide these post-level measurements.
    # Keep them explicitly unavailable; do not derive them from reactions,
    # comments, or shares.
    metrics["reach"] = _facebook_content_metric_unavailable(label="Reach")
    metrics["views"] = _facebook_content_metric_unavailable(label="Views")
    metrics["engagement"] = _facebook_content_metric_unavailable(label="Engagement")
    return normalized


def _persist_facebook_posts(*, account, page, since, until, api_version, state=None):
    posts = page.get("data", [])
    if not isinstance(posts, list):
        raise MetaAPIError("Meta returned an invalid Page posts response.")

    discovered_ids = []
    seen_page_ids = set()
    fetched_at = timezone.now()
    for item in posts:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        post_id = str(item["id"])
        if post_id in seen_page_ids or not _media_is_in_range(item, since=since, until=until):
            continue
        seen_page_ids.add(post_id)
        normalized = _normalize_facebook_post(item, since=since, until=until)
        published_at = _safe_published_at(normalized.get("published_at"))
        values = {
            "media_type": normalized["media_type"],
            "caption": normalized["caption"],
            "permalink": normalized["permalink"],
            "published_at": published_at,
            "api_version": api_version,
            "metrics": normalized["metrics"],
            "fetched_at": fetched_at,
        }
        if state is not None:
            _upsert_content_snapshot_item(
                state=state,
                provider_media_id=post_id,
                metadata={field: values[field] for field in (
                    "media_type", "caption", "permalink", "published_at",
                )},
                metrics=normalized["metrics"],
            )
        media, created = InsightsMediaSnapshot.objects.get_or_create(
            social_account=account,
            provider_media_id=post_id,
            is_deleted=False,
            defaults=values,
        )
        if not created:
            values["metrics"] = _merge_media_metric_values(
                media.metrics,
                normalized["metrics"],
            )
            for field, value in values.items():
                setattr(media, field, value)
            media.save(update_fields=(*values.keys(), "updated_at"))
        discovered_ids.append(post_id)

    paging = page.get("paging") if isinstance(page.get("paging"), dict) else {}
    cursors = paging.get("cursors") if isinstance(paging.get("cursors"), dict) else {}
    has_more = bool(paging.get("next"))
    next_cursor = str(cursors.get("after") or "") if has_more else ""
    return discovered_ids, has_more, next_cursor


def _facebook_content_provider_failure(claim, error, *, social_account_id):
    availability, reason = _failure_status(error)
    _log_facebook_content_provider_error(
        claim=claim,
        social_account_id=social_account_id,
        error=error,
        classification=availability,
    )
    if reason in RETRYABLE_REASONS:
        return {"status": "retryable", "retryable": True, "error_code": reason, "reason": reason}
    if reason == "invalid_credential":
        status = InsightsSyncStatus.FAILED
        error_code = reason
        error_reason = reason
    else:
        status = InsightsSyncStatus.PARTIAL
        error_code = reason
        error_reason = FACEBOOK_CONTENT_PERMISSION if availability == "permission_required" else reason
    mark_content_sync_terminal(
        claim=claim,
        status=status,
        error_code=error_code,
        reason=error_reason,
    )
    return {"status": status, "error_code": error_code}


def _process_facebook_content_batch(*, claim, state, account):
    try:
        token = MetaCredentialService.get_access_token(social_account=account)
    except MetaIntegrationError:
        mark_content_sync_terminal(
            claim=claim,
            status=InsightsSyncStatus.FAILED,
            error_code="invalid_credential",
            reason="credential_unavailable_or_configuration_error",
        )
        return {"status": "failed", "error_code": "invalid_credential"}

    checkpoint = dict(state.checkpoint or {})
    max_pages = int(checkpoint.get("max_pages", settings.INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT))
    pages_fetched = int(checkpoint.get("pages_fetched", 0))
    continuation_count = int(checkpoint.get(AUTOMATIC_CONTENT_CONTINUATIONS_KEY, 0) or 0)
    client = _HeartbeatMetaClient(MetaAPIClient(), claim)

    # A persisted pending_media_ids key means the posts page was committed
    # before its Insights requests. Resume that bounded batch without fetching
    # the page again after a worker restart or retry.
    if "pending_media_ids" not in checkpoint:
        params = {
            "fields": (
                "id,message,created_time,permalink_url,shares,"
                "comments.limit(0).summary(true),reactions.limit(0).summary(true)"
            ),
            "limit": CONTENT_PAGE_SIZE,
        }
        if state.provider_cursor:
            params["after"] = state.provider_cursor
        try:
            page = client.get(
                f"/{account.platform_account_id}/posts",
                access_token=token,
                params=params,
            )
        except MetaAPIError as exc:
            return _facebook_content_provider_failure(
                claim,
                exc,
                social_account_id=account.id,
            )

        with _fenced_stage_transaction(**claim) as (locked, work):
            discovered_ids, has_more, next_cursor = _persist_facebook_posts(
                account=account,
                page=page,
                since=state.since,
                until=state.until,
                api_version=settings.META_GRAPH_API_VERSION,
                state=locked,
            )
            current_checkpoint = dict(locked.checkpoint or {})
            previously_discovered = current_checkpoint.get("discovered_post_ids", [])
            if not isinstance(previously_discovered, list):
                previously_discovered = []
            seen_ids = {str(post_id) for post_id in previously_discovered}
            new_discovered_ids = [post_id for post_id in discovered_ids if post_id not in seen_ids]
            pages_fetched = int(current_checkpoint.get("pages_fetched", 0)) + 1
            checkpoint = {
                **current_checkpoint,
                "pending_media_ids": new_discovered_ids,
                "offset": 0,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "pages_fetched": pages_fetched,
                "max_pages": max_pages,
                AUTOMATIC_CONTENT_CONTINUATIONS_KEY: continuation_count,
                "discovered_post_ids": list(dict.fromkeys(
                    [str(post_id) for post_id in previously_discovered] + new_discovered_ids
                )),
            }
            locked.content_status = InsightsSyncStatus.SYNCING
            locked.started_at = locked.started_at or timezone.now()
            locked.items_discovered += len(new_discovered_ids)
            # A discovered count is not a final total while the provider has
            # another page. Keep an already-known bounded total monotonic for
            # an attempt resuming after the existing traversal ceiling.
            if locked.items_total is not None or not has_more:
                locked.items_total = max(
                    locked.items_total or 0,
                    locked.items_discovered,
                )
            locked.checkpoint = checkpoint
            locked.provider_cursor = next_cursor if has_more and next_cursor else ""
            _aggregate_overall_status(locked)
            locked.save(update_fields=(
                "status", "content_status", "started_at", "completed_at",
                "items_discovered", "items_total", "checkpoint", "provider_cursor",
                "updated_at",
            ))
            state = locked
        checkpoint = dict(state.checkpoint or {})

    pending_ids = checkpoint.get("pending_media_ids", [])
    if not isinstance(pending_ids, list):
        pending_ids = []
    offset = int(checkpoint.get("offset", 0))
    processed_this_run = 0

    while offset < len(pending_ids) and processed_this_run < CONTENT_INSIGHTS_BATCH_SIZE:
        media_id = str(pending_ids[offset])
        provider_error_reason = ""
        try:
            response = client.get(
                f"/{media_id}/insights",
                access_token=token,
                params={
                    "metric": FACEBOOK_POST_INSIGHTS_METRIC_PARAM,
                    "period": "lifetime",
                },
            )
            metric_values = _parse_facebook_post_insights(response)
        except MetaAPIError as exc:
            availability, reason = _failure_status(exc)
            if reason == "invalid_credential":
                mark_content_sync_terminal(
                    claim=claim,
                    status=InsightsSyncStatus.FAILED,
                    error_code=reason,
                    reason=reason,
                )
                return {"status": InsightsSyncStatus.FAILED, "error_code": reason}
            if reason in RETRYABLE_REASONS:
                return {
                    "status": "retryable",
                    "retryable": True,
                    "error_code": reason,
                    "reason": reason,
                    "availability": availability,
                    "media_id": media_id,
                }
            provider_error_reason = reason
            metric_values = _facebook_post_insight_unavailable_metrics(
                availability=availability,
                reason=(
                    FACEBOOK_INSIGHTS_PERMISSION
                    if availability == "permission_required"
                    else reason
                ),
            )

        metric_incomplete = any(
            not isinstance(metric_values.get(output_name), dict)
            or metric_values[output_name].get("availability") != "available"
            for output_name in FACEBOOK_REQUIRED_POST_INSIGHT_OUTPUTS
        )
        attempt_error_code = (
            provider_error_reason or ("metric_unavailable" if metric_incomplete else "")
        )
        attempt_error_reason = (
            FACEBOOK_INSIGHTS_PERMISSION
            if provider_error_reason == "permission_required"
            else (
                provider_error_reason
                or ("one_or_more_post_insights_metrics_unavailable" if metric_incomplete else "")
            )
        )
        with _fenced_stage_transaction(**claim) as (locked, work):
            _store_media_metrics(
                account=account,
                media_id=media_id,
                metrics=metric_values,
                preserve_available=True,
                sync_state=locked,
            )
            current_checkpoint = dict(locked.checkpoint or {})
            current_offset = int(current_checkpoint.get("offset", offset))
            current_checkpoint["offset"] = current_offset + 1
            locked.checkpoint = current_checkpoint
            locked.items_processed += 1
            if attempt_error_code and not locked.error_code:
                locked.error_code = attempt_error_code
                locked.error_reason = attempt_error_reason
            _aggregate_overall_status(locked)
            locked.save(update_fields=(
                "checkpoint", "items_processed", "error_code", "error_reason",
                "status", "updated_at",
            ))
            state = locked
        offset += 1
        processed_this_run += 1

    state.refresh_from_db()
    checkpoint = dict(state.checkpoint or {})
    pending_ids = checkpoint.get("pending_media_ids", [])
    offset = int(checkpoint.get("offset", 0))
    has_more = bool(checkpoint.get("has_more"))
    next_cursor = str(checkpoint.get("next_cursor") or "")
    pages_fetched = int(checkpoint.get("pages_fetched", 0))
    discovered_count = state.items_discovered

    if offset < len(pending_ids):
        rearm_claimed_work(
            claim,
            provider_retry_count=0,
            stage_status=InsightsSyncStatus.SYNCING,
        )
        return {
            "status": InsightsSyncStatus.SYNCING,
            "continue": True,
            "processed": processed_this_run,
        }

    if has_more and not next_cursor:
        return _finish_unusable_content_pagination(
            claim,
            processed=processed_this_run,
        )
    if has_more and next_cursor and pages_fetched >= max_pages:
        checkpoint["stop_reason"] = "page_ceiling_reached"
        checkpoint.pop("pending_media_ids", None)
        checkpoint.pop("offset", None)
        return _continue_content_after_page_ceiling(
            claim,
            checkpoint=checkpoint,
            next_cursor=next_cursor,
            items_total=discovered_count,
            processed=processed_this_run,
        )
    if has_more and next_cursor:
        checkpoint.pop("pending_media_ids", None)
        checkpoint.pop("offset", None)
        rearm_claimed_work(
            claim,
            provider_retry_count=0,
            stage_status=InsightsSyncStatus.SYNCING,
            state_fields={
                "checkpoint": checkpoint,
                "provider_cursor": next_cursor,
            },
        )
        return {
            "status": InsightsSyncStatus.SYNCING,
            "continue": True,
            "processed": processed_this_run,
        }

    final_status = (
        InsightsSyncStatus.PARTIAL
        if state.error_code
        else InsightsSyncStatus.COMPLETE
    )
    state = _finish_claimed_stage(
        claim,
        status=final_status,
        state_fields={
            "checkpoint": {},
            "provider_cursor": "",
            "items_total": discovered_count,
        },
    )
    return {
        "status": state.status,
        "content_status": state.content_status,
        "processed": processed_this_run,
        "items_processed": state.items_processed,
        "items_total": state.items_discovered,
    }


def process_content_sync_batch(*, claim):
    """Run bounded content work, coalescing empty Instagram pages safely."""
    service_started = time.monotonic()
    state = InsightsSyncState.objects.select_related("social_account").filter(id=claim["sync_state_id"], is_deleted=False).first()
    if state is None:
        return {"status": "not_found"}
    account = state.social_account
    if not _account_is_syncable(account):
        mark_content_sync_terminal(claim=claim, status=InsightsSyncStatus.FAILED, error_code="account_unavailable", reason="account_not_connected_or_invalid")
        if account.platform == SocialPlatform.INSTAGRAM:
            _log_instagram_content_event(
                "BATCH_END", claim=claim, account=account, state=state,
                outcome="terminal_failure", processed_count=0,
                discovered_count=state.items_discovered, total=state.items_total,
                total_duration_seconds=time.monotonic() - service_started,
            )
        return {"status": InsightsSyncStatus.FAILED, "error_code": "account_unavailable"}
    if account.platform == SocialPlatform.FACEBOOK:
        return _process_facebook_content_batch(claim=claim, state=state, account=account)
    credential = get_active_instagram_credential(social_account=account)
    if credential is None:
        mark_content_sync_terminal(claim=claim, status=InsightsSyncStatus.FAILED, error_code="invalid_credential", reason="credential_unavailable")
        _log_instagram_content_event(
            "BATCH_END", claim=claim, account=account, state=state,
            outcome="terminal_failure", processed_count=0,
            discovered_count=state.items_discovered, total=state.items_total,
            total_duration_seconds=time.monotonic() - service_started,
        )
        return {"status": "failed", "error_code": "invalid_credential"}
    try:
        token = decrypt_token(credential.encrypted_access_token)
        client = _HeartbeatInstagramClient(InstagramAPIClient(), claim)
    except (InstagramIntegrationError, InstagramOAuthConfigurationError):
        mark_content_sync_terminal(claim=claim, status=InsightsSyncStatus.FAILED, error_code="invalid_credential", reason="credential_or_provider_configuration_unavailable")
        _log_instagram_content_event(
            "BATCH_END", claim=claim, account=account, state=state,
            outcome="terminal_failure", processed_count=0,
            discovered_count=state.items_discovered, total=state.items_total,
            total_duration_seconds=time.monotonic() - service_started,
        )
        return {"status": "failed", "error_code": "invalid_credential"}
    since, until = state.since, state.until
    timings = {
        "provider_page_operation_seconds": 0.0,
        "provider_http_seconds": 0.0,
        "provider_response_parse_seconds": 0.0,
        "pacer_wait_seconds": 0.0,
        "page_persist_filter_seconds": 0.0,
        "page_transaction_seconds": 0.0,
        "metrics_operation_seconds": 0.0,
        "metrics_http_seconds": 0.0,
        "metrics_response_parse_seconds": 0.0,
        "metrics_values_parse_seconds": 0.0,
        "metrics_persistence_seconds": 0.0,
        "checkpoint_persistence_seconds": 0.0,
        "continuation_decision_seconds": 0.0,
    }
    metrics_request_count = 0
    metrics_failed_count = 0
    metrics_http_seconds = 0.0
    metrics_pacer_seconds = 0.0
    metrics_max_http_seconds = 0.0
    metrics_statuses = {}
    page_eligible_count = None
    checkpoint_write_count = 0
    initial_processed_count = state.items_processed

    def finish_batch(result, outcome, *, processed_count=None):
        latest_checkpoint = dict(state.checkpoint or {})
        if page_eligible_count is None:
            eligible_count = len(latest_checkpoint.get("pending_media_ids", []))
        else:
            eligible_count = page_eligible_count
        processed = (
            max(0, state.items_processed - initial_processed_count)
            if processed_count is None
            else processed_count
        )
        has_more = bool(latest_checkpoint.get("has_more"))
        cursor_present = bool(
            latest_checkpoint.get("next_cursor") or state.provider_cursor
        )
        _log_instagram_content_event(
            "BATCH_END", claim=claim, account=account, state=state,
            outcome=outcome, status=(result or {}).get("status", "unknown"),
            processed_count=processed,
            discovered_count=state.items_discovered, total=state.items_total,
            eligible_count=eligible_count, has_more=has_more,
            cursor_present=cursor_present,
            continue_work=bool((result or {}).get("continue")),
            total_duration_seconds=time.monotonic() - service_started,
        )
        _log_instagram_content_event(
            "BATCH_TIMINGS", claim=claim, account=account, state=state,
            level="debug", **timings,
        )
        if metrics_request_count:
            _log_instagram_content_event(
                "METRICS", claim=claim, account=account, state=state,
                level="debug", operation="instagram_media_insights",
                request_count=metrics_request_count,
                failed_count=metrics_failed_count,
                duration_seconds=round(timings["metrics_operation_seconds"], 6),
                http_duration_seconds=round(metrics_http_seconds, 6),
                max_http_duration_seconds=round(metrics_max_http_seconds, 6),
                response_parse_seconds=round(timings["metrics_response_parse_seconds"], 6),
                pacing_wait_seconds=round(metrics_pacer_seconds, 6),
                http_statuses=",".join(
                    f"{status}:{count}" for status, count in sorted(metrics_statuses.items())
                ) or "none",
            )
        return result

    _log_instagram_content_event(
        "BATCH_START", claim=claim, account=account, state=state,
        outcome="started", discovered_count=state.items_discovered,
        processed_count=0, total=state.items_total,
    )
    checkpoint = dict(state.checkpoint or {})
    max_pages = int(checkpoint["max_pages"] if "max_pages" in checkpoint else settings.INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT)
    pages_fetched = int(checkpoint.get("pages_fetched", 0))
    checkpoint["max_pages"] = max_pages
    checkpoint["pages_fetched"] = pages_fetched
    if (state.checkpoint or {}).get("max_pages") != max_pages or (state.checkpoint or {}).get("pages_fetched") != pages_fetched:
        checkpoint_started = time.monotonic()
        state = _save_batch_checkpoint(claim, checkpoint=checkpoint)
        checkpoint_elapsed = time.monotonic() - checkpoint_started
        timings["checkpoint_persistence_seconds"] += checkpoint_elapsed
        checkpoint_write_count += 1
        _log_instagram_content_event(
            "CHECKPOINT", claim=claim, account=account, state=state,
            level="debug", duration_seconds=round(checkpoint_elapsed, 6),
            write_count=checkpoint_write_count,
        )
    if not checkpoint.get("pending_media_ids"):
        while True:
            if pages_fetched >= max_pages:
                checkpoint["stop_reason"] = "page_ceiling_reached"
                next_cursor = str(checkpoint.get("next_cursor") or "")
                if checkpoint.get("has_more") is True:
                    if not next_cursor:
                        result = _finish_unusable_content_pagination(claim)
                        return finish_batch(result, "terminal_failure")
                    if not state.error_code:
                        continuation_started = time.monotonic()
                        result = _continue_content_after_page_ceiling(
                            claim,
                            checkpoint=checkpoint,
                            items_total=state.items_discovered,
                            next_cursor=next_cursor,
                        )
                        continuation_elapsed = time.monotonic() - continuation_started
                        timings["continuation_decision_seconds"] += continuation_elapsed
                        timings["checkpoint_persistence_seconds"] += continuation_elapsed
                        if not result.get("continue"):
                            return finish_batch(result, "terminal_failure")
                        outcome = (
                            "zero_eligible_with_more_pages"
                            if state.items_discovered == 0
                            and state.items_processed == initial_processed_count
                            else "processed_work"
                        )
                        return finish_batch(result, outcome)
                result = _complete_content_partial(claim, checkpoint=checkpoint, items_total=state.items_discovered)
                return finish_batch(result, "terminal_failure")
            params = {"fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count", "limit": CONTENT_PAGE_SIZE}
            checkpoint_cursor = checkpoint.get("next_cursor")
            page_cursor = (
                checkpoint_cursor
                if checkpoint.get("has_more") and checkpoint_cursor
                else state.provider_cursor
            )
            if page_cursor:
                params["after"] = page_cursor
            provider_page_started = time.monotonic()
            try:
                page = _instagram_graph_get(client, f"{account.platform_account_id}/media", access_token=token, params=params)
            except InstagramAPIError as exc:
                provider_elapsed = time.monotonic() - provider_page_started
                timings["provider_page_operation_seconds"] += provider_elapsed
                timings["provider_http_seconds"] += _instagram_client_timing(
                    client, "last_http_duration_seconds",
                )
                timings["provider_response_parse_seconds"] += _instagram_client_timing(
                    client, "last_response_parse_duration_seconds",
                )
                timings["pacer_wait_seconds"] += _instagram_client_timing(
                    client, "last_pacer_wait_seconds",
                )
                _, reason = _failure_status(exc)
                if reason in RETRYABLE_REASONS:
                    result = {"status": "retryable", "retryable": True, "error_code": reason, "reason": reason}
                    return finish_batch(result, "retryable_failure")
                status = InsightsSyncStatus.FAILED if reason == "invalid_credential" else InsightsSyncStatus.PARTIAL
                mark_content_sync_terminal(claim=claim, status=status, error_code=reason, reason=reason)
                result = {"status": status, "error_code": reason}
                return finish_batch(result, "terminal_failure")
            provider_elapsed = time.monotonic() - provider_page_started
            timings["provider_page_operation_seconds"] += provider_elapsed
            page_http_elapsed = _instagram_client_timing(
                client, "last_http_duration_seconds",
            )
            page_parse_elapsed = _instagram_client_timing(
                client, "last_response_parse_duration_seconds",
            )
            page_pacer_elapsed = _instagram_client_timing(
                client, "last_pacer_wait_seconds",
            )
            page_http_status = getattr(
                getattr(client, "_client", None),
                "last_http_status_code",
                None,
            )
            timings["provider_http_seconds"] += page_http_elapsed
            timings["provider_response_parse_seconds"] += page_parse_elapsed
            timings["pacer_wait_seconds"] += page_pacer_elapsed
            _log_instagram_content_event(
                "PROVIDER_PAGE", claim=claim, account=account, state=state,
                level="info", operation="instagram_media_list",
                duration_seconds=round(provider_elapsed, 6),
                http_duration_seconds=round(page_http_elapsed, 6),
                response_parse_seconds=round(page_parse_elapsed, 6),
                pacer_wait_seconds=round(page_pacer_elapsed, 6),
                http_status=page_http_status or "unavailable",
            )
            page_transaction_started = time.monotonic()
            with _fenced_stage_transaction(**claim) as (locked, work):
                page_persist_started = time.monotonic()
                eligible_ids, next_cursor, has_more = _persist_media_page(state=locked, account=account, page=page, since=since, until=until)
                page_persist_elapsed = time.monotonic() - page_persist_started
                timings["page_persist_filter_seconds"] += page_persist_elapsed
                page_eligible_count = len(eligible_ids)
                continuation_count = int(
                    checkpoint.get(AUTOMATIC_CONTENT_CONTINUATIONS_KEY, 0) or 0
                )
                checkpoint = {
                    "pending_media_ids": eligible_ids,
                    "offset": 0,
                    "next_cursor": next_cursor,
                    "has_more": has_more,
                    "pages_fetched": pages_fetched + 1,
                    "max_pages": max_pages,
                    AUTOMATIC_CONTENT_CONTINUATIONS_KEY: continuation_count,
                }
                locked.content_status = InsightsSyncStatus.SYNCING
                locked.started_at = locked.started_at or timezone.now()
                locked.items_discovered += len(eligible_ids)
                if locked.items_total is not None or not has_more:
                    locked.items_total = max(locked.items_total or 0, locked.items_discovered)
                locked.checkpoint = checkpoint
                _aggregate_overall_status(locked)
                checkpoint_started = time.monotonic()
                locked.save(update_fields=("status", "content_status", "started_at", "completed_at", "items_discovered", "items_total", "checkpoint", "updated_at"))
                checkpoint_elapsed = time.monotonic() - checkpoint_started
                timings["checkpoint_persistence_seconds"] += checkpoint_elapsed
                checkpoint_write_count += 1
                state = locked
            page_transaction_elapsed = time.monotonic() - page_transaction_started
            timings["page_transaction_seconds"] += page_transaction_elapsed
            pages_fetched = int(checkpoint["pages_fetched"])
            _log_instagram_content_event(
                "PAGE_PERSIST", claim=claim, account=account, state=state,
                level="info", eligible_count=page_eligible_count,
                eligible_media=bool(page_eligible_count),
                discovered_count=state.items_discovered, total=state.items_total,
                processed_count=0,
                has_more=has_more, cursor_present=bool(next_cursor),
                duration_seconds=round(page_persist_elapsed, 6),
                transaction_duration_seconds=round(page_transaction_elapsed, 6),
                checkpoint_duration_seconds=round(checkpoint_elapsed, 6),
            )
            if page_eligible_count or not has_more or not next_cursor or pages_fetched >= max_pages:
                break
    pending_ids = checkpoint.get("pending_media_ids", [])
    offset = int(checkpoint.get("offset", 0))
    processed_this_run = 0
    partial = bool(state.error_code)
    while offset < len(pending_ids) and processed_this_run < CONTENT_INSIGHTS_BATCH_SIZE:
        media_id = str(pending_ids[offset])
        metric_operation_started = time.monotonic()
        metrics_request_count += 1
        try:
            response = _instagram_graph_get(client, f"{media_id}/insights", access_token=token, params={"metric": "reach,views,shares,saved,total_interactions"})
            metric_parse_started = time.monotonic()
            metric_values = _parse_media_metrics(response)
            timings["metrics_values_parse_seconds"] += time.monotonic() - metric_parse_started
        except InstagramAPIError as exc:
            metric_operation_elapsed = time.monotonic() - metric_operation_started
            timings["metrics_operation_seconds"] += metric_operation_elapsed
            metrics_failed_count += 1
            metric_http_elapsed = _instagram_client_timing(
                client, "last_http_duration_seconds",
            )
            metric_pacer_elapsed = _instagram_client_timing(
                client, "last_pacer_wait_seconds",
            )
            metric_response_parse_elapsed = _instagram_client_timing(
                client, "last_response_parse_duration_seconds",
            )
            metrics_http_seconds += metric_http_elapsed
            metrics_pacer_seconds += metric_pacer_elapsed
            timings["metrics_http_seconds"] += metric_http_elapsed
            timings["metrics_response_parse_seconds"] += metric_response_parse_elapsed
            timings["pacer_wait_seconds"] += metric_pacer_elapsed
            metrics_max_http_seconds = max(metrics_max_http_seconds, metric_http_elapsed)
            metric_status = getattr(
                getattr(client, "_client", None),
                "last_http_status_code",
                None,
            )
            status_key = str(metric_status or "unavailable")
            metrics_statuses[status_key] = metrics_statuses.get(status_key, 0) + 1
            availability, reason = _failure_status(exc)
            if reason in RETRYABLE_REASONS:
                result = {"status": "retryable", "retryable": True, "error_code": reason, "reason": reason, "media_id": media_id}
                return finish_batch(result, "retryable_failure", processed_count=processed_this_run)
            if reason == "invalid_credential":
                mark_content_sync_terminal(claim=claim, status=InsightsSyncStatus.FAILED, error_code=reason, reason=reason)
                result = {"status": InsightsSyncStatus.FAILED, "error_code": reason}
                return finish_batch(result, "terminal_failure", processed_count=processed_this_run)
            partial = True
            metric_persist_started = time.monotonic()
            failure_timing_collector = _InsightsSqlTimingCollector()
            _record_media_failure(
                claim=claim, account=account, state=state, media_id=media_id,
                error_code=reason, reason=reason, availability=availability,
                timings=timings, timing_collector=failure_timing_collector,
            )
            timings["metrics_persistence_seconds"] += time.monotonic() - metric_persist_started
            offset += 1
            state.refresh_from_db()
            checkpoint = dict(state.checkpoint or {})
            pending_ids = checkpoint.get("pending_media_ids", [])
            processed_this_run += 1
            continue
        else:
            metric_operation_elapsed = time.monotonic() - metric_operation_started
            timings["metrics_operation_seconds"] += metric_operation_elapsed
            metric_http_elapsed = _instagram_client_timing(
                client, "last_http_duration_seconds",
            )
            metric_pacer_elapsed = _instagram_client_timing(
                client, "last_pacer_wait_seconds",
            )
            metric_response_parse_elapsed = _instagram_client_timing(
                client, "last_response_parse_duration_seconds",
            )
            metrics_http_seconds += metric_http_elapsed
            metrics_pacer_seconds += metric_pacer_elapsed
            timings["metrics_http_seconds"] += metric_http_elapsed
            timings["metrics_response_parse_seconds"] += metric_response_parse_elapsed
            timings["pacer_wait_seconds"] += metric_pacer_elapsed
            metrics_max_http_seconds = max(metrics_max_http_seconds, metric_http_elapsed)
            metric_status = getattr(
                getattr(client, "_client", None),
                "last_http_status_code",
                None,
            )
            status_key = str(metric_status or "unavailable")
            metrics_statuses[status_key] = metrics_statuses.get(status_key, 0) + 1
        unavailable = any(metric.get("availability") != "available" for metric in metric_values.values())
        partial = partial or unavailable
        metric_persist_started = time.monotonic()
        post_timing_collector = _InsightsSqlTimingCollector()
        with _fenced_stage_transaction(
            **claim, _timing_collector=post_timing_collector,
        ) as (locked, work):
            _store_media_metrics_with_timing(
                timing_collector=post_timing_collector,
                account=account,
                media_id=media_id,
                metrics=metric_values,
                preserve_available=unavailable,
                sync_state=locked,
            )
            current_checkpoint = dict(locked.checkpoint or {})
            current_checkpoint["offset"] = int(current_checkpoint.get("offset", offset)) + 1
            locked.checkpoint = current_checkpoint
            locked.items_processed += 1
            if unavailable and not locked.error_code:
                locked.error_code = "metric_unavailable"
                locked.error_reason = "one_or_more_media_metrics_unavailable"
            checkpoint_started = time.monotonic()
            post_timing_collector.set_phase("checkpoint")
            locked.save(update_fields=("checkpoint", "items_processed", "error_code", "error_reason", "updated_at"))
            checkpoint_elapsed = time.monotonic() - checkpoint_started
            timings["checkpoint_persistence_seconds"] += checkpoint_elapsed
            checkpoint_write_count += 1
            state = locked
        timings["metrics_persistence_seconds"] += time.monotonic() - metric_persist_started
        offset += 1
        processed_this_run += 1
    checkpoint = dict(state.checkpoint or {})
    pending_ids = checkpoint.get("pending_media_ids", [])
    offset = int(checkpoint.get("offset", 0))
    continuation_started = time.monotonic()
    if offset < len(pending_ids):
        if checkpoint.get("has_more") and int(checkpoint.get("pages_fetched", 0)) >= max_pages:
            checkpoint["stop_reason"] = "page_ceiling_reached"
            if not checkpoint.get("next_cursor"):
                result = _finish_unusable_content_pagination(
                    claim,
                    processed=processed_this_run,
                )
                timings["continuation_decision_seconds"] += time.monotonic() - continuation_started
                return finish_batch(result, "terminal_failure", processed_count=processed_this_run)
            if not state.error_code:
                result = _continue_content_after_page_ceiling(
                    claim,
                    checkpoint=checkpoint,
                    items_total=state.items_discovered,
                    processed=processed_this_run,
                )
                continuation_elapsed = time.monotonic() - continuation_started
                timings["continuation_decision_seconds"] += continuation_elapsed
                timings["checkpoint_persistence_seconds"] += continuation_elapsed
                return finish_batch(result, "processed_work", processed_count=processed_this_run)
            result = _complete_content_partial(claim, checkpoint=checkpoint, items_total=state.items_discovered, processed=processed_this_run)
            continuation_elapsed = time.monotonic() - continuation_started
            timings["continuation_decision_seconds"] += continuation_elapsed
            timings["checkpoint_persistence_seconds"] += continuation_elapsed
            return finish_batch(result, "terminal_failure", processed_count=processed_this_run)
        rearm_started = time.monotonic()
        rearm_claimed_work(claim, provider_retry_count=0)
        rearm_elapsed = time.monotonic() - rearm_started
        timings["continuation_decision_seconds"] += time.monotonic() - continuation_started
        timings["checkpoint_persistence_seconds"] += rearm_elapsed
        result = {"status": "syncing", "continue": True, "processed": processed_this_run}
        outcome = "processed_work" if processed_this_run else "zero_eligible_with_more_pages" if page_eligible_count == 0 and checkpoint.get("has_more") else "processed_work"
        return finish_batch(result, outcome, processed_count=processed_this_run)
    next_cursor = str(checkpoint.get("next_cursor") or "")
    has_more = bool(checkpoint.get("has_more"))
    if has_more and not next_cursor:
        result = _finish_unusable_content_pagination(
            claim,
            processed=processed_this_run,
        )
        timings["continuation_decision_seconds"] += time.monotonic() - continuation_started
        return finish_batch(result, "terminal_failure", processed_count=processed_this_run)
    if has_more and next_cursor:
        if int(checkpoint.get("pages_fetched", 0)) >= max_pages:
            if state.error_code:
                checkpoint["stop_reason"] = "page_ceiling_reached"
                result = _complete_content_partial(
                    claim,
                    checkpoint=checkpoint,
                    provider_cursor=next_cursor,
                    items_total=state.items_discovered,
                    processed=processed_this_run,
                )
                continuation_elapsed = time.monotonic() - continuation_started
                timings["continuation_decision_seconds"] += continuation_elapsed
                timings["checkpoint_persistence_seconds"] += continuation_elapsed
                return finish_batch(result, "terminal_failure", processed_count=processed_this_run)
            checkpoint["stop_reason"] = "page_ceiling_reached"
            result = _continue_content_after_page_ceiling(
                claim,
                checkpoint=checkpoint,
                next_cursor=next_cursor,
                items_total=state.items_discovered,
                processed=processed_this_run,
            )
            continuation_elapsed = time.monotonic() - continuation_started
            timings["continuation_decision_seconds"] += continuation_elapsed
            timings["checkpoint_persistence_seconds"] += continuation_elapsed
            outcome = "processed_work" if processed_this_run else "zero_eligible_with_more_pages" if page_eligible_count == 0 else "processed_work"
            if not result.get("continue"):
                outcome = "terminal_failure"
            return finish_batch(result, outcome, processed_count=processed_this_run)
        next_checkpoint = {
            key: value
            for key, value in checkpoint.items()
            if key == AUTOMATIC_CONTENT_CONTINUATIONS_KEY
        }
        next_checkpoint.update({"pages_fetched": int(checkpoint.get("pages_fetched", 0)), "max_pages": max_pages})
        rearm_started = time.monotonic()
        rearm_claimed_work(claim, provider_retry_count=0, state_fields={"checkpoint": next_checkpoint, "provider_cursor": next_cursor})
        rearm_elapsed = time.monotonic() - rearm_started
        timings["continuation_decision_seconds"] += time.monotonic() - continuation_started
        timings["checkpoint_persistence_seconds"] += rearm_elapsed
        result = {"status": "syncing", "continue": True, "processed": processed_this_run}
        outcome = "processed_work" if processed_this_run else "zero_eligible_with_more_pages" if page_eligible_count == 0 else "processed_work"
        return finish_batch(result, outcome, processed_count=processed_this_run)
    state.refresh_from_db()
    content_status = InsightsSyncStatus.PARTIAL if partial or state.error_code else InsightsSyncStatus.COMPLETE
    fields = {"items_total": state.items_discovered}
    if content_status == InsightsSyncStatus.COMPLETE:
        fields.update({"checkpoint": {}, "provider_cursor": ""})
    completion_started = time.monotonic()
    _finish_claimed_stage(claim, status=content_status, state_fields=fields)
    completion_elapsed = time.monotonic() - completion_started
    timings["checkpoint_persistence_seconds"] += completion_elapsed
    timings["continuation_decision_seconds"] += time.monotonic() - continuation_started
    state.refresh_from_db()
    result = {"status": state.status, "content_status": state.content_status, "processed": processed_this_run, "items_processed": state.items_processed, "items_total": state.items_discovered}
    outcome = "zero_eligible_final_page" if processed_this_run == 0 and page_eligible_count == 0 and not has_more else "complete" if content_status == InsightsSyncStatus.COMPLETE else "terminal_failure"
    return finish_batch(result, outcome, processed_count=processed_this_run)


def _complete_content_partial(claim, *, checkpoint, items_total, provider_cursor=None, processed=None):
    fields = {"checkpoint": checkpoint, "items_total": items_total}
    if provider_cursor is not None:
        fields["provider_cursor"] = provider_cursor
    state = _finish_claimed_stage(claim, status=InsightsSyncStatus.PARTIAL, state_fields=fields)
    result = {"status": state.status, "content_status": state.content_status}
    if processed is not None:
        result["processed"] = processed
    return result


def _continue_content_after_page_ceiling(
    claim,
    *,
    checkpoint,
    items_total,
    next_cursor=None,
    processed=None,
):
    """Re-arm a confirmed page continuation within a durable attempt budget."""
    continuation_count = int(
        checkpoint.get(AUTOMATIC_CONTENT_CONTINUATIONS_KEY, 0) or 0
    )
    if continuation_count >= settings.INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT:
        checkpoint["stop_reason"] = "automatic_continuation_budget_reached"
        return _complete_content_partial(
            claim,
            checkpoint=checkpoint,
            items_total=items_total,
            provider_cursor=next_cursor,
            processed=processed,
        )

    continuation_count += 1
    checkpoint[AUTOMATIC_CONTENT_CONTINUATIONS_KEY] = continuation_count
    checkpoint["pages_fetched"] = 0
    checkpoint.pop("max_pages", None)
    checkpoint.pop("stop_reason", None)

    state_fields = {
        "checkpoint": checkpoint,
        "items_total": items_total,
    }
    if next_cursor is not None:
        state_fields["provider_cursor"] = next_cursor
    rearm_claimed_work(
        claim,
        provider_retry_count=0,
        state_fields=state_fields,
        stage_status=InsightsSyncStatus.SYNCING,
    )
    result = {"status": InsightsSyncStatus.SYNCING, "continue": True}
    if processed is not None:
        result["processed"] = processed
    return result


def _finish_unusable_content_pagination(claim, *, processed=None):
    state = _finish_claimed_stage(
        claim,
        status=InsightsSyncStatus.PARTIAL,
        state_fields={
            "error_code": "pagination_unavailable",
            "error_reason": "provider_pagination_cursor_unavailable",
        },
    )
    result = {"status": state.status, "content_status": state.content_status}
    if processed is not None:
        result["processed"] = processed
    return result


def handle_retryable_stage_result(claim, result):
    """Persist bounded provider retries in the work row instead of Celery metadata."""
    media_id = result.get("media_id")
    error_code = (result.get("error_code") or "provider_temporary_error")[:64]
    reason = (result.get("reason") or error_code)[:255]
    with _fenced_stage_transaction(**claim) as (state, work):
        retry_count = work.provider_retry_count
        if retry_count < 3:
            delay = min(30 * (2 ** retry_count), 5 * 60)
            work.provider_retry_count = retry_count + 1
            work.status = InsightsSyncWorkStatus.PENDING
            _clear_work_claim(work)
            work.dispatch_expires_at = None
            work.celery_task_id = ""
            work.next_attempt_at = timezone.now() + timedelta(seconds=delay)
            work.last_error_code = error_code
            work.last_error_reason = reason
            work.save()
            return {"status": "retrying", "retry_at": work.next_attempt_at.isoformat()}

        if work.stage == InsightsSyncWorkStage.ACCOUNT:
            state.account_status = InsightsSyncStatus.FAILED
            state.account_error_code = error_code
            state.account_error_reason = "account_metrics_retry_limit_reached"
            state.account_completed_at = timezone.now()
            final_status = InsightsSyncStatus.FAILED
        elif (
            work.stage == InsightsSyncWorkStage.CONTENT
            and media_id
            and state.social_account.platform == SocialPlatform.FACEBOOK
        ):
            # Exhaustion for one Facebook post is terminal for that post, not
            # for the entire durable content stage. Preserve any existing
            # available values while recording unavailable results, then
            # continue from the post checkpoint so later posts are attempted.
            unavailable_metrics = _facebook_post_insight_unavailable_metrics(
                availability="provider_error",
                reason=error_code,
            )
            _store_media_metrics(
                account=state.social_account,
                media_id=media_id,
                metrics=unavailable_metrics,
                preserve_available=True,
                sync_state=state,
            )
            checkpoint = dict(state.checkpoint or {})
            checkpoint["offset"] = int(checkpoint.get("offset", 0)) + 1
            state.checkpoint = checkpoint
            state.items_processed += 1
            state.content_status = InsightsSyncStatus.SYNCING
            state.error_code = state.error_code or error_code
            state.error_reason = state.error_reason or reason
            _aggregate_overall_status(state)
            state.save(update_fields=(
                "checkpoint", "items_processed", "content_status", "error_code",
                "error_reason", "status", "updated_at",
            ))
            rearm_claimed_work(
                claim,
                provider_retry_count=0,
                stage_status=InsightsSyncStatus.SYNCING,
            )
            return {
                "status": InsightsSyncStatus.SYNCING,
                "continue": True,
                "processed": 1,
                "error_code": error_code,
            }
        else:
            if media_id:
                failed_metrics = {
                    output_name: _unavailable_metric(
                        label=label, source="instagram", availability="provider_error",
                        reason=reason, provider_metric=provider_name, period="lifetime",
                    )
                    for output_name, provider_name, label in MEDIA_INSIGHT_SPECS
                }
                _store_media_metrics(
                    account=state.social_account,
                    media_id=media_id,
                    metrics=failed_metrics,
                    preserve_available=True,
                    sync_state=state,
                )
                checkpoint = dict(state.checkpoint or {})
                checkpoint["offset"] = int(checkpoint.get("offset", 0)) + 1
                state.checkpoint = checkpoint
                state.items_processed += 1
            state.content_status = InsightsSyncStatus.PARTIAL
            state.content_completed_at = timezone.now()
            state.items_total = state.items_discovered
            state.error_code = error_code
            state.error_reason = reason
            final_status = InsightsSyncStatus.PARTIAL
        _aggregate_overall_status(state)
        state.save()
        work.status = InsightsSyncWorkStatus.TERMINAL
        _clear_work_claim(work)
        work.next_attempt_at = None
        work.dispatch_expires_at = None
        work.save()
        _update_snapshot_slot_for_terminal_stage(
            state, work.stage, final_status,
        )
        return {"status": final_status, "error_code": error_code}
