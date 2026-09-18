import logging

from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import Post, PostPlatform, PostStatus
from .publishing.exceptions import MediaProcessingPending
from .publishing.registry import get_publisher

logger = logging.getLogger(__name__)


def _format_publish_error(exc):
    """Keep actionable provider details without logging credentials."""
    message = str(exc)
    payload = getattr(exc, "error_payload", None)

    if not isinstance(payload, dict):
        return message

    provider_error = payload.get("error")
    if not isinstance(provider_error, dict):
        return message

    provider_message = str(provider_error.get("message") or "").strip()
    provider_code = provider_error.get("code")

    if not provider_message:
        return message

    details = f"Provider error: {provider_message}"
    if provider_code is not None:
        details = f"{details} (code {provider_code})"

    return f"{message} {details}"


def _update_post_status(post_id):
    targets = PostPlatform.objects.filter(post_id=post_id, is_deleted=False)
    statuses = set(targets.values_list("status", flat=True))
    if statuses == {PostStatus.PUBLISHED}:
        Post.objects.filter(id=post_id).update(status=PostStatus.PUBLISHED, published_at=timezone.now(), error_message="")
    elif PostStatus.PUBLISHED in statuses:
        Post.objects.filter(id=post_id).update(status=PostStatus.PARTIALLY_PUBLISHED)
    elif PostStatus.FAILED in statuses and PostStatus.PUBLISHING not in statuses:
        error_message = (
            targets.filter(status=PostStatus.FAILED)
            .exclude(error_message="")
            .values_list("error_message", flat=True)
            .first()
            or "One or more publishing targets failed."
        )
        Post.objects.filter(id=post_id).update(
            status=PostStatus.FAILED,
            error_message=error_message[:1000],
        )


@shared_task(bind=True, autoretry_for=(), max_retries=20)
def publish_post_task(self, post_id):
    """Publish a stored post once per destination; never logs provider secrets."""
    post = Post.objects.filter(id=post_id, is_deleted=False).first()
    if not post or post.status not in {PostStatus.PUBLISHING, PostStatus.SCHEDULED}:
        return
    targets = PostPlatform.objects.filter(post=post, is_deleted=False).select_related("social_account", "social_account__connection")
    for target in targets:
        lock_key = f"posts:publish:{target.idempotency_key}"
        if not cache.add(lock_key, "1", timeout=30 * 60):
            continue
        try:
            with transaction.atomic():
                target = (
                    PostPlatform.objects.select_for_update(of=("self",))
                    .select_related("post", "social_account", "social_account__connection")
                    .get(id=target.id)
                )
                if target.status in {PostStatus.PUBLISHED, PostStatus.FAILED}:
                    continue
                # Unknown in-progress calls are not replayed automatically.
                # Provider container state is safe to resume after asynchronous
                # media processing has completed.
                if (
                    target.status == PostStatus.PUBLISHING
                    and target.publish_started_at
                    and not target.provider_container_id
                    and not target.provider_state
                ):
                    continue
                target.status = PostStatus.PUBLISHING
                target.publish_started_at = timezone.now()
                target.attempt_count += 1
                target.save(update_fields=["status", "publish_started_at", "attempt_count", "updated_at"])
            provider = (
                target.social_account.connection.provider
                if target.social_account.connection_id
                else "meta"
            )
            publisher = get_publisher(provider=provider)
            result = publisher.publish(post_platform=target)
            with transaction.atomic():
                target = PostPlatform.objects.select_for_update().get(id=target.id)
                target.status = PostStatus.PUBLISHED
                target.external_post_id = result["external_post_id"]
                target.provider_container_id = result.get("provider_container_id", target.provider_container_id)
                target.published_at = timezone.now()
                target.error_message = ""
                target.save(update_fields=["status", "external_post_id", "provider_container_id", "published_at", "error_message", "updated_at"])
        except MediaProcessingPending as exc:
            logger.info(
                "Post target media is still processing. target_id=%s",
                target.id,
            )
            raise self.retry(exc=exc, countdown=30)
        except Exception as exc:
            error_message = _format_publish_error(exc)
            logger.warning(
                "Post target publishing failed. target_id=%s error_type=%s error=%s",
                target.id,
                type(exc).__name__,
                error_message,
            )
            with transaction.atomic():
                target = PostPlatform.objects.select_for_update().get(id=target.id)
                target.status = PostStatus.FAILED
                target.error_message = error_message[:1000]
                target.save(update_fields=["status", "error_message", "updated_at"])
        finally:
            cache.delete(lock_key)
    _update_post_status(post.id)


@shared_task
def dispatch_due_posts_task():
    """Claim due scheduled posts and route them through the same publisher."""
    due = Post.objects.filter(is_deleted=False, status=PostStatus.SCHEDULED, scheduled_at__lte=timezone.now()).values_list("id", flat=True)[:100]
    for post_id in due:
        with transaction.atomic():
            post = Post.objects.select_for_update(skip_locked=True).filter(id=post_id, status=PostStatus.SCHEDULED).first()
            if not post:
                continue
            post.status = PostStatus.PUBLISHING
            post.save(update_fields=["status", "updated_at"])
        publish_post_task.delay(str(post_id))
