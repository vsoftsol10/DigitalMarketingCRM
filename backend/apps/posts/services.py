from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from django.utils import timezone

from apps.integrations.instagram.selectors import get_active_instagram_credential
from apps.integrations.meta.credentials import MetaCredentialService
from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)
from apps.activities.models import ActivityEventType, ActivitySource
from apps.activities.services import create_activity_log

from .models import (
    Post,
    PostMedia,
    PostPlatform,
    PostPublishType,
    PostStatus,
)

from PIL import Image

from django.db import transaction

from .models import PostMedia, PostMediaType

# ============================================================
# CREATE POST
# ============================================================


@transaction.atomic
def create_post(
    *,
    organization,
    created_by,
    validated_data,
):
    """
    Create a post together with its exact social-account targets
    and media.

    This service handles database persistence only.

    Actual provider publishing is handled by the publishing
    / integration layer.
    """

    targets = validated_data.pop(
        "targets",
        [],
    )

    media_items = validated_data.pop(
        "media",
        [],
    )

    publish_date = validated_data.pop(
        "publish_date",
        None,
    )

    publish_time = validated_data.pop(
        "publish_time",
        None,
    )

    timezone_name = validated_data.get(
        "timezone",
        "UTC",
    )

    publish_type = validated_data.get(
        "publish_type",
        PostPublishType.DRAFT,
    )

    validate_target_accounts(
        organization=organization,
        targets=targets,
        require_publishable=publish_type != PostPublishType.DRAFT,
    )

    scheduled_at = build_scheduled_at(
        publish_type=publish_type,
        publish_date=publish_date,
        publish_time=publish_time,
        timezone_name=timezone_name,
    )

    status = get_initial_post_status(
        publish_type=publish_type,
    )

    post = Post.objects.create(
        organization=organization,
        created_by=created_by,
        scheduled_at=scheduled_at,
        status=status,
        **validated_data,
    )

    create_post_platforms(
        post=post,
        organization=organization,
        targets=targets,
    )

    # The post retains the aggregate schedule for existing post-level
    # workflows, while each destination owns its executable lifecycle.
    if publish_type == PostPublishType.SCHEDULE:
        PostPlatform.objects.filter(
            post=post,
            is_deleted=False,
        ).update(
            status=PostStatus.SCHEDULED,
            scheduled_at=scheduled_at,
            scheduled_timezone=timezone_name,
        )

    create_post_media(
        post=post,
        media_items=media_items,
    )

    create_activity_log(
        organization=organization,
        post=post,
        event_type=ActivityEventType.POST_CREATED,
        source=ActivitySource.USER if created_by else ActivitySource.SYSTEM,
        actor=created_by,
        metadata={"publish_type": post.publish_type},
    )

    if publish_type == PostPublishType.SCHEDULE:
        create_activity_log(
            organization=organization,
            post=post,
            event_type=ActivityEventType.POST_SCHEDULED,
            source=ActivitySource.USER if created_by else ActivitySource.SYSTEM,
            actor=created_by,
            metadata={
                "schedule_scope": "POST",
                "scheduled_at": scheduled_at.isoformat(),
                "timezone": timezone_name,
            },
            idempotency_key=(
                f"post:{post.id}:scheduled:aggregate:{scheduled_at.isoformat()}"
            ),
        )

    if publish_type == PostPublishType.NOW:
        transaction.on_commit(lambda: enqueue_post_publication(post.id))

    return post


# ============================================================
# VALIDATE TARGET ACCOUNTS
# ============================================================


