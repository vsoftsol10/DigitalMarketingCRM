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
    MediaUploadSession,
    MediaUploadStatus,
    Post,
    PostMedia,
    PostPlatform,
    PostPublishType,
    PostStatus,
)

from PIL import Image

from django.db import transaction

from .models import PostMedia, PostMediaType


class MediaUploadValidationError(ValueError):
    """Expected validation failure for a media upload reference."""


INSTAGRAM_IMAGE_MIN_ASPECT_RATIO = 0.75
INSTAGRAM_IMAGE_MAX_ASPECT_RATIO = 1.91
# Allow the small rounding difference between a 3:4 source and integer pixel
# dimensions such as 1085x1447 (0.7498 when represented as a decimal ratio).
INSTAGRAM_IMAGE_MIN_RATIO_TOLERANCE = 0.0002
INSTAGRAM_IMAGE_FORMATS = {"jpg", "jpeg", "png"}


def _validate_instagram_image_metadata(*, metadata, filename, media_index):
    """Validate one image against Instagram's image container contract."""

    metadata = metadata or {}
    try:
        width = int(metadata.get("width") or 0)
        height = int(metadata.get("height") or 0)
    except (TypeError, ValueError):
        width = 0
        height = 0
    image_format = str(metadata.get("format") or "").lower()
    label = f'Instagram image {media_index + 1} ({filename or "unnamed"})'

    if not width or not height:
        raise MediaUploadValidationError(
            f"{label} dimensions could not be verified for Instagram."
        )

    aspect_ratio = width / height
    if not (
        aspect_ratio + INSTAGRAM_IMAGE_MIN_RATIO_TOLERANCE
        >= INSTAGRAM_IMAGE_MIN_ASPECT_RATIO
        and aspect_ratio
        <= INSTAGRAM_IMAGE_MAX_ASPECT_RATIO
    ):
        raise MediaUploadValidationError(
            f"{label} is {width}x{height} with aspect ratio "
            f"{aspect_ratio:.2f}; Instagram requires an aspect ratio "
            "between 0.75 (3:4) and 1.91:1."
        )

    if not image_format:
        raise MediaUploadValidationError(
            f"{label} format could not be verified for Instagram."
        )

    if image_format not in INSTAGRAM_IMAGE_FORMATS:
        raise MediaUploadValidationError(
            f"{label} uses {image_format.upper()} format; Instagram image "
            "publishing supports JPEG or PNG media."
        )


def validate_multipart_media_for_targets(*, media_items, targets, organization):
    """Validate legacy multipart images only for Instagram destinations."""

    account_ids = [item["social_account"] for item in targets]
    accounts = SocialAccount.objects.filter(
        id__in=account_ids,
        organization=organization,
        platform=SocialPlatform.INSTAGRAM,
        is_deleted=False,
    )
    instagram_account_ids = {str(account.id) for account in accounts}
    if not instagram_account_ids:
        return

    instagram_post_selected = any(
        str(target.get("content_type") or "POST").upper() in {"POST", "CAROUSEL"}
        and str(target["social_account"]) in instagram_account_ids
        for target in targets
    )
    if not instagram_post_selected:
        return

    for media_index, media in enumerate(media_items):
        if media.get("media_type") != PostMediaType.IMAGE:
            continue
        uploaded_file = media.get("file")
        try:
            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            metadata = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
            }
        except Exception as exc:
            raise MediaUploadValidationError(
                f"Instagram image {media_index + 1} "
                f'({getattr(uploaded_file, "name", "unnamed")}) '
                "dimensions could not be verified."
            ) from exc
        finally:
            try:
                uploaded_file.seek(0)
            except (AttributeError, OSError, ValueError):
                pass

        _validate_instagram_image_metadata(
            metadata=metadata,
            filename=getattr(uploaded_file, "name", ""),
            media_index=media_index,
        )


# ============================================================
# CREATE POST
# ============================================================


