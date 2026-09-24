import logging
from datetime import timedelta

from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.integrations.instagram.client import InstagramAPIClient
from apps.integrations.instagram.crypto import decrypt_token as decrypt_instagram_token
from apps.integrations.instagram.exceptions import InstagramAPIError
from apps.integrations.instagram.selectors import get_active_instagram_credential
from apps.social_accounts.models import SocialPlatform
from apps.activities.models import ActivityEventType, ActivitySource
from apps.activities.services import create_activity_log

from .models import Post, PostPlatform, PostStatus
from .publishing.exceptions import MediaProcessingPending
from .publishing.registry import get_publisher

logger = logging.getLogger(__name__)

AMBIGUOUS_INSTAGRAM_PUBLISH_PREFIX = "Instagram publish outcome could not be confirmed."
AMBIGUOUS_INSTAGRAM_RECONCILIATION_WINDOW = timedelta(hours=24)
AMBIGUOUS_INSTAGRAM_RECONCILIATION_BATCH_SIZE = 100


def _pending_retry_countdown(exc, retries):
    """Use bounded exponential backoff only for provider rate limits."""
    if getattr(exc, "rate_limited", False):
        return min(60 * (2 ** max(retries, 0)), 15 * 60)
    return 30


def _pending_retry_limit_reached(task):
    """Return whether this pending operation has consumed its final retry."""
    return task.request.retries >= task.max_retries


def _mark_pending_target_failed(target_id):
    """Finish an exhausted resumable operation without discarding provider state."""
    with transaction.atomic():
        target = PostPlatform.objects.select_for_update().filter(
            id=target_id,
            is_deleted=False,
            status=PostStatus.PUBLISHING,
        ).first()
        if not target:
            return
        target.status = PostStatus.FAILED
        target.error_message = (
            "Instagram media processing did not complete before the retry limit. "
            "Retry publishing to resume the existing provider container."
        )
        target.save(update_fields=["status", "error_message", "updated_at"])
        create_activity_log(
            organization=target.post.organization,
            post=target.post,
            post_platform=target,
            event_type=ActivityEventType.POST_FAILED,
            source=ActivitySource.SYSTEM,
            metadata={
                "platform": target.platform,
                "attempt_count": target.attempt_count,
            },
            idempotency_key=(
                f"post-platform:{target.id}:failed:"
                f"{target.attempt_count}:{target.updated_at.isoformat()}"
            ),
        )


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