def validate_target_accounts(
    *,
    organization,
    targets,
    require_publishable=True,
):
    """
    Ensure every selected SocialAccount belongs to the same
    organization as the post.

    This is an important tenant-isolation check.
    """

    if not targets:
        raise ValueError(
            "At least one social account target is required.",
        )

    social_account_ids = [item["social_account"] for item in targets]

    accounts = SocialAccount.objects.filter(
        id__in=social_account_ids,
        organization=organization,
        is_deleted=False,
    ).select_related(
        "connection",
    )

    account_map = {str(account.id): account for account in accounts}

    missing_accounts = []

    for social_account_id in social_account_ids:
        if str(social_account_id) not in account_map:
            missing_accounts.append(
                str(social_account_id),
            )

    if missing_accounts:
        raise ValueError(
            "One or more selected social accounts do not belong "
            "to the organization or are unavailable.",
        )

    if not require_publishable:
        return account_map

    for account in accounts:
        if (
            account.status != SocialAccountStatus.CONNECTED
            or not account.is_valid
        ):
            raise ValueError("A selected social account is not publishable.")

        # Resolve through the existing credential layers. Tokens are never
        # retained or returned by posts; this only verifies publish readiness.
        if account.platform == SocialPlatform.FACEBOOK:
            MetaCredentialService.get_access_token(social_account=account)
        elif account.platform == SocialPlatform.INSTAGRAM:
            if not get_active_instagram_credential(social_account=account):
                raise ValueError("Instagram credential is not active.")
        else:
            raise ValueError("Publishing is not configured for this platform.")

    return account_map


# ============================================================
# INITIAL POST STATUS
# ============================================================


def get_initial_post_status(
    *,
    publish_type,
):
    """
    Determine initial persisted state.

    NOW starts as PUBLISHING because the publishing layer will
    be invoked after persistence.

    A later publishing-job implementation should move the actual
    provider execution to a background worker.
    """

    if publish_type == PostPublishType.SCHEDULE:
        return PostStatus.SCHEDULED

    if publish_type == PostPublishType.NOW:
        return PostStatus.PUBLISHING

    return PostStatus.DRAFT


# ============================================================
# BUILD SCHEDULED DATETIME
# ============================================================


def build_scheduled_at(
    *,
    publish_type,
    publish_date=None,
    publish_time=None,
    timezone_name="UTC",
):
    """
    Convert local date/time + IANA timezone into an aware
    datetime.

    DRAFT and NOW posts do not receive scheduled_at.
    """

    if publish_type != PostPublishType.SCHEDULE:
        return None

    if not publish_date or not publish_time:
        raise ValueError(
            "Publish date and publish time are required for scheduled posts.",
        )

    timezone_name = (timezone_name or "UTC").strip() or "UTC"

    try:
        selected_timezone = ZoneInfo(
            timezone_name,
        )
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"Invalid timezone: {timezone_name}.",
        ) from exc

    naive_datetime = timezone.datetime.combine(
        publish_date,
        publish_time,
    )

    return naive_datetime.replace(
        tzinfo=selected_timezone,
    )


# ============================================================
# CREATE POST PLATFORMS
# ============================================================


def create_post_platforms(
    *,
    post,
    organization,
    targets,
):
    """
    Create one PostPlatform row per exact SocialAccount target.

    The platform value is derived from SocialAccount rather than
    trusted from the client.
    """

    if not targets:
        raise ValueError(
            "At least one social account target is required.",
        )

    social_account_ids = [item["social_account"] for item in targets]

    accounts = SocialAccount.objects.filter(
        id__in=social_account_ids,
        organization=organization,
        is_deleted=False,
    )

    account_map = {str(account.id): account for account in accounts}

    post_platforms = []

    for target in targets:
        social_account_id = str(
            target["social_account"],
        )

        social_account = account_map.get(
            social_account_id,
        )

        if not social_account:
            raise ValueError(
                "Selected social account is unavailable.",
            )

        post_platforms.append(
            PostPlatform(
                post=post,
                platform=social_account.platform,
                social_account=social_account,
                content_type=(
                    target.get(
                        "content_type",
                        "",
                    )
                    or ""
                ),
                status=PostStatus.DRAFT,
            )
        )

    PostPlatform.objects.bulk_create(
        post_platforms,
    )

    return post_platforms


# ============================================================
# CREATE POST MEDIA
# ============================================================


