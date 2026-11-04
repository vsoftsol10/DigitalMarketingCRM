"""Scheduled cleanup for expired invitation OAuth and delivery secrets."""

from celery import shared_task

from .invitations import cleanup_expired_invitation_oauth_secrets


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def cleanup_invitation_oauth_secrets_task(self):
    """Clear one bounded batch of expired or invalid invitation secrets."""
    return cleanup_expired_invitation_oauth_secrets(batch_size=200)
