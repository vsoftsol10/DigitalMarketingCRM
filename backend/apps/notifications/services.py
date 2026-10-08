from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

import requests

from .constants import EMAIL_TEMPLATE_MAP
from .models import (
    EmailDeliveryStatus,
    EmailEvent,
    UserNotification,
    UserNotificationType,
)


BREVO_SEND_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


def _resolve_notifications(*, organization, event_types, post_platform=None, subscription=None):
    notifications = UserNotification.objects.filter(
        organization=organization,
        event_type__in=event_types,
        is_deleted=False,
        resolved_at__isnull=True,
    )
    if post_platform is not None:
        notifications = notifications.filter(post_platform=post_platform)
    if subscription is not None:
        notifications = notifications.filter(subscription=subscription)
    now = timezone.now()
    notifications.update(resolved_at=now, updated_at=now)


def _record_user_notification(
    *, activity, event_type, event_key, title, message, post_platform=None, subscription=None,
    reopen=False,
):
    organization = activity.organization
    recipient_id = organization.created_by_id
    if not recipient_id:
        return None

    defaults = {
        "recipient_id": recipient_id,
        "organization": organization,
        "source_activity": activity,
        "post_platform": post_platform,
        "subscription": subscription,
        "event_type": event_type,
        "title": title,
        "message": message,
        "resolved_at": None,
    }
    if reopen:
        defaults["read_at"] = None

    notification, created = UserNotification.objects.get_or_create(
        event_key=event_key,
        is_deleted=False,
        defaults=defaults,
    )
    if not created and reopen:
        for field, value in defaults.items():
            setattr(notification, field, value)
        notification.save(update_fields=[*defaults.keys(), "updated_at"])
    return notification


def record_activity_notification(activity):
    """Persist the notification counterpart of a real business lifecycle event."""
    from apps.activities.models import ActivityEventType

    event_type = activity.event_type
    target = activity.post_platform
    subscription = activity.subscription
    organization = activity.organization

    if event_type == ActivityEventType.POST_FAILED and target:
        return _record_user_notification(
            activity=activity,
            event_type=UserNotificationType.FAILED_POST,
            event_key=f"failed-post:{target.id}",
            title="Failed Post",
            message="Publishing failed. Review the target and retry it from Calendar.",
            post_platform=target,
            reopen=True,
        )

    if event_type == ActivityEventType.POST_PUBLISHED and target:
        _resolve_notifications(
            organization=organization,
            event_types=[UserNotificationType.FAILED_POST],
            post_platform=target,
        )
        return _record_user_notification(
            activity=activity,
            event_type=UserNotificationType.POST_PUBLISHED,
            event_key=f"post-published:{target.id}",
            title="Post Published",
            message="Your post was published successfully.",
            post_platform=target,
        )

    if event_type == ActivityEventType.SUBSCRIPTION_EXPIRING and subscription:
        return _record_user_notification(
            activity=activity,
            event_type=UserNotificationType.SUBSCRIPTION_EXPIRING,
            event_key=f"subscription-expiring:{subscription.id}",
            title="Subscription Expiring Soon",
            message=f"Subscription expires on {subscription.expiry_date.isoformat()}.",
            subscription=subscription,
        )

    if event_type == ActivityEventType.SUBSCRIPTION_EXPIRED and subscription:
        _resolve_notifications(
            organization=organization,
            event_types=[UserNotificationType.SUBSCRIPTION_EXPIRING],
            subscription=subscription,
        )
        return _record_user_notification(
            activity=activity,
            event_type=UserNotificationType.SUBSCRIPTION_EXPIRED,
            event_key=f"subscription-expired:{subscription.id}",
            title="Subscription Expired",
            message=f"Subscription expired on {subscription.expiry_date.isoformat()}.",
            subscription=subscription,
        )

    if event_type in {
        ActivityEventType.SUBSCRIPTION_ACTIVATED,
        ActivityEventType.SUBSCRIPTION_RENEWED,
    } and subscription:
        _resolve_notifications(
            organization=organization,
            event_types=[
                UserNotificationType.SUBSCRIPTION_EXPIRED,
                UserNotificationType.SUBSCRIPTION_EXPIRING,
            ],
        )
        return _record_user_notification(
            activity=activity,
            event_type=UserNotificationType.SUBSCRIPTION_ACTIVATED,
            event_key=f"subscription-activated:{subscription.id}",
            title="Subscription Activated",
            message="The organization subscription is active.",
            subscription=subscription,
        )

    if event_type == ActivityEventType.SUBSCRIPTION_CANCELLED:
        _resolve_notifications(
            organization=organization,
            event_types=[UserNotificationType.SUBSCRIPTION_EXPIRING],
        )

    return None