def create_post_media(
    *,
    post,
    media_items,
):
    """
    Create PostMedia records.
    """

    post_media_items = []

    for index, media in enumerate(
        media_items,
    ):
        uploaded_file = media.get(
            "file",
        )

        if not uploaded_file:
            raise ValueError(
                "Media file is required.",
            )

        media_type = media.get(
            "media_type",
        )

        post_media_items.append(
            PostMedia(
                post=post,
                media_type=media_type,
                file=uploaded_file,
                original_filename=getattr(
                    uploaded_file,
                    "name",
                    "",
                ),
                mime_type=getattr(
                    uploaded_file,
                    "content_type",
                    "",
                ),
                file_size=getattr(
                    uploaded_file,
                    "size",
                    None,
                ),
                sort_order=index,
            )
        )

    if post_media_items:
        PostMedia.objects.bulk_create(
            post_media_items,
        )

    return post_media_items


# ============================================================
# UPLOAD SINGLE POST MEDIA
# ============================================================


@transaction.atomic
def upload_post_media(*, post, uploaded_file, media_type):
    """
    Upload and persist a single media file for an existing post.

    Database persistence only.
    Provider publishing is handled by the publishing layer.
    """

    if not uploaded_file:
        raise ValueError("Media file is required.")

    if not media_type:
        raise ValueError("Media type is required.")

    mime_type = getattr(uploaded_file, "content_type", "") or ""

    if media_type == PostMediaType.IMAGE:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)

        mime_type_map = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
        }

        mime_type = mime_type_map.get(
            image.format,
            mime_type,
        )

        uploaded_file.seek(0)

    sort_order = PostMedia.objects.filter(
        post=post,
        is_deleted=False,
    ).count()

    media = PostMedia.objects.create(
        post=post,
        media_type=media_type,
        file=uploaded_file,
        original_filename=getattr(uploaded_file, "name", ""),
        mime_type=mime_type,
        file_size=getattr(uploaded_file, "size", None),
        sort_order=sort_order,
    )

    return media


# ============================================================
# UPDATE POST
# ============================================================


@transaction.atomic
def update_post(
    *,
    post,
    validated_data,
):
    """
    Update an existing post.

    Targets and media are replaced only when explicitly supplied.

    Existing scheduled values are preserved for partial updates.
    """

    targets = validated_data.pop(
        "targets",
        None,
    )

    media_items = validated_data.pop(
        "media",
        None,
    )

    publish_date = validated_data.pop(
        "publish_date",
        None,
    )

    publish_time = validated_data.pop(
        "publish_time",
        None,
    )

    publish_type = validated_data.get(
        "publish_type",
        post.publish_type,
    )

    timezone_name = validated_data.get(
        "timezone",
        post.timezone or "UTC",
    )

    # ---------------------------------------------------------
    # Schedule handling
    # ---------------------------------------------------------

    if publish_type == PostPublishType.SCHEDULE:
        final_publish_date = (
            publish_date
            if publish_date is not None
            else (post.scheduled_at.date() if post.scheduled_at else None)
        )

        final_publish_time = (
            publish_time
            if publish_time is not None
            else (
                post.scheduled_at.timetz().replace(
                    tzinfo=None,
                )
                if post.scheduled_at
                else None
            )
        )

        if not final_publish_date:
            raise ValueError(
                "Publish date is required for scheduled posts.",
            )

        if not final_publish_time:
            raise ValueError(
                "Publish time is required for scheduled posts.",
            )

        post.scheduled_at = build_scheduled_at(
            publish_type=PostPublishType.SCHEDULE,
            publish_date=final_publish_date,
            publish_time=final_publish_time,
            timezone_name=timezone_name,
        )

        post.status = PostStatus.SCHEDULED

    elif publish_type == PostPublishType.DRAFT:
        post.scheduled_at = None
        post.status = PostStatus.DRAFT

    elif publish_type == PostPublishType.NOW:
        post.scheduled_at = None
        post.status = PostStatus.PUBLISHING

    # ---------------------------------------------------------
    # Normal fields
    # ---------------------------------------------------------

    for field, value in validated_data.items():
        setattr(
            post,
            field,
            value,
        )

    post.save()

    # ---------------------------------------------------------
    # Replace targets
    # ---------------------------------------------------------

    if targets is not None:
        validate_target_accounts(
            organization=post.organization,
            targets=targets,
            require_publishable=publish_type != PostPublishType.DRAFT,
        )

        PostPlatform.objects.filter(
            post=post,
            is_deleted=False,
        ).update(
            is_deleted=True,
        )

        create_post_platforms(
            post=post,
            organization=post.organization,
            targets=targets,
        )

    # ---------------------------------------------------------
    # Replace media
    # ---------------------------------------------------------

    if media_items is not None:
        PostMedia.objects.filter(
            post=post,
            is_deleted=False,
        ).update(
            is_deleted=True,
        )

        create_post_media(
            post=post,
            media_items=media_items,
        )

    if publish_type == PostPublishType.SCHEDULE:
        PostPlatform.objects.filter(
            post=post,
            is_deleted=False,
        ).update(
            status=PostStatus.SCHEDULED,
            scheduled_at=post.scheduled_at,
            scheduled_timezone=timezone_name,
        )

    return post


def enqueue_post_publication(post_id):
    """Queue publishing after the post transaction has committed."""
    from .tasks import publish_post_task

    publish_post_task.delay(str(post_id))


def enqueue_post_target_publication(post_id, target_id):
    """Queue one exact destination without widening a retry to other targets."""
    from .tasks import publish_post_task

    publish_post_task.delay(str(post_id), str(target_id))


def _active_target_inputs(post):
    return [
        {
            "social_account": target.social_account_id,
            "content_type": target.content_type,
        }
        for target in PostPlatform.objects.filter(
            post=post,
            is_deleted=False,
        )
    ]


@transaction.atomic
def schedule_post(
    *,
    post_id,
    organization_id,
    publish_date,
    publish_time,
    timezone_name,
    reschedule=False,
    actor=None,
):
    """Schedule or reschedule a post while preventing concurrent publication."""
    post = Post.objects.select_for_update().filter(
        id=post_id,
        organization_id=organization_id,
        is_deleted=False,
    ).first()
    if not post:
        raise ValueError("Post not found.")

    required_status = PostStatus.SCHEDULED if reschedule else PostStatus.DRAFT
    if post.status != required_status:
        action = "rescheduled" if reschedule else "scheduled"
        raise ValueError(f"Only {required_status.lower()} posts can be {action}.")

    scheduled_at = build_scheduled_at(
        publish_type=PostPublishType.SCHEDULE,
        publish_date=publish_date,
        publish_time=publish_time,
        timezone_name=timezone_name,
    )
    if scheduled_at <= timezone.now():
        raise ValueError("Scheduled publishing must be in the future.")

    validate_target_accounts(
        organization=post.organization,
        targets=_active_target_inputs(post),
        require_publishable=True,
    )
    post.publish_type = PostPublishType.SCHEDULE
    post.status = PostStatus.SCHEDULED
    post.scheduled_at = scheduled_at
    post.timezone = timezone_name
    post.error_message = ""
    post.save(update_fields=[
        "publish_type", "status", "scheduled_at", "timezone",
        "error_message", "updated_at",
    ])
    PostPlatform.objects.select_for_update().filter(
        post=post,
        is_deleted=False,
    ).update(
        status=PostStatus.SCHEDULED,
        scheduled_at=scheduled_at,
        scheduled_timezone=timezone_name,
        error_message="",
    )
    create_activity_log(
        organization=post.organization,
        post=post,
        event_type=ActivityEventType.POST_SCHEDULED,
        source=ActivitySource.USER if actor else ActivitySource.SYSTEM,
        actor=actor,
        metadata={
            "schedule_scope": "POST",
            "scheduled_at": scheduled_at.isoformat(),
            "timezone": timezone_name,
        },
        idempotency_key=(
            f"post:{post.id}:scheduled:aggregate:{scheduled_at.isoformat()}"
        ),
    )
    return post


