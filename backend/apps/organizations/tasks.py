from celery import shared_task

from .services import (
    activate_due_scheduled_subscriptions,
)

from .subscription_service import (
    expire_due_subscriptions,
)

from apps.notifications.models import (
    EmailEventType,
)

from apps.notifications.services import (
    queue_email_event,
)

from apps.notifications.recipients import (
    get_organization_billing_recipient,
)

from .models import (
    OrganizationSubscription,
    SubscriptionStatus,
)

# ============================================================
# SCHEDULED SUBSCRIPTION ACTIVATION
# ============================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def activate_scheduled_subscriptions_task(
    self,
):
    """
    Activate scheduled subscriptions whose start date has arrived.

    Renewal email is triggered by the service layer only after
    the scheduled subscription actually becomes ACTIVE.
    """

    activated_count = activate_due_scheduled_subscriptions()

    return {
        "activated_count": activated_count,
    }


# ============================================================
# PLAN EXPIRY REMINDER
# ============================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def send_plan_expiry_reminders_task(
    self,
):
    """
    Queue plan expiry reminder emails for subscriptions
    expiring exactly three days from today.
    """

    from django.utils import timezone
    from datetime import timedelta

    today = timezone.localdate()

    reminder_date = today + timedelta(days=3)

    subscriptions = OrganizationSubscription.objects.select_related(
        "organization",
        "plan",
    ).filter(
        is_deleted=False,
        is_current=True,
        status=SubscriptionStatus.ACTIVE,
        expiry_date=reminder_date,
    )

    queued_count = 0

    for subscription in subscriptions:
        organization = subscription.organization

        recipient_email, recipient_name = get_organization_billing_recipient(
            organization,
        )

        if not recipient_email:
            continue

        event = queue_email_event(
            organization=organization,
            subscription=subscription,
            event_type=(EmailEventType.PLAN_EXPIRY_REMINDER),
            recipient_email=recipient_email,
            recipient_name=recipient_name,
        )

        if event:
            queued_count += 1

    return {
        "queued_count": queued_count,
        "reminder_date": reminder_date.isoformat(),
    }


# ============================================================
# PLAN EXPIRY
# ============================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def expire_due_subscriptions_task(
    self,
):
    """
    Expire subscriptions whose expiry date has passed.

    The underlying service performs the actual state transition.
    """

    expired_count = expire_due_subscriptions()

    return {
        "expired_count": expired_count,
    }
