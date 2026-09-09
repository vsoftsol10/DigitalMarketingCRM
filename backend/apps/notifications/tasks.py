from celery import shared_task

from .models import (
    EmailDeliveryStatus,
    EmailEvent,
)

from .services import (
    BrevoEmailError,
    mark_email_failed,
    mark_email_processing,
    mark_email_sent,
    send_brevo_email,
)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def send_email_event_task(
    self,
    email_event_id,
):
    """
    Deliver a pending transactional email event
    through Brevo.
    """

    event = (
        EmailEvent.objects
        .select_related(
            "organization",
            "subscription",
        )
        .filter(
            id=email_event_id,
            is_deleted=False,
        )
        .first()
    )

    if not event:
        return {
            "status": "not_found",
        }

    # ----------------------------------------------------------
    # IDEMPOTENCY
    # ----------------------------------------------------------

    if (
        event.status ==
        EmailDeliveryStatus.SENT
    ):
        return {
            "status": "already_sent",
            "email_event_id": str(
                event.id,
            ),
        }

    # ----------------------------------------------------------
    # PROCESSING
    # ----------------------------------------------------------

    mark_email_processing(
        event,
    )

    # ----------------------------------------------------------
    # PARAMS
    # ----------------------------------------------------------

    params = build_email_params(
        event,
    )

    try:
        response = send_brevo_email(
            event_type=event.event_type,
            recipient_email=event.recipient_email,
            recipient_name=event.recipient_name,
            params=params,
        )

        provider_message_id = (
            response.get(
                "messageId",
                "",
            )
        )

        mark_email_sent(
            event=event,
            provider_message_id=provider_message_id,
        )

        return {
            "status": "sent",
            "email_event_id": str(
                event.id,
            ),
            "provider_message_id": provider_message_id,
        }

    except BrevoEmailError as exc:
        mark_email_failed(
            event=event,
            error=exc,
        )

        raise


def build_email_params(
    event,
):
    """
    Build common transactional template parameters.

    Event-specific additions can be introduced here later.
    """

    organization = (
        event.organization
    )

    subscription = (
        event.subscription
    )

    params = {
        "organization_name": (
            organization.name
        ),
    }

    if subscription:
        params.update(
            {
                "plan_name": (
                    subscription.plan.name
                ),
                "billing_cycle": (
                    subscription.billing_cycle
                ),
                "start_date": (
                    subscription.start_date.strftime(
                        "%d %b %Y"
                    )
                    if subscription.start_date
                    else ""
                ),
                "expiry_date": (
                    subscription.expiry_date.strftime(
                        "%d %b %Y"
                    )
                    if subscription.expiry_date
                    else ""
                ),
            }
        )

    return params