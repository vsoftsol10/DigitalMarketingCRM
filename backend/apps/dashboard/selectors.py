from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Exists, OuterRef, Q, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.organizations.models import Organization, OrganizationSubscription, SubscriptionStatus
from apps.activities.models import ActivityLog
from apps.posts.models import PostPlatform, PostStatus
from apps.posts.selectors import get_calendar_event_local_datetime
from apps.social_accounts.models import SocialAccount, SocialAccountStatus

DASHBOARD_NOTIFICATION_LIMIT = 20
DASHBOARD_ACTIVITY_LIMIT = 10
_POST_PREVIEW_LIMIT = 160
_FAILURE_REASON = "Publishing failed. Review the target and retry it from Calendar."

_DASHBOARD_ACTIVITY_METADATA_FIELDS = {
    "organization_name",
    "billing_cycle",
    "plan_id",
    "schedule_type",
    "publish_type",
    "schedule_scope",
    "scheduled_at",
    "timezone",
    "platform",
    "attempt_count",
}


def _utc_bounds_for_current_local_days(now):
    """Return a bounded UTC range that covers today's date in every IANA timezone."""

    utc_date = now.astimezone(ZoneInfo("UTC")).date()
    start = datetime.combine(utc_date - timedelta(days=1), time.min, tzinfo=ZoneInfo("UTC"))
    end = datetime.combine(utc_date + timedelta(days=2), time.min, tzinfo=ZoneInfo("UTC"))
    return start, end


def _is_target_today(target, now):
    event_datetime = get_calendar_event_local_datetime(target)
    return (
        event_datetime is not None
        and event_datetime.date() == now.astimezone(event_datetime.tzinfo).date()
    )


def _target_timezone(target):
    return target.scheduled_timezone or target.post.timezone or "UTC"


def _account_display_name(target):
    account = target.social_account
    if (
        not account
        or account.is_deleted
        or account.organization_id != target.post.organization_id
    ):
        return ""
    return account.account_name or account.username or account.platform_account_id


def _post_title(post):
    caption = _display_text(post.caption, limit=80)
    return caption.splitlines()[0] if caption else "Untitled Post"


def _display_text(value, *, limit):
    """Normalize untrusted user/provider text for compact Dashboard display."""

    return " ".join(str(value or "").split())[:limit]


def _post_preview(post):
    return _display_text(post.caption, limit=_POST_PREVIEW_LIMIT)


def _activity_post(activity):
    post = activity.post
    if post and post.organization_id == activity.organization_id:
        return post

    target = activity.post_platform
    if target and target.post.organization_id == activity.organization_id:
        return target.post

    return None


def _activity_target(activity):
    target = activity.post_platform
    if target and target.post.organization_id == activity.organization_id:
        return target
    return None


def _activity_subscription(activity):
    subscription = activity.subscription
    if subscription and subscription.organization_id == activity.organization_id:
        return subscription
    return None


def _metadata_datetime(metadata, field_name):
    value = metadata.get(field_name) if isinstance(metadata, dict) else None
    return parse_datetime(value) if isinstance(value, str) else None


def _safe_failure_reason(_target):
    """Use a fixed, user-safe message instead of provider error payload text."""

    return _FAILURE_REASON


def _activity_metadata_for_dashboard(metadata):
    """Return only display-safe, primitive activity metadata."""
    if not isinstance(metadata, dict):
        return {}

    return {
        key: value
        for key, value in metadata.items()
        if key in _DASHBOARD_ACTIVITY_METADATA_FIELDS
        and isinstance(value, (str, int, float, bool, type(None)))
    }


def _recent_activities(*, user):
    activities = (
        ActivityLog.objects.filter(
            organization__created_by=user,
            organization__is_deleted=False,
            is_deleted=False,
        )
        .select_related(
            "organization",
            "actor",
            "post",
            "post_platform__post",
            "post_platform__social_account",
            "subscription__plan",
        )
        .order_by("-occurred_at", "-id")[:DASHBOARD_ACTIVITY_LIMIT]
    )

    recent_activities = []
    for activity in activities:
        metadata = activity.metadata if isinstance(activity.metadata, dict) else {}
        post = _activity_post(activity)
        target = _activity_target(activity)
        subscription = _activity_subscription(activity)
        plan = subscription.plan if subscription else None

        recent_activities.append(
            {
                "id": activity.id,
                "event_type": activity.event_type,
                "occurred_at": activity.occurred_at,
                "organization_id": activity.organization.organization_id,
                "organization_name": activity.organization.name,
                "actor_name": activity.actor.full_name if activity.actor else "",
                "actor_email": activity.actor.email if activity.actor else "",
                "metadata": _activity_metadata_for_dashboard(activity.metadata),
                "post_title": _post_title(post) if post else "",
                "post_preview": _post_preview(post) if post else "",
                "platform": (
                    target.platform.upper()
                    if target
                    else _display_text(metadata.get("platform"), limit=20).upper()
                ),
                "social_account": _account_display_name(target) if target else "",
                "scheduled_at": (
                    _metadata_datetime(metadata, "scheduled_at")
                    or (target.scheduled_at if target else None)
                    or (post.scheduled_at if post else None)
                ),
                "published_at": (
                    target.published_at if target else (post.published_at if post else None)
                ),
                "plan_name": plan.name if plan and not plan.is_deleted else "",
                "expiry_date": subscription.expiry_date if subscription else None,
            }
        )

    return recent_activities


def _subscription_notification(subscription, *, notification_type, title, message, days_remaining=None):
    notification = {
        "id": f"{notification_type.lower().replace('_', '-')}:{subscription.id}",
        "type": notification_type,
        "title": title,
        "message": message,
        "organization_id": subscription.organization.organization_id,
        "organization_name": subscription.organization.name,
        "expiry_date": subscription.expiry_date,
        "created_at": subscription.updated_at,
    }

    if not subscription.plan.is_deleted:
        notification["plan_name"] = subscription.plan.name
    if days_remaining is not None:
        notification["days_remaining"] = days_remaining

    return notification