@transaction.atomic
def schedule_post_target(
    *,
    post_id,
    organization_id,
    target_id,
    publish_date,
    publish_time,
    timezone_name,
    actor=None,
):
    """Schedule one Calendar-selected destination without changing siblings."""
    post = Post.objects.select_for_update().filter(
        id=post_id,
        organization_id=organization_id,
        is_deleted=False,
    ).first()
    if not post:
        raise ValueError("Post not found.")

    target = PostPlatform.objects.select_for_update().filter(
        id=target_id,
        post=post,
        is_deleted=False,
        status__in=[PostStatus.DRAFT, PostStatus.SCHEDULED],
    ).first()
    if not target:
        raise ValueError("Only draft or scheduled publishing targets can be scheduled.")

    scheduled_at = build_scheduled_at(
        publish_type=PostPublishType.SCHEDULE,
        publish_date=publish_date,
        publish_time=publish_time,
        timezone_name=timezone_name,
    )
    if scheduled_at <= timezone.now():
        raise ValueError("Scheduled publishing must be in the future.")

    validate_target_accounts(
        organization=post.organization,
        targets=[{
            "social_account": target.social_account_id,
            "content_type": target.content_type,
        }],
        require_publishable=True,
    )
    target.status = PostStatus.SCHEDULED
    target.scheduled_at = scheduled_at
    target.scheduled_timezone = timezone_name
    target.error_message = ""
    target.save(update_fields=[
        "status", "scheduled_at", "scheduled_timezone", "error_message", "updated_at",
    ])
    create_activity_log(
        organization=post.organization,
        post=post,
        post_platform=target,
        event_type=ActivityEventType.POST_SCHEDULED,
        source=ActivitySource.USER if actor else ActivitySource.SYSTEM,
        actor=actor,
        metadata={
            "schedule_scope": "POST_PLATFORM",
            "platform": target.platform,
            "scheduled_at": scheduled_at.isoformat(),
            "timezone": timezone_name,
        },
        idempotency_key=(
            f"post-platform:{target.id}:scheduled:{scheduled_at.isoformat()}"
        ),
    )
    return target


@transaction.atomic
def publish_post_now(*, post_id, organization_id):
    """Claim a draft or scheduled post for immediate publishing after commit."""
    post = Post.objects.select_for_update().filter(
        id=post_id,
        organization_id=organization_id,
        is_deleted=False,
        status__in=[PostStatus.DRAFT, PostStatus.SCHEDULED],
    ).first()
    if not post:
        raise ValueError("Only draft or scheduled posts can be published now.")

    validate_target_accounts(
        organization=post.organization,
        targets=_active_target_inputs(post),
        require_publishable=True,
    )
    post.publish_type = PostPublishType.NOW
    post.status = PostStatus.PUBLISHING
    post.scheduled_at = None
    post.error_message = ""
    post.save(update_fields=[
        "publish_type", "status", "scheduled_at", "error_message", "updated_at",
    ])
    transaction.on_commit(lambda: enqueue_post_publication(post.id))
    return post


@transaction.atomic
def publish_post_target_now(*, post_id, organization_id, target_id):
    """Immediately publish one Calendar-selected destination only."""
    post = Post.objects.select_for_update().filter(
        id=post_id,
        organization_id=organization_id,
        is_deleted=False,
        status__in=[PostStatus.DRAFT, PostStatus.SCHEDULED],
    ).first()
    if not post:
        raise ValueError("Only draft or scheduled posts can be published now.")

    target = PostPlatform.objects.select_for_update().filter(
        id=target_id,
        post=post,
        is_deleted=False,
        status__in=[PostStatus.DRAFT, PostStatus.SCHEDULED],
    ).first()
    if not target:
        raise ValueError("Only draft or scheduled publishing targets can be published now.")

    validate_target_accounts(
        organization=post.organization,
        targets=[{
            "social_account": target.social_account_id,
            "content_type": target.content_type,
        }],
        require_publishable=True,
    )
    target.scheduled_at = None
    target.scheduled_timezone = ""
    target.status = PostStatus.PUBLISHING
    target.save(update_fields=[
        "status", "scheduled_at", "scheduled_timezone", "updated_at",
    ])
    post.publish_type = PostPublishType.NOW
    post.status = PostStatus.PUBLISHING
    post.scheduled_at = None
    post.error_message = ""
    post.save(update_fields=[
        "publish_type", "status", "scheduled_at", "error_message", "updated_at",
    ])
    transaction.on_commit(
        lambda: enqueue_post_target_publication(post.id, target.id)
    )
    return post, target


