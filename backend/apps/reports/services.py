from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core import signing
from django.db.models import F, FloatField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from rest_framework.exceptions import APIException, ValidationError

from apps.insights.snapshot_read import (
    build_account_snapshot_read,
    build_content_snapshot_read,
    get_duration_slot_days,
)


REPORT_TOKEN_SALT = "reports.insights.render"
REPORT_TOKEN_MAX_AGE_SECONDS = 15 * 60
PLATFORM_CONTENT_FIELDS = {
    "instagram": (
        ("reach", "Reach"),
        ("engagement", "Engagement"),
        ("likes", "Likes / Reactions"),
        ("comments", "Comments"),
        ("shares", "Shares"),
    ),
    "facebook": (
        ("reach", "Reach"),
        ("views", "Views"),
        ("reactions", "Reactions"),
        ("comments", "Comments"),
        ("clicks", "Clicks"),
    ),
}


class ReportSnapshotUnavailable(APIException):
    status_code = 409
    default_detail = "A complete saved Insights snapshot is required to export this report."
    default_code = "report_snapshot_unavailable"


def _metric_envelope(metrics, key):
    value = metrics.get(key) if isinstance(metrics, dict) else None
    return value if isinstance(value, dict) else {
        "value": None,
        "availability": "unavailable",
        "reason": "metric_not_recorded",
    }


def _metric_number(envelope):
    if not isinstance(envelope, dict) or envelope.get("availability") != "available":
        return None
    value = envelope.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    return float(value)


def _date_in_timezone(value, tz):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.date()
    return value.astimezone(tz).date()


def _daily_reach(*, queryset, since, until, organization_timezone):
    try:
        tz = ZoneInfo(organization_timezone or settings.TIME_ZONE)
    except (ZoneInfoNotFoundError, TypeError):
        tz = ZoneInfo(settings.TIME_ZONE)

    buckets = {}
    for item in queryset.values("published_at", "metrics").iterator():
        published_day = _date_in_timezone(item["published_at"], tz)
        if published_day is None or not since <= published_day <= until:
            continue
        bucket = buckets.setdefault(published_day, {"posts": 0, "available": 0, "total": 0.0})
        bucket["posts"] += 1
        reach = _metric_number(_metric_envelope(item["metrics"], "reach"))
        if reach is not None:
            bucket["available"] += 1
            bucket["total"] += reach

    points = []
    current = since
    while current <= until:
        bucket = buckets.get(current)
        value = None
        if bucket is not None and bucket["posts"] == bucket["available"]:
            value = bucket["total"]
        points.append({
            "date": current.isoformat(),
            "value": value,
            "posts": bucket["posts"] if bucket else 0,
        })
        current += timedelta(days=1)
    return points


def _top_content(*, queryset, platform):
    reach_value = Cast(
        KeyTextTransform("value", KeyTextTransform("reach", "metrics")),
        FloatField(),
    )
    rows = queryset.filter(
        metrics__reach__availability="available",
    ).exclude(
        metrics__reach__value__isnull=True,
    ).annotate(
        _report_reach_value=reach_value,
    ).order_by(
        F("_report_reach_value").desc(nulls_last=True),
        F("published_at").desc(nulls_last=True),
        "provider_media_id",
    )[:5]

    fields = PLATFORM_CONTENT_FIELDS[platform]
    content = []
    for item in rows:
        metrics = item.metrics if isinstance(item.metrics, dict) else {}
        content.append({
            "provider_media_id": item.provider_media_id,
            "media_type": item.media_type,
            "caption": item.caption,
            "permalink": item.permalink,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "metrics": {
                key: _metric_envelope(metrics, key)
                for key, _label in fields
            },
        })
    return content


def build_insights_report_payload(*, user, organization, account, since, until, mode, meta_ads):
    duration_days = get_duration_slot_days(account=account, since=since, until=until)
    account_read = build_account_snapshot_read(
        organization=organization,
        account=account,
        since=since,
        until=until,
        duration_days=duration_days,
    )
    account_freshness = account_read["freshness"]["account_snapshot"]
    if not account_freshness["exists"]:
        raise ReportSnapshotUnavailable("No saved account snapshot exists for the selected duration.")

    content_queryset, content_sync = build_content_snapshot_read(
        account=account,
        duration_days=duration_days,
    )
    if content_sync["content_status"] != "complete":
        raise ReportSnapshotUnavailable("No complete saved content snapshot exists for the selected duration.")

    actual_since = account_freshness.get("since")
    actual_until = account_freshness.get("until")
    if (
        not actual_since
        or not actual_until
        or actual_since != content_sync.get("content_since")
        or actual_until != content_sync.get("content_until")
    ):
        raise ReportSnapshotUnavailable(
            "The published account and content snapshots cover different date ranges."
        )

    from datetime import date

    snapshot_since = date.fromisoformat(actual_since)
    snapshot_until = date.fromisoformat(actual_until)
    if (snapshot_until - snapshot_since).days + 1 != duration_days:
        raise ReportSnapshotUnavailable("The saved snapshot range does not match the selected duration.")

    account_metrics = account_read["account_overview"].get("metrics") or {}
    content_count = content_queryset.count()
    stats = [
        {"label": "Total Reach", "metric": _metric_envelope(account_metrics, "reach")},
        {"label": "Total Engagement", "metric": _metric_envelope(account_metrics, "engagement")},
        {"label": "Total Followers", "metric": _metric_envelope(account_metrics, "followers")},
        {"label": "Total Views", "metric": _metric_envelope(account_metrics, "views")},
        {"label": "Total Posts", "metric": {"value": content_count, "availability": "available"}},
    ]
    platform = account.platform
    content_fields = [
        {"key": key, "label": label}
        for key, label in PLATFORM_CONTENT_FIELDS[platform]
    ]
    report = {
        "organization": {"name": organization.name},
        "account": {
            "platform": platform,
            "name": account.username or account.account_name or account.platform_account_id,
        },
        "date_range": {
            "since": actual_since,
            "until": actual_until,
            "duration_days": duration_days,
        },
        "stats": stats,
        "daily_reach": _daily_reach(
            queryset=content_queryset,
            since=snapshot_since,
            until=snapshot_until,
            organization_timezone=organization.timezone,
        ),
        "content_fields": content_fields,
        "content_performance": _top_content(
            queryset=content_queryset,
            platform=platform,
        ),
        "meta_ads": [
            {"date": row["date"].isoformat(), "total_leads": str(row["total_leads"])}
            for row in meta_ads
        ] if mode == "add_ads" else [],
        "mode": mode,
    }
    render_token = signing.dumps({
        "user_id": str(user.pk),
        "organization_id": organization.organization_id,
        "social_account_id": str(account.id),
        "duration_days": duration_days,
        "since": actual_since,
        "until": actual_until,
        "mode": mode,
    }, salt=REPORT_TOKEN_SALT, compress=True)
    return {"report": report, "render_token": render_token}


def validate_report_render_token(*, token, user):
    try:
        payload = signing.loads(
            token,
            salt=REPORT_TOKEN_SALT,
            max_age=REPORT_TOKEN_MAX_AGE_SECONDS,
        )
    except signing.BadSignature as exc:
        raise ValidationError({"render_token": "The report preview has expired. Please generate it again."}) from exc
    if payload.get("user_id") != str(user.pk):
        raise ValidationError({"render_token": "This report preview belongs to another user."})
    return payload
