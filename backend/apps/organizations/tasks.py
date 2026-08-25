from celery import shared_task

from .services import activate_due_scheduled_subscriptions


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def activate_scheduled_subscriptions_task(self):
    """
    Activate scheduled subscriptions whose start date has arrived.
    """

    activated_count = activate_due_scheduled_subscriptions()

    return {
        "activated_count": activated_count,
    }
