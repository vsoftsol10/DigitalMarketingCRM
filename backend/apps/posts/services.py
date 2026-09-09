from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from django.utils import timezone

from apps.social_accounts.models import SocialAccount

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

    create_post_media(
        post=post,
        media_items=media_items,
    )

    return post


# ============================================================
# VALIDATE TARGET ACCOUNTS
# ============================================================


def validate_target_accounts(
    *,
    organization,
    targets,
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

    return post


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
