from django.db import transaction
from django.utils import timezone


@transaction.atomic
def expire_due_subscriptions():
    """
    Mark subscriptions as expired when their expiry date
    has passed.

    A subscription is considered expired only when:
        expiry_date < today
    """

    from .models import OrganizationSubscription

    today = timezone.localdate()

    updated_count = (
        OrganizationSubscription.objects
        .filter(
            is_current=True,
            status="active",
            expiry_date__lt=today,
        )
        .update(
            status="expired",
            is_current=False,
        )
    )

    return updated_count