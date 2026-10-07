"""Database-only read helpers for published Insights snapshots."""

from datetime import datetime, time, timedelta, timezone as datetime_timezone

from django.db.models import Count, Max, Min, Q
from rest_framework.exceptions import ValidationError

from apps.social_accounts.models import SocialPlatform

from .models import (
    InsightsAccountSnapshot,
    InsightsContentSnapshotItem,
    InsightsSnapshotSlot,
    InsightsSyncStatus,
)


def _iso(value):
    return value.isoformat() if value else None


def get_duration_slot_days(*, account, since, until):
    """Validate the selected inclusive range and map it to a platform slot."""
    duration_days = (until - since).days + 1
    supported = {
        SocialPlatform.INSTAGRAM: {7, 30},
        SocialPlatform.FACEBOOK: {7, 28},
    }.get(account.platform, set())
    if duration_days not in supported:
        raise ValidationError({
            "date_range": "The selected date range is not supported for this platform."
        })
    return duration_days


def _more_content_available(state):
    if state is None or state.content_status != InsightsSyncStatus.PARTIAL:
        return False

    checkpoint = state.checkpoint if isinstance(state.checkpoint, dict) else {}
    next_cursor = checkpoint.get("next_cursor")
    provider_cursor = state.provider_cursor
    has_cursor = any(
        isinstance(cursor, str) and bool(cursor.strip())
        for cursor in (next_cursor, provider_cursor)
    )
    return bool(
        has_cursor
        and (
            checkpoint.get("has_more") is True
            or (
                "has_more" not in checkpoint
                and checkpoint.get("stop_reason") == "page_ceiling_reached"
                and isinstance(provider_cursor, str)
                and bool(provider_cursor.strip())
            )
        )
    )


def _attempt_payload(state):
    if state is None:
        return None
    return {
        "sync_state_id": str(state.id),
        "status": state.status,
        "account_status": state.account_status,
        "content_status": state.content_status,
        "more_content_available": _more_content_available(state),
        "progress": {
            "discovered": state.items_discovered,
            "processed": state.items_processed,
            "total": state.items_total,
        },
        "requested_at": _iso(state.requested_at),
        "started_at": _iso(state.started_at),
        "completed_at": _iso(state.completed_at),
        "account_started_at": _iso(state.account_started_at),
        "account_completed_at": _iso(state.account_completed_at),
        "content_completed_at": _iso(state.content_completed_at),
        "error_code": state.error_code,
        "error_reason": state.error_reason,
        "account_error_code": state.account_error_code,
        "account_error_reason": state.account_error_reason,
    }


def _published_sync_payload(*, account_state, content_state, active_state, legacy_account=False):
    """Keep status fields tied to published stages and active polling separate."""
    if active_state is not None:
        status = active_state.status
        active_progress = {
            "discovered": active_state.items_discovered,
            "processed": active_state.items_processed,
            "total": active_state.items_total,
        }
        progress = active_progress if account_state is None and content_state is None else None
        requested_at = _iso(active_state.requested_at)
        started_at = _iso(active_state.started_at)
    elif account_state is not None or content_state is not None or legacy_account:
        status = InsightsSyncStatus.COMPLETE
        progress = None
        requested_at = None
        started_at = None
    else:
        status = "never_synced"
        progress = None
        requested_at = None
        started_at = None

    return {
        "status": status,
        "account_status": "complete" if account_state is not None or legacy_account else "never_synced",
        "content_status": "complete" if content_state is not None else "never_synced",
        "more_content_available": False,
        "progress": progress,
        "requested_at": requested_at,
        "started_at": started_at,
        "completed_at": None,
        "account_started_at": _iso(account_state.account_started_at) if account_state else None,
        "account_completed_at": _iso(account_state.account_completed_at) if account_state else None,
        "content_completed_at": _iso(content_state.content_completed_at) if content_state else None,
        "error_code": "",
        "error_reason": "",
        "account_error_code": "",
        "account_error_reason": "",
        "active_sync": _attempt_payload(active_state),
    }


def _get_slot(*, account, duration_days):
    return (
        InsightsSnapshotSlot.objects.filter(
            social_account=account,
            duration_days=duration_days,
            is_deleted=False,
        )
        .select_related(
            "published_account_sync_state",
            "published_content_sync_state",
            "active_sync_state",
        )
        .first()
    )


def _state_for_account_pointer(*, slot, account):
    state = slot.published_account_sync_state if slot is not None else None
    if (
        state is None
        or state.is_deleted
        or state.social_account_id != account.id
        or (state.until - state.since).days + 1 != slot.duration_days
    ):
        return None
    return state


def _state_for_content_pointer(*, slot, account):
    state = slot.published_content_sync_state if slot is not None else None
    if (
        state is None
        or state.is_deleted
        or state.social_account_id != account.id
        or (state.until - state.since).days + 1 != slot.duration_days
    ):
        return None
    return state


def _active_state_for_slot(*, slot, account):
    state = slot.active_sync_state if slot is not None else None
    if (
        state is None
        or state.is_deleted
        or state.social_account_id != account.id
        or (state.until - state.since).days + 1 != slot.duration_days
    ):
        return None
    return state


def _metrics_status(metrics):
    if not isinstance(metrics, dict) or not metrics:
        return "unavailable", "metrics_not_recorded"

    entries = [value for value in metrics.values() if isinstance(value, dict)]
    if any(value.get("availability") == "available" for value in entries):
        return "available", ""

    for availability in ("permission_required", "provider_error", "not_supported", "unavailable"):
        for value in entries:
            if value.get("availability") == availability:
                return availability, value.get("reason", "")
    return "unavailable", "metric_availability_not_recorded"


def _legacy_account_snapshot(*, account, since, until):
    """Preserve the old exact-range read only when no versioned slot exists."""
    return (
        InsightsAccountSnapshot.objects.filter(
            social_account=account,
            since=since,
            until=until,
            sync_state__isnull=True,
            is_deleted=False,
        )
        .order_by("-fetched_at", "-id")
        .first()
    )


def build_account_snapshot_read(*, organization, account, since, until, duration_days=None):
    duration_days = duration_days or get_duration_slot_days(
        account=account,
        since=since,
        until=until,
    )
    slot = _get_slot(account=account, duration_days=duration_days)
    state = _state_for_account_pointer(slot=slot, account=account)
    snapshot = None
    legacy = False

    if state is not None:
        snapshot = InsightsAccountSnapshot.objects.filter(
            social_account=account,
            sync_state=state,
            api_version=state.api_version,
            is_deleted=False,
        ).order_by("-id").first()
    elif slot is None:
        snapshot = _legacy_account_snapshot(account=account, since=since, until=until)
        legacy = snapshot is not None

    metrics = snapshot.metrics if snapshot is not None else None
    availability, reason = (
        ("not_ready", "snapshot_not_found")
        if snapshot is None
        else _metrics_status(metrics)
    )
    updated_at = (
        state.account_completed_at
        if state is not None
        else snapshot.fetched_at if legacy and snapshot is not None else None
    )
    snapshot_since = snapshot.since if snapshot is not None else None
    snapshot_until = snapshot.until if snapshot is not None else None
    sync = _published_sync_payload(
        account_state=state,
        content_state=_state_for_content_pointer(slot=slot, account=account),
        active_state=_active_state_for_slot(slot=slot, account=account),
        legacy_account=legacy,
    )

    return {
        "schema_version": "2.0",
        "filters": {
            "organization_id": organization.organization_id,
            "social_account_id": str(account.id),
            "platform": account.platform,
            "since": since.isoformat(),
            "until": until.isoformat(),
        },
        "account": account,
        "account_overview": {
            "availability": availability,
            "reason": reason,
            "metrics": metrics if snapshot is not None else None,
        },
        "follower_growth": snapshot.follower_growth if snapshot is not None else None,
        "account_performance": {
            "availability": availability,
            "reason": reason,
            "metrics": metrics if snapshot is not None else None,
        },
        "freshness": {
            "account_snapshot": {
                "exists": snapshot is not None,
                "status": "complete" if snapshot is not None else "never_synced",
                "since": snapshot_since.isoformat() if snapshot_since else None,
                "until": snapshot_until.isoformat() if snapshot_until else None,
                "updated_at": _iso(updated_at),
                # Kept for existing frontend compatibility.
                "fetched_at": _iso(updated_at),
                "source": "legacy" if legacy else "published" if state is not None else None,
            },
            "sync": sync,
            "active_sync": sync["active_sync"],
        },
    }