@transaction.atomic
def create_post(
    *,
    organization,
    created_by,
    validated_data,
    idempotency_key=None,
):
    """
    Create a post together with its exact social-account targets
    and media.

    This service handles database persistence only.

    Actual provider publishing is handled by the publishing
    / integration layer.
    """

    if idempotency_key:
        existing_post = Post.objects.filter(
            organization=organization,
            request_idempotency_key=idempotency_key,
            is_deleted=False,
        ).first()
        if existing_post:
            return existing_post

    targets = validated_data.pop(
        "targets",
        [],
    )

    media_items = validated_data.pop(
        "media",
        [],
    )

    media_asset_ids = validated_data.pop(
        "media_asset_ids",
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

    account_map = validate_target_accounts(
        organization=organization,
        targets=targets,
        require_publishable=publish_type != PostPublishType.DRAFT,
    )

    media_count = len(media_asset_ids or media_items)
    for target in targets:
        account = account_map[str(target["social_account"])]
        if (
            account.platform == SocialPlatform.INSTAGRAM
            and str(target.get("content_type") or "POST").upper() == "STORY"
            and media_count != 1
        ):
            raise MediaUploadValidationError(
                "Instagram Stories require exactly one media item."
            )

    if media_asset_ids:
        validate_media_assets_for_targets(
            organization=organization,
            created_by=created_by,
            media_asset_ids=media_asset_ids,
            targets=targets,
        )
    elif media_items:
        validate_multipart_media_for_targets(
            organization=organization,
            media_items=media_items,
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
        request_idempotency_key=idempotency_key,
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

    if media_asset_ids:
        create_post_media_from_uploads(
            post=post,
            organization=organization,
            created_by=created_by,
            media_asset_ids=media_asset_ids,
        )
    else:
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
            {
                "post": post,
                "media_type": media_type,
                "file": uploaded_file,
                "original_filename": getattr(
                    uploaded_file,
                    "name",
                    "",
                ),
                "mime_type": getattr(
                    uploaded_file,
                    "content_type",
                    "",
                ),
                "file_size": getattr(
                    uploaded_file,
                    "size",
                    None,
                ),
                "sort_order": index,
            }
        )

    for media_item in post_media_items:
        PostMedia.objects.create(**media_item)

    return list(PostMedia.objects.filter(post=post, is_deleted=False).order_by("sort_order"))


def create_post_media_from_uploads(
    *,
    post,
    organization,
    created_by,
    media_asset_ids,
):
    """Attach verified, organization-owned Cloudinary assets to a post."""

    sessions = list(
        MediaUploadSession.objects.select_for_update().filter(
            id__in=media_asset_ids,
            organization=organization,
            created_by=created_by,
            status=MediaUploadStatus.READY,
            attached_post__isnull=True,
            expires_at__gt=timezone.now(),
            is_deleted=False,
        )
    )
    requested_ids = [str(item) for item in media_asset_ids]
    if len(requested_ids) != len(set(requested_ids)):
        raise MediaUploadValidationError(
            "The same media upload cannot be attached more than once."
        )
    session_map = {str(session.id): session for session in sessions}
    if len(session_map) != len(requested_ids):
        raise MediaUploadValidationError(
            "One or more media uploads are unavailable or not ready."
        )
    if any(session.expires_at <= timezone.now() for session in sessions):
        raise MediaUploadValidationError("One or more media uploads have expired.")

    post_media_items = []
    for index, asset_id in enumerate(requested_ids):
        session = session_map[str(asset_id)]
        post_media_items.append(
            PostMedia(
                post=post,
                media_type=session.media_type,
                file=session.storage_name,
                original_filename=session.original_filename,
                mime_type=session.content_type,
                file_size=session.expected_size,
                sort_order=index,
            )
        )

    PostMedia.objects.bulk_create(post_media_items)
    MediaUploadSession.objects.filter(id__in=requested_ids).update(
        attached_post=post,
        updated_at=timezone.now(),
    )
    return post_media_items


def validate_media_assets_for_targets(
    *,
    organization,
    created_by,
    media_asset_ids,
    targets,
):
    """Apply destination-specific preflight checks before post persistence."""

    sessions = MediaUploadSession.objects.filter(
        id__in=media_asset_ids,
        organization=organization,
        created_by=created_by,
        status=MediaUploadStatus.READY,
        attached_post__isnull=True,
        expires_at__gt=timezone.now(),
        is_deleted=False,
    )
    session_map = {str(session.id): session for session in sessions}
    for asset_id in media_asset_ids:
        session = session_map.get(str(asset_id))
        if not session:
            raise MediaUploadValidationError(
                "One or more media uploads are unavailable or not ready."
            )

    account_ids = [item["social_account"] for item in targets]
    accounts = SocialAccount.objects.filter(
        id__in=account_ids,
        organization=organization,
        is_deleted=False,
    )
    platform_by_account = {account.id: account.platform for account in accounts}

    for target in targets:
        platform = platform_by_account.get(target["social_account"])
        content_type = str(target.get("content_type") or "POST").upper()
        for media_index, asset_id in enumerate(media_asset_ids):
            session = session_map[str(asset_id)]
            if (
                platform == SocialPlatform.INSTAGRAM
                and content_type in {"POST", "CAROUSEL"}
                and session.media_type == PostMediaType.IMAGE
            ):
                _validate_instagram_image_metadata(
                    metadata=session.metadata,
                    filename=session.original_filename,
                    media_index=media_index,
                )
            if session.media_type != PostMediaType.VIDEO:
                continue
            metadata = session.metadata or {}
            duration = float(metadata.get("duration") or 0)
            width = int(metadata.get("width") or 0)
            height = int(metadata.get("height") or 0)
            frame_rate = float(metadata.get("frame_rate") or 0)
            if not duration or not width or not height:
                raise ValueError("Video metadata could not be verified.")

            if platform == SocialPlatform.INSTAGRAM and content_type == "REEL":
                if not 3 <= duration <= 900:
                    raise ValueError("Instagram Reels must be between 3 seconds and 15 minutes.")
                if width > 1920 or not 23 <= frame_rate <= 60:
                    raise ValueError("This video does not meet Instagram Reel dimensions or frame-rate requirements.")
            elif platform == SocialPlatform.FACEBOOK and content_type == "REEL":
                if not 4 <= duration <= 60:
                    raise ValueError("Facebook Reels must be between 4 and 60 seconds.")
                if width < 540 or height < 960 or not 23 <= frame_rate <= 60:
                    raise ValueError("This video does not meet Facebook Reel dimensions or frame-rate requirements.")
            elif content_type == "STORY" and duration > 60:
                raise ValueError("Story videos must not exceed 60 seconds.")


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
