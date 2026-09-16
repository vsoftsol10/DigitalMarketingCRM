import logging

from celery import shared_task

from .lifecycle import MetaTokenLifecycleService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def maintain_meta_tokens_task(self):
    """
    Periodic Facebook Page token lifecycle maintenance.

    The actual lifecycle logic lives inside
    MetaTokenLifecycleService.

    Celery is responsible only for scheduling/executing
    the lifecycle service.
    """

    service = MetaTokenLifecycleService()

    result = service.refresh_due_credentials()

    logger.info(
        "Meta Facebook Page token lifecycle task completed: %s",
        result,
    )

    return result