class BrevoEmailError(Exception):
    """
    Raised when Brevo fails to accept a transactional email.
    """


def get_brevo_template_id(event_type):
    """
    Resolve the Brevo template ID from Django settings.
    """

    setting_name = EMAIL_TEMPLATE_MAP.get(
        event_type,
    )

    if not setting_name:
        raise BrevoEmailError(
            f"No Brevo template configured for event: {event_type}",
        )

    template_id = getattr(
        settings,
        setting_name,
        None,
    )

    if not template_id:
        raise BrevoEmailError(
            f"Brevo template setting '{setting_name}' is not configured.",
        )

    return int(template_id)


def build_brevo_payload(
    *,
    event_type,
    recipient_email,
    recipient_name,
    params,
):
    """
    Build a Brevo transactional email payload.
    """

    template_id = get_brevo_template_id(
        event_type,
    )

    return {
        "sender": {
            "email": settings.BREVO_SENDER_EMAIL,
            "name": settings.BREVO_SENDER_NAME,
        },
        "to": [
            {
                "email": recipient_email,
                "name": recipient_name or "",
            }
        ],
        "templateId": template_id,
        "params": params or {},
        "tags": [
            "digital-marketing-platform",
            event_type,
        ],
    }


def send_brevo_email(
    *,
    event_type,
    recipient_email,
    recipient_name="",
    params=None,
):
    """
    Send a transactional email through Brevo.

    Returns:
        dict containing Brevo response data.
    """

    if not recipient_email:
        raise BrevoEmailError(
            "Recipient email is required.",
        )

    payload = build_brevo_payload(
        event_type=event_type,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        params=params,
    )

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            BREVO_SEND_EMAIL_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise BrevoEmailError(
            f"Brevo request failed: {exc}",
        ) from exc

    if not response.ok:
        try:
            error_data = response.json()
        except ValueError:
            error_data = {
                "message": response.text,
            }

        raise BrevoEmailError(
            f"Brevo rejected the email: {error_data}",
        )

    try:
        return response.json()
    except ValueError as exc:
        raise BrevoEmailError(
            "Brevo returned an invalid response.",
        ) from exc


def create_email_event(
    *,
    organization,
    subscription,
    event_type,
    recipient_email,
    recipient_name="",
):
    """
    Create an idempotent email event.

    Returns:
        tuple[EmailEvent, bool]

        created=True  -> new event
        created=False -> event already existed
    """

    try:
        event = EmailEvent.objects.create(
            organization=organization,
            subscription=subscription,
            event_type=event_type,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
        )

        return event, True

    except IntegrityError:
        existing_event = EmailEvent.objects.filter(
            subscription=subscription,
            event_type=event_type,
            is_deleted=False,
        ).first()

        if not existing_event:
            raise

        return existing_event, False


def mark_email_processing(
    event,
):
    """
    Mark an email event as processing.
    """

    event.status = EmailDeliveryStatus.PROCESSING

    event.attempts += 1

    event.last_error = ""

    event.save(
        update_fields=[
            "status",
            "attempts",
            "last_error",
            "updated_at",
        ],
    )


def mark_email_sent(
    *,
    event,
    provider_message_id="",
):
    """
    Mark email as successfully accepted by Brevo.
    """

    event.status = EmailDeliveryStatus.SENT

    event.provider_message_id = provider_message_id or ""

    event.sent_at = timezone.now()

    event.last_error = ""

    event.save(
        update_fields=[
            "status",
            "provider_message_id",
            "sent_at",
            "last_error",
            "updated_at",
        ],
    )


def mark_email_failed(
    *,
    event,
    error,
):
    """
    Mark an email delivery attempt as failed.
    """

    event.status = EmailDeliveryStatus.FAILED

    event.last_error = str(
        error,
    )

    event.save(
        update_fields=[
            "status",
            "last_error",
            "updated_at",
        ],
    )


from django.db import transaction

from .models import EmailEventType


def queue_email_event(
    *,
    organization,
    subscription,
    event_type,
    recipient_email,
    recipient_name="",
):
    """
    Create an idempotent email event and queue delivery
    only after the surrounding transaction commits.
    """

    if not recipient_email:
        return None

    from .services import create_email_event
    from .tasks import send_email_event_task

    event, created = create_email_event(
        organization=organization,
        subscription=subscription,
        event_type=event_type,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
    )

    if not created:
        return event

    transaction.on_commit(
        lambda: send_email_event_task.delay(
            str(event.id),
        )
    )

    return event
