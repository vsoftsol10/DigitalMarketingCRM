from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

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


@transaction.atomic
def expire_due_subscriptions():
    """
    Expire active subscriptions whose expiry date has passed.

    A subscription becomes expired only when:

        expiry_date < today

    After successful state transition, a PLAN_EXPIRED email
    event is queued for the primary organization contact.
    """

    today = timezone.localdate()

    subscriptions = (
        OrganizationSubscription.objects.select_for_update()
        .select_related(
            "organization",
            "plan",
        )
        .filter(
            is_current=True,
            status=SubscriptionStatus.ACTIVE,
            expiry_date__lt=today,
            is_deleted=False,
        )
    )

    expired_count = 0

    for subscription in subscriptions:
        # --------------------------------------------------------
        # EXPIRE SUBSCRIPTION
        # --------------------------------------------------------

        subscription.status = SubscriptionStatus.EXPIRED

        subscription.is_current = False

        subscription.save(
            update_fields=[
                "status",
                "is_current",
                "updated_at",
            ],
        )

        # --------------------------------------------------------
        # EXPIRED EMAIL
        # --------------------------------------------------------

        recipient_email, recipient_name = get_organization_billing_recipient(
            subscription.organization,
        )

        if recipient_email:
            queue_email_event(
                organization=(subscription.organization),
                subscription=subscription,
                event_type=(EmailEventType.PLAN_EXPIRED),
                recipient_email=recipient_email,
                recipient_name=recipient_name,
            )

        expired_count += 1

    return expired_count