def get_dashboard_data(*, user):
    """Build the owner-scoped, read-only Dashboard response payload."""

    now = timezone.now()
    today = timezone.localdate()
    reminder_end = today + timedelta(days=3)
    utc_start, utc_end = _utc_bounds_for_current_local_days(now)

    organizations = Organization.objects.filter(
        created_by=user,
        is_deleted=False,
    )

    target_base_queryset = (
        PostPlatform.objects.filter(
            is_deleted=False,
            post__is_deleted=False,
            post__organization__is_deleted=False,
            post__organization__created_by=user,
        )
        .filter(Q(social_account__isnull=True) | Q(social_account__is_deleted=False))
        .select_related("post", "post__organization", "social_account")
    )

    scheduled_candidates = target_base_queryset.filter(
        status=PostStatus.SCHEDULED,
    ).filter(
        Q(scheduled_at__gte=utc_start, scheduled_at__lt=utc_end)
        | Q(
            scheduled_at__isnull=True,
            post__scheduled_at__gte=utc_start,
            post__scheduled_at__lt=utc_end,
        )
    )
    scheduled_targets = [
        target
        for target in scheduled_candidates
        if _is_target_today(target, now)
    ]
    scheduled_targets.sort(
        key=lambda target: (
            get_calendar_event_local_datetime(target),
            str(target.id),
        )
    )

    published_candidates = target_base_queryset.filter(
        status=PostStatus.PUBLISHED,
        published_at__gte=utc_start,
        published_at__lt=utc_end,
    )
    published_targets = [
        target
        for target in published_candidates
        if _is_target_today(target, now)
    ]

    expiring_subscriptions = (
        OrganizationSubscription.objects.filter(
            organization__created_by=user,
            organization__is_deleted=False,
            is_deleted=False,
            is_current=True,
            status=SubscriptionStatus.ACTIVE,
            expiry_date__gte=today,
            expiry_date__lte=reminder_end,
        )
        .select_related("organization", "plan")
        .order_by("-updated_at", "-id")[:DASHBOARD_NOTIFICATION_LIMIT]
    )
    active_current_subscription = OrganizationSubscription.objects.filter(
        organization_id=OuterRef("organization_id"),
        is_deleted=False,
        is_current=True,
        status=SubscriptionStatus.ACTIVE,
    )
    latest_expired_subscription = (
        OrganizationSubscription.objects.filter(
            organization_id=OuterRef("organization_id"),
            is_deleted=False,
            status=SubscriptionStatus.EXPIRED,
        )
        .order_by("-expiry_date", "-updated_at", "-id")
        .values("id")[:1]
    )
    expired_subscriptions = (
        OrganizationSubscription.objects.filter(
            organization__created_by=user,
            organization__is_deleted=False,
            is_deleted=False,
            status=SubscriptionStatus.EXPIRED,
        )
        .annotate(has_current_active=Exists(active_current_subscription))
        .filter(
            has_current_active=False,
            id=Subquery(latest_expired_subscription),
        )
        .select_related("organization", "plan")
        .order_by("-updated_at", "-id")[:DASHBOARD_NOTIFICATION_LIMIT]
    )
    failed_targets = (
        target_base_queryset.filter(status=PostStatus.FAILED)
        .order_by("-updated_at", "-id")[:DASHBOARD_NOTIFICATION_LIMIT]
    )

    notifications = [
        _subscription_notification(
            subscription,
            notification_type="SUBSCRIPTION_EXPIRING",
            title="Subscription Expiring Soon",
            message=(
                f"{subscription.plan.name if not subscription.plan.is_deleted else 'Subscription'} "
                f"expires on {subscription.expiry_date.isoformat()}."
            ),
            days_remaining=(subscription.expiry_date - today).days,
        )
        for subscription in expiring_subscriptions
    ]
    notifications.extend(
        _subscription_notification(
            subscription,
            notification_type="SUBSCRIPTION_EXPIRED",
            title="Subscription Expired",
            message=(
                f"{subscription.plan.name if not subscription.plan.is_deleted else 'Subscription'} "
                f"expired on {subscription.expiry_date.isoformat()}."
            ),
        )
        for subscription in expired_subscriptions
    )
    notifications.extend(
        {
            "id": f"failed-post:{target.id}",
            "type": "FAILED_POST",
            "title": "Failed Post",
            "message": _safe_failure_reason(target),
            "organization_id": target.post.organization.organization_id,
            "organization_name": target.post.organization.name,
            "post_id": target.post_id,
            "target_id": target.id,
            "platform": target.platform.upper(),
            "social_account": _account_display_name(target),
            "post_title": _post_title(target.post),
            "post_preview": _post_preview(target.post),
            "failure_reason": _safe_failure_reason(target),
            "error_message": _safe_failure_reason(target),
            "created_at": target.updated_at,
        }
        for target in failed_targets
    )
    notifications.sort(
        key=lambda notification: (notification["created_at"], notification["id"]),
        reverse=True,
    )
    notifications = notifications[:DASHBOARD_NOTIFICATION_LIMIT]

    return {
        "statistics": {
            "total_organizations": organizations.count(),
            "connected_social_accounts": SocialAccount.objects.filter(
                organization__created_by=user,
                organization__is_deleted=False,
                is_deleted=False,
                status=SocialAccountStatus.CONNECTED,
                is_valid=True,
            ).count(),
            "scheduled_posts_today": len(scheduled_targets),
            "published_posts_today": len(published_targets),
        },
        "today_schedule": [
            {
                "target_id": target.id,
                "post_id": target.post_id,
                "organization_id": target.post.organization.organization_id,
                "organization_name": target.post.organization.name,
                "platform": target.platform.upper(),
                "social_account": _account_display_name(target),
                "content_type": target.content_type,
                "title": _post_title(target.post),
                "scheduled_at": target.scheduled_at or target.post.scheduled_at,
                "timezone": _target_timezone(target),
                "status": target.status,
            }
            for target in scheduled_targets
        ],
        "notifications": notifications,
        "recent_activities": _recent_activities(user=user),
    }