def publication_range(*, since, until):
    """Return UTC day boundaries matching the provider's parsed timestamp dates."""
    start = datetime.combine(since, time.min, tzinfo=datetime_timezone.utc)
    end = datetime.combine(until + timedelta(days=1), time.min, tzinfo=datetime_timezone.utc)
    return start, end


def get_content_snapshot_queryset(*, account, since=None, until=None, duration_days=None):
    if duration_days is None:
        if since is None or until is None:
            raise ValueError("duration_days or both since and until are required")
        duration_days = get_duration_slot_days(account=account, since=since, until=until)
    slot = _get_slot(account=account, duration_days=duration_days)
    state = _state_for_content_pointer(slot=slot, account=account)
    return _content_items_for_state(state)


def _content_items_for_state(state):
    if state is None:
        return InsightsContentSnapshotItem.objects.none()
    return InsightsContentSnapshotItem.objects.filter(
        sync_state=state,
        api_version=state.api_version,
        is_deleted=False,
    ).only(
        "provider_media_id",
        "media_type",
        "caption",
        "permalink",
        "published_at",
        "metrics",
        "fetched_at",
    ).order_by("-published_at", "-provider_media_id")


def get_content_freshness(*, queryset, sync):
    values = queryset.aggregate(
        total=Count("id"),
        fetched=Count("id", filter=Q(fetched_at__isnull=False)),
        unfetched=Count("id", filter=Q(fetched_at__isnull=True)),
        oldest_fetched_at=Min("fetched_at"),
        newest_media_fetched_at=Max("fetched_at"),
    )
    published = sync["content_status"] == InsightsSyncStatus.COMPLETE
    if values["total"]:
        availability, reason = "available", ""
    elif published:
        availability, reason = "available", "no_media_in_range"
    else:
        availability, reason = "unavailable", "never_synced"

    # Existing frontend reads newest_fetched_at as the update label. Keep that
    # response key, but source it from the published stage completion time.
    completed_at = sync.get("content_completed_at") if published else None
    return {
        "availability": availability,
        "reason": reason,
        "status": "complete" if published else "never_synced",
        "since": sync.get("content_since"),
        "until": sync.get("content_until"),
        "updated_at": completed_at,
        "completed_at": completed_at,
        "media_count": values["total"],
        "fetched_count": values["fetched"],
        "unfetched_count": values["unfetched"],
        "oldest_fetched_at": _iso(values["oldest_fetched_at"]),
        "newest_media_fetched_at": _iso(values["newest_media_fetched_at"]),
        "newest_fetched_at": completed_at,
    }


def build_content_sync_read(*, account, since=None, until=None, duration_days=None):
    if duration_days is None:
        if since is None or until is None:
            raise ValueError("duration_days or both since and until are required")
        duration_days = get_duration_slot_days(account=account, since=since, until=until)
    slot = _get_slot(account=account, duration_days=duration_days)
    account_state = _state_for_account_pointer(slot=slot, account=account)
    content_state = _state_for_content_pointer(slot=slot, account=account)
    active_state = _active_state_for_slot(slot=slot, account=account)
    sync = _published_sync_payload(
        account_state=account_state,
        content_state=content_state,
        active_state=active_state,
    )
    sync["content_since"] = content_state.since.isoformat() if content_state else None
    sync["content_until"] = content_state.until.isoformat() if content_state else None
    sync["content_completed_at"] = _iso(content_state.content_completed_at) if content_state else None
    return sync


def build_content_snapshot_read(*, account, duration_days):
    """Read one slot version and its metadata from the same pointer snapshot."""
    slot = _get_slot(account=account, duration_days=duration_days)
    account_state = _state_for_account_pointer(slot=slot, account=account)
    content_state = _state_for_content_pointer(slot=slot, account=account)
    active_state = _active_state_for_slot(slot=slot, account=account)
    sync = _published_sync_payload(
        account_state=account_state,
        content_state=content_state,
        active_state=active_state,
    )
    sync["content_since"] = content_state.since.isoformat() if content_state else None
    sync["content_until"] = content_state.until.isoformat() if content_state else None
    sync["content_completed_at"] = _iso(content_state.content_completed_at) if content_state else None
    return _content_items_for_state(content_state), sync
