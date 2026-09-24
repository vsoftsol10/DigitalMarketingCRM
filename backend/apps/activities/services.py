from .models import ActivityLog


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
        activity, _created = ActivityLog.objects.get_or_create(
            idempotency_key=idempotency_key,
            is_deleted=False,
            defaults=values,
        )
        return activity

    return ActivityLog.objects.create(**values)