def _safe_instagram_error_fields(exc):
    """Extract only approved provider diagnostics for reconciliation logs."""
    payload = getattr(exc, "error_payload", None)
    provider_error = payload.get("error", {}) if isinstance(payload, dict) else {}
    provider_error = provider_error if isinstance(provider_error, dict) else {}
    return {
        "message": provider_error.get("message"),
        "code": provider_error.get("code"),
        "error_subcode": provider_error.get("error_subcode"),
        "fbtrace_id": provider_error.get("fbtrace_id"),
    }


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
def publish_post_task(self, post_id, target_id=None):
    """Publish a stored post once per destination; never logs provider secrets."""
    post = Post.objects.filter(id=post_id, is_deleted=False).first()
    if not post:
        return
    # Target-specific Calendar dispatches must not be blocked by aggregate
    # parent state (for example, PARTIALLY_PUBLISHED after a sibling succeeds).
    if not target_id and post.status not in {PostStatus.PUBLISHING, PostStatus.SCHEDULED}:
        return
    targets = PostPlatform.objects.filter(
        post=post,
        is_deleted=False,
    )
    if target_id:
        targets = targets.filter(id=target_id)
    targets = targets.select_related("social_account", "social_account__connection")
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
                if target.status in {
                    PostStatus.PUBLISHED,
                    PostStatus.FAILED,
                    PostStatus.UNRESOLVED,
                }:
                    continue
                # Unknown in-progress calls are not replayed automatically.
                # Instagram is the exception: media_publish is reached only
                # after provider_container_id is durably saved. Without that
                # ID, replaying can at most create an orphaned, unpublished
                # container; it cannot replay a published Instagram post.
                # This lets a pre-container MediaProcessingPending retry make
                # forward progress while retaining the guard for Facebook and
                # any other publisher whose external side effect is unknown.
                if (
                    target.status == PostStatus.PUBLISHING
                    and target.publish_started_at
                    and not target.provider_container_id
                    and not target.provider_state
                    and target.platform != SocialPlatform.INSTAGRAM
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
                create_activity_log(
                    organization=target.post.organization,
                    post=target.post,
                    post_platform=target,
                    event_type=ActivityEventType.POST_PUBLISHED,
                    source=ActivitySource.SYSTEM,
                    metadata={"platform": target.platform},
                    idempotency_key=(
                        f"post-platform:{target.id}:published:"
                        f"{target.published_at.isoformat()}"
                    ),
                )
        except MediaProcessingPending as exc:
            logger.info(
                "Post target media is still processing. target_id=%s",
                target.id,
            )
            if _pending_retry_limit_reached(self):
                logger.warning(
                    "Post target media processing exhausted retries. target_id=%s",
                    target.id,
                )
                _mark_pending_target_failed(target.id)
                continue
            raise self.retry(
                exc=exc,
                countdown=_pending_retry_countdown(exc, self.request.retries),
            )
        except Exception as exc:
            error_message = _format_publish_error(exc)
            if getattr(exc, "ambiguous_media_publish", False):
                logger.warning(
                    "Post target publishing outcome is unresolved. target_id=%s error=%s",
                    target.id,
                    error_message,
                )
                with transaction.atomic():
                    target = PostPlatform.objects.select_for_update().get(id=target.id)
                    if target.status == PostStatus.PUBLISHING:
                        target.status = PostStatus.UNRESOLVED
                        target.error_message = error_message[:1000]
                        target.save(update_fields=["status", "error_message", "updated_at"])
                continue
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
                create_activity_log(
                    organization=target.post.organization,
                    post=target.post,
                    post_platform=target,
                    event_type=ActivityEventType.POST_FAILED,
                    source=ActivitySource.SYSTEM,
                    metadata={
                        "platform": target.platform,
                        "attempt_count": target.attempt_count,
                    },
                    idempotency_key=(
                        f"post-platform:{target.id}:failed:"
                        f"{target.attempt_count}:{target.updated_at.isoformat()}"
                    ),
                )
        finally:
            cache.delete(lock_key)
    _update_post_status(post.id)


@shared_task
def reconcile_ambiguous_instagram_publishes_task():
    """Read-only reconciliation for bounded unresolved Instagram outcomes."""
    cutoff = timezone.now() - AMBIGUOUS_INSTAGRAM_RECONCILIATION_WINDOW
    target_ids = list(
        PostPlatform.objects.filter(
            is_deleted=False,
            platform=SocialPlatform.INSTAGRAM,
            status=PostStatus.UNRESOLVED,
            error_message__startswith=AMBIGUOUS_INSTAGRAM_PUBLISH_PREFIX,
            provider_container_id__gt="",
            updated_at__gte=cutoff,
        )
        .order_by("updated_at")
        .values_list("id", flat=True)[:AMBIGUOUS_INSTAGRAM_RECONCILIATION_BATCH_SIZE]
    )

    for target_id in target_ids:
        lock_key = f"posts:instagram-reconcile:{target_id}"
        if not cache.add(lock_key, "1", timeout=5 * 60):
            continue
        try:
            target = (
                PostPlatform.objects.select_related("post", "social_account")
                .filter(
                    id=target_id,
                    is_deleted=False,
                    platform=SocialPlatform.INSTAGRAM,
                    status=PostStatus.UNRESOLVED,
                    error_message__startswith=AMBIGUOUS_INSTAGRAM_PUBLISH_PREFIX,
                )
                .first()
            )
            if not target or not target.social_account or not target.provider_container_id:
                continue

            credential = get_active_instagram_credential(
                social_account=target.social_account,
            )
            if not credential:
                logger.warning(
                    "Instagram ambiguous publish reconciliation skipped without an active credential. "
                    "target_id=%s container_id=%s",
                    target.id,
                    target.provider_container_id,
                )
                continue

            api = InstagramAPIClient()
            try:
                state = api.graph_get(
                    target.provider_container_id,
                    access_token=decrypt_instagram_token(
                        credential.encrypted_access_token,
                    ),
                    params={"fields": "status_code"},
                )
            except InstagramAPIError as exc:
                diagnostics = _safe_instagram_error_fields(exc)
                logger.warning(
                    "Instagram ambiguous publish reconciliation request failed. "
                    "target_id=%s container_id=%s http_status=%s message=%s "
                    "code=%s error_subcode=%s fbtrace_id=%s",
                    target.id,
                    target.provider_container_id,
                    exc.status_code,
                    diagnostics["message"],
                    diagnostics["code"],
                    diagnostics["error_subcode"],
                    diagnostics["fbtrace_id"],
                )
                continue

            status_code = state.get("status_code") if isinstance(state, dict) else None
            logger.info(
                "Instagram ambiguous publish reconciliation status. target_id=%s "
                "container_id=%s http_status=%s status_code=%s",
                target.id,
                target.provider_container_id,
                getattr(api, "last_response_status_code", None),
                status_code,
            )

            if status_code != "PUBLISHED":
                continue

            with transaction.atomic():
                target = PostPlatform.objects.select_for_update().filter(
                    id=target.id,
                    is_deleted=False,
                    platform=SocialPlatform.INSTAGRAM,
                    status=PostStatus.UNRESOLVED,
                    error_message__startswith=AMBIGUOUS_INSTAGRAM_PUBLISH_PREFIX,
                ).first()
                if not target:
                    continue
                if status_code == "PUBLISHED":
                    target.status = PostStatus.PUBLISHED
                    target.published_at = timezone.now()
                    target.error_message = ""
                    target.save(update_fields=[
                        "status",
                        "published_at",
                        "error_message",
                        "updated_at",
                    ])
                    create_activity_log(
                        organization=target.post.organization,
                        post=target.post,
                        post_platform=target,
                        event_type=ActivityEventType.POST_PUBLISHED,
                        source=ActivitySource.SYSTEM,
                        metadata={"platform": target.platform},
                        idempotency_key=(
                            f"post-platform:{target.id}:published:"
                            f"{target.published_at.isoformat()}"
                        ),
                    )
            _update_post_status(target.post_id)
        finally:
            cache.delete(lock_key)


@shared_task
def dispatch_due_posts_task():
    """Claim due scheduled posts and route them through the same publisher."""
    # Retain the post-level path only for legacy scheduled posts whose
    # destinations do not yet carry target-level schedules. New schedules are
    # claimed exclusively by the target loop below.
    due = Post.objects.filter(
        is_deleted=False,
        status=PostStatus.SCHEDULED,
        scheduled_at__lte=timezone.now(),
    ).exclude(
        platforms__is_deleted=False,
        platforms__status=PostStatus.SCHEDULED,
    ).values_list("id", flat=True)[:100]
    for post_id in due:
        with transaction.atomic():
            post = Post.objects.select_for_update(skip_locked=True).filter(id=post_id, status=PostStatus.SCHEDULED).first()
            if not post:
                continue
            post.status = PostStatus.PUBLISHING
            post.save(update_fields=["status", "updated_at"])
        publish_post_task.delay(str(post_id))

    # Calendar may schedule a single PostPlatform destination. These use the
    # same publisher task, constrained to the claimed target.
    due_target_ids = (
        PostPlatform.objects.filter(
            is_deleted=False,
            status=PostStatus.SCHEDULED,
            scheduled_at__lte=timezone.now(),
            post__is_deleted=False,
        )
        .values_list("id", flat=True)[:100]
    )
    for target_id in due_target_ids:
        with transaction.atomic():
            target = (
                PostPlatform.objects.select_for_update(skip_locked=True)
                .filter(
                    id=target_id,
                    is_deleted=False,
                    status=PostStatus.SCHEDULED,
                )
                .first()
            )
            if not target:
                continue
            post = Post.objects.select_for_update().filter(
                id=target.post_id,
                is_deleted=False,
            ).first()
            if not post:
                continue
            target.status = PostStatus.PUBLISHING
            target.save(update_fields=["status", "updated_at"])
            if post.status != PostStatus.PUBLISHING:
                post.status = PostStatus.PUBLISHING
                post.save(update_fields=["status", "updated_at"])
        publish_post_task.delay(str(post.id), str(target.id))