@transaction.atomic
def retry_post_target(*, post_id, organization_id, target_id):
    """Retry one failed destination while retaining provider resume state."""
    post = Post.objects.select_for_update().filter(
        id=post_id,
        organization_id=organization_id,
        is_deleted=False,
    ).first()
    if not post:
        raise ValueError("Post not found.")

    target = PostPlatform.objects.select_for_update().filter(
        id=target_id,
        post=post,
        is_deleted=False,
        status=PostStatus.FAILED,
    ).first()
    if not target:
        raise ValueError("Only failed publishing targets can be retried.")

    # Do not clear provider_container_id or provider_state: publishers use
    # those values to safely resume asynchronous provider work.
    target.status = PostStatus.PUBLISHING
    target.scheduled_at = None
    target.scheduled_timezone = ""
    target.error_message = ""
    target.save(update_fields=[
        "status", "scheduled_at", "scheduled_timezone", "error_message", "updated_at",
    ])

    post.status = PostStatus.PUBLISHING
    post.scheduled_at = None
    post.error_message = ""
    post.retry_count += 1
    post.save(update_fields=[
        "status", "scheduled_at", "error_message", "retry_count", "updated_at",
    ])
    transaction.on_commit(lambda: enqueue_post_target_publication(post.id, target.id))
    return post, target


@transaction.atomic
def delete_post_target(*, post_id, organization_id, target_id):
    """Deactivate one destination without deleting its shared post or media."""
    post = Post.objects.select_for_update().filter(
        id=post_id,
        organization_id=organization_id,
        is_deleted=False,
    ).first()
    if not post:
        raise ValueError("Post not found.")

    target = PostPlatform.objects.select_for_update().filter(
        id=target_id,
        post=post,
        is_deleted=False,
    ).first()
    if not target:
        raise ValueError("Publishing target not found.")
    if target.status == PostStatus.PUBLISHED:
        raise ValueError("Published publishing targets cannot be deleted.")
    if target.status == PostStatus.PUBLISHING:
        raise ValueError("A publishing target that is currently publishing cannot be deleted.")

    target.is_deleted = True
    target.save(update_fields=["is_deleted", "updated_at"])
    return target


# ============================================================
# DELETE POST
# ============================================================


@transaction.atomic
def delete_post(
    *,
    post,
):
    """
    Soft-delete a post and its active child records.
    """

    post = Post.objects.select_for_update().filter(
        id=post.id,
        is_deleted=False,
    ).first()
    if not post:
        raise ValueError("Post not found.")

    if post.status == PostStatus.PUBLISHING or PostPlatform.objects.filter(
        post=post,
        is_deleted=False,
        status=PostStatus.PUBLISHING,
    ).exists():
        raise ValueError("A post that is currently publishing cannot be deleted.")

    if post.status == PostStatus.PUBLISHED:
        raise ValueError("Published posts cannot be deleted.")

    post.is_deleted = True

    post.save(
        update_fields=[
            "is_deleted",
            "updated_at",
        ],
    )

    PostPlatform.objects.filter(
        post=post,
        is_deleted=False,
    ).update(
        is_deleted=True,
        updated_at=timezone.now(),
    )

    PostMedia.objects.filter(
        post=post,
        is_deleted=False,
    ).update(
        is_deleted=True,
        updated_at=timezone.now(),
    )

    return post


# ============================================================
# MARK POST AS PUBLISHED
# ============================================================


@transaction.atomic
def mark_post_as_published(
    *,
    post,
):
    """
    Mark the post as successfully published.

    This should only be called after the publishing layer
    confirms successful provider publication.
    """

    post.status = PostStatus.PUBLISHED
    post.published_at = timezone.now()
    post.error_message = ""

    post.save(
        update_fields=[
            "status",
            "published_at",
            "error_message",
            "updated_at",
        ],
    )

    return post


# ============================================================
# MARK POST AS FAILED
# ============================================================


@transaction.atomic
def mark_post_as_failed(
    *,
    post,
    error_message="",
):
    """
    Mark the post as failed.
    """

    post.status = PostStatus.FAILED
    post.error_message = error_message or ""

    post.save(
        update_fields=[
            "status",
            "error_message",
            "updated_at",
        ],
    )

    return post
