import logging

from celery import shared_task

from .lifecycle import InstagramTokenLifecycleService

logger = logging.getLogger(__name__)


# ============================================================
# INSTAGRAM TOKEN LIFECYCLE
# ============================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def maintain_instagram_tokens_task(
    self,
):
    """
    Maintain active Instagram long-lived access tokens.

    The lifecycle service:
        - checks token expiry,
        - refreshes tokens before expiry,
        - marks expired credentials,
        - handles provider errors,
        - updates SocialAccount state.

    Celery is responsible only for scheduling and retrying
    unexpected task-level failures.
    """

    service = InstagramTokenLifecycleService()

    result = service.refresh_due_credentials()

    logger.info(
        "Instagram token lifecycle completed: %s",
        result,
    )

    return result
