import logging

from django.db import transaction

from .models import ActivityEventType, ActivityLog

logger = logging.getLogger(__name__)

_NOTIFICATION_EVENT_TYPES = {
    ActivityEventType.POST_FAILED,
    ActivityEventType.POST_PUBLISHED,
    ActivityEventType.SUBSCRIPTION_ACTIVATED,
    ActivityEventType.SUBSCRIPTION_RENEWED,
    ActivityEventType.SUBSCRIPTION_CANCELLED,
    ActivityEventType.SUBSCRIPTION_EXPIRING,
    ActivityEventType.SUBSCRIPTION_EXPIRED,
}


def create_activity_log(
    *,
    organization,
    event_type,
    source,
    actor=None,
    subscription=None,
    post=None,
    post_platform=None,
    metadata=None,
    idempotency_key="",
):
    """Create one durable business activity within the caller's transaction."""
    values = {
        "organization": organization,
        "event_type": event_type,
        "source": source,
        "actor": actor,
        "subscription": subscription,
        "post": post,
        "post_platform": post_platform,
        "metadata": metadata or {},
        "idempotency_key": idempotency_key,
    }

    if idempotency_key:
        activity, created = ActivityLog.objects.get_or_create(
            idempotency_key=idempotency_key,
            is_deleted=False,
            defaults=values,
        )
    else:
        activity = ActivityLog.objects.create(**values)
        created = True

    if created and event_type in _NOTIFICATION_EVENT_TYPES:
        # Keep notification failures isolated from the business lifecycle event.
        # Most callers already have an outer transaction; this savepoint prevents
        # a notification write failure from rolling back publishing/subscription state.
        try:
            with transaction.atomic():
                from apps.notifications.services import record_activity_notification

                record_activity_notification(activity)
        except Exception:
            logger.exception(
                "Unable to persist in-app notification for activity. activity_id=%s event_type=%s",
                activity.id,
                activity.event_type,
            )

    return activity
