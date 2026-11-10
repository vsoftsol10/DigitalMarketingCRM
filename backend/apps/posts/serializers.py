from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from uuid import UUID

from django.conf import settings
from django.utils import timezone

from rest_framework import serializers

from .selectors import get_calendar_event_local_datetime, get_calendar_event_status

from .models import (
    MediaUploadSession,
    Post,
    PostMedia,
    PostMediaType,
    PostPlatform,
    PostPublishType,
    PostStatus,
    SocialPlatform,
)

from PIL import Image
from rest_framework import serializers

from .models import PostMediaType


def validate_media_size(*, media_type, size):
    """Enforce the configured byte ceiling for a declared media type."""
    max_size = (
        settings.MEDIA_UPLOAD_MAX_IMAGE_BYTES
        if media_type == PostMediaType.IMAGE
        else settings.MEDIA_UPLOAD_MAX_VIDEO_BYTES
    )
    if size > max_size:
        raise serializers.ValidationError(
            {"file": "Media exceeds the configured upload limit."}
        )

# ============================================================
# POST TARGET INPUT
# ============================================================


class PostTargetInputSerializer(serializers.Serializer):
    """
    Input contract for one exact social-account target.

    Example:

        {
            "social_account": "uuid",
            "content_type": "FEED"
        }
    """

    social_account = serializers.UUIDField(
        required=True,
    )

    content_type = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50,
        default="",
    )

    def validate_content_type(
        self,
        value,
    ):
        return value.strip().upper()


# ============================================================
# POST MEDIA INPUT
# ============================================================


class PostMediaInputSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    media_type = serializers.ChoiceField(
        choices=PostMediaType.choices,
        required=True,
    )

    def validate(self, attrs):
        uploaded_file = attrs["file"]
        media_type = attrs["media_type"]

        if media_type == PostMediaType.IMAGE:
            self.validate_image(uploaded_file)

        if media_type == PostMediaType.VIDEO:
            self.validate_video(uploaded_file)

        return attrs

    def validate_image(self, uploaded_file):
        validate_media_size(
            media_type=PostMediaType.IMAGE,
            size=uploaded_file.size,
        )

        try:
            uploaded_file.seek(0)

            image = Image.open(uploaded_file)
            image.verify()

            uploaded_file.seek(0)

        except Exception:
            raise serializers.ValidationError(
                {"file": "Uploaded file is not a valid image."}
            )

        allowed_formats = {"JPEG", "PNG", "WEBP"}

        uploaded_file.seek(0)

        try:
            image = Image.open(uploaded_file)
            image_format = image.format
            uploaded_file.seek(0)
        except Exception:
            raise serializers.ValidationError(
                {"file": "Unable to detect image format."}
            )

        if image_format not in allowed_formats:
            raise serializers.ValidationError(
                {
                    "file": (
                        "Unsupported image format. "
                        "Allowed formats: JPG, JPEG, PNG, WEBP."
                    )
                }
            )

    def validate_video(self, uploaded_file):
        allowed_types = set(settings.MEDIA_UPLOAD_ALLOWED_VIDEO_TYPES)
        content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
        validate_media_size(
            media_type=PostMediaType.VIDEO,
            size=uploaded_file.size,
        )

        if content_type not in allowed_types:
            raise serializers.ValidationError(
                {"file": "Unsupported video format for this application."}
            )


class MediaUploadSessionCreateSerializer(serializers.Serializer):
    """Validate metadata before issuing a direct Cloudinary signature."""

    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    size = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        content_type = attrs["content_type"].lower().strip()
        size = attrs["size"]
        image_types = set(settings.MEDIA_UPLOAD_ALLOWED_IMAGE_TYPES)
        video_types = set(settings.MEDIA_UPLOAD_ALLOWED_VIDEO_TYPES)

        if content_type in image_types:
            media_type = PostMediaType.IMAGE
            max_size = settings.MEDIA_UPLOAD_MAX_IMAGE_BYTES
        elif content_type in video_types:
            media_type = PostMediaType.VIDEO
            max_size = settings.MEDIA_UPLOAD_MAX_VIDEO_BYTES
        else:
            raise serializers.ValidationError(
                {"content_type": "This media format is not supported."}
            )

        if size > max_size:
            raise serializers.ValidationError(
                {
                    "size": (
                        f"This file exceeds the configured {media_type.lower()} "
                        "upload limit."
                    )
                }
            )

        attrs["content_type"] = content_type
        attrs["media_type"] = media_type
        return attrs


class MediaUploadSessionFinalizeSerializer(serializers.Serializer):
    public_id = serializers.CharField(max_length=512)
    resource_type = serializers.CharField(max_length=20)
    asset_id = serializers.CharField(max_length=255, required=False, allow_blank=True)


class MediaUploadSessionReadSerializer(serializers.ModelSerializer):
    media_asset_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = MediaUploadSession
        fields = (
            "media_asset_id",
            "status",
            "original_filename",
            "content_type",
            "media_type",
            "expected_size",
            "bytes_uploaded",
            "metadata",
            "cloudinary_secure_url",
            "cloudinary_version",
            "expires_at",
            "error_message",
        )
        read_only_fields = fields


# ============================================================
# POST PLATFORM READ
# ============================================================


class PostPlatformReadSerializer(
    serializers.ModelSerializer,
):
    social_account_id = serializers.UUIDField(
        source="social_account.id",
        read_only=True,
        allow_null=True,
    )

    platform_account_id = serializers.CharField(
        source="social_account.platform_account_id",
        read_only=True,
        allow_null=True,
    )

    account_name = serializers.CharField(
        source="social_account.account_name",
        read_only=True,
        allow_blank=True,
        allow_null=True,
    )

    username = serializers.CharField(
        source="social_account.username",
        read_only=True,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = PostPlatform

        fields = (
            "id",
            "platform",
            "social_account_id",
            "platform_account_id",
            "account_name",
            "username",
            "content_type",
            "status",
            "external_post_id",
            "published_at",
            "error_message",
            "provider_container_id",
            "attempt_count",
        )

        read_only_fields = fields


# ============================================================
# POST MEDIA READ
# ============================================================


class PostMediaReadSerializer(
    serializers.ModelSerializer,
):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia

        fields = (
            "id",
            "media_type",
            "file_url",
            "original_filename",
            "mime_type",
            "file_size",
            "sort_order",
        )

        read_only_fields = fields

    def get_file_url(
        self,
        obj,
    ):
        if not obj.file:
            return None

        request = self.context.get(
            "request",
        )

        if request:
            return request.build_absolute_uri(
                obj.file.url,
            )

        return obj.file.url


class CalendarEventSerializer(serializers.Serializer):
    """Serialize a PostPlatform as the existing Calendar event shape."""

    def to_representation(self, target):
        post = target.post
        event_datetime = get_calendar_event_local_datetime(target)
        timezone_name = target.scheduled_timezone or post.timezone or "UTC"
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            timezone_name = "UTC"

        caption = post.caption or ""
        title = caption.strip().splitlines()[0][:80] if caption.strip() else "Untitled Post"
        account = target.social_account

        return {
            "id": str(target.id),
            "post_id": str(post.id),
            "organization": {
                "id": post.organization.organization_id,
                "name": post.organization.name,
            },
            "social_account": {
                "id": str(account.id) if account else None,
                "name": (account.account_name or account.username or account.platform_account_id) if account else "",
                "platform": target.platform.upper(),
            },
            "title": title,
            "date": event_datetime.date().isoformat() if event_datetime else None,
            "time": event_datetime.strftime("%I:%M %p") if event_datetime else None,
            "platform": target.platform.upper(),
            "content_type": target.content_type,
            "status": get_calendar_event_status(target),
            "caption": caption,
            "timezone": timezone_name,
            "error_message": target.error_message or post.error_message,
            "created_at": post.created_at.isoformat(),
            "updated_at": target.updated_at.isoformat(),
            "media": [
                {
                    "id": str(media.id),
                    "type": media.media_type,
                    "url": media.file.url,
                    "mime_type": media.mime_type,
                }
                for media in post.media.all()
                if media.file
            ],
        }


# ============================================================
# POST READ
# ============================================================


class PostReadSerializer(
    serializers.ModelSerializer,
):
    platforms = PostPlatformReadSerializer(
        many=True,
        read_only=True,
    )

    media = PostMediaReadSerializer(
        many=True,
        read_only=True,
    )

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta:
        model = Post

        fields = (
            "id",
            "organization",
            "organization_name",
            "created_by",
            "caption",
            "publish_type",
            "status",
            "scheduled_at",
            "timezone",
            "published_at",
            "error_message",
            "retry_count",
            "platforms",
            "media",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


# ============================================================
# COMMON VALIDATION HELPERS
# ============================================================


def validate_timezone_name(
    value,
):
    """
    Validate IANA timezone name.
    """

    value = (value or "").strip() or "UTC"

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise serializers.ValidationError(
            f"Invalid timezone: {value}.",
        ) from exc

    return value


# ============================================================
# CREATE POST
# ============================================================


class PostCreateSerializer(
    serializers.Serializer,
):
    """
    Create-post input contract.

    Organization is resolved from the URL and therefore is NOT
    accepted from the request body.

    Exact social accounts are provided through targets.
    """

    targets = PostTargetInputSerializer(
        many=True,
        required=True,
        allow_empty=False,
    )

    caption = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2200,
    )

    publish_type = serializers.ChoiceField(
        choices=PostPublishType.choices,
        required=True,
    )

    publish_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    publish_time = serializers.TimeField(
        required=False,
        allow_null=True,
    )

    timezone = serializers.CharField(
        required=False,
        allow_blank=True,
        default="UTC",
    )

    media = PostMediaInputSerializer(
        many=True,
        required=False,
        default=list,
    )

    media_asset_ids = serializers.JSONField(
        required=False,
        write_only=True,
    )

    def validate_timezone(
        self,
        value,
    ):
        return validate_timezone_name(
            value,
        )

    def validate_targets(
        self,
        value,
    ):
        """
        Reject duplicate social-account targets.
        """

        social_account_ids = [str(item["social_account"]) for item in value]

        if len(social_account_ids) != len(set(social_account_ids)):
            raise serializers.ValidationError(
                "The same social account cannot be targeted more than once."
            )

        return value

    def validate(
        self,
        attrs,
    ):
        media_asset_ids = attrs.get("media_asset_ids")
        if media_asset_ids is not None:
            if not isinstance(media_asset_ids, list) or not media_asset_ids:
                raise serializers.ValidationError(
                    {"media_asset_ids": "Media asset IDs must be a non-empty list."}
                )

            normalized_asset_ids = []
            for asset_id in media_asset_ids:
                try:
                    normalized_asset_ids.append(str(UUID(str(asset_id))))
                except (TypeError, ValueError, AttributeError) as exc:
                    raise serializers.ValidationError(
                        {"media_asset_ids": "Media asset IDs are invalid."}
                    ) from exc
            attrs["media_asset_ids"] = normalized_asset_ids

            if attrs.get("media"):
                raise serializers.ValidationError(
                    {
                        "media_asset_ids": (
                            "Use media asset IDs or multipart media, not both."
                        )
                    }
                )

        publish_type = attrs.get(
            "publish_type",
        )

        publish_date = attrs.get(
            "publish_date",
        )

        publish_time = attrs.get(
            "publish_time",
        )

        timezone_name = attrs.get(
            "timezone",
            "UTC",
        )

        if publish_type == PostPublishType.SCHEDULE:
            if not publish_date:
                raise serializers.ValidationError(
                    {"publish_date": ("Publish date is required for scheduled posts.")}
                )

            if not publish_time:
                raise serializers.ValidationError(
                    {"publish_time": ("Publish time is required for scheduled posts.")}
                )

            if not timezone_name:
                raise serializers.ValidationError(
                    {
                        "timezone": "Timezone is required for scheduled posts.",
                    }
                )

            scheduled_at = timezone.datetime.combine(
                publish_date,
                publish_time,
            ).replace(tzinfo=ZoneInfo(timezone_name))

            if scheduled_at <= timezone.now():
                raise serializers.ValidationError(
                    {"publish_time": "Scheduled publishing must be in the future."}
                )

        return attrs


# ============================================================
# UPDATE POST
# ============================================================


class PostUpdateSerializer(
    serializers.Serializer,
):
    """
    Update contract for an existing post.

    Organization and credentials are never accepted from
    the client.
    """

    targets = PostTargetInputSerializer(
        many=True,
        required=False,
        allow_empty=False,
    )

    caption = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2200,
    )

    publish_type = serializers.ChoiceField(
        choices=PostPublishType.choices,
        required=False,
    )

    publish_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    publish_time = serializers.TimeField(
        required=False,
        allow_null=True,
    )

    timezone = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    media = PostMediaInputSerializer(
        many=True,
        required=False,
    )

    def validate_timezone(
        self,
        value,
    ):
        return validate_timezone_name(
            value,
        )

    def validate_targets(
        self,
        value,
    ):
        social_account_ids = [str(item["social_account"]) for item in value]

        if len(social_account_ids) != len(set(social_account_ids)):
            raise serializers.ValidationError(
                "The same social account cannot be targeted more than once."
            )

        return value

    def validate(
        self,
        attrs,
    ):
        publish_type = attrs.get(
            "publish_type",
        )

        if publish_type == PostPublishType.SCHEDULE:
            publish_date = attrs.get(
                "publish_date",
            )

            publish_time = attrs.get(
                "publish_time",
            )

            timezone_name = attrs.get(
                "timezone",
            )

            if not publish_date:
                raise serializers.ValidationError(
                    {"publish_date": ("Publish date is required for scheduled posts.")}
                )

            if not publish_time:
                raise serializers.ValidationError(
                    {"publish_time": ("Publish time is required for scheduled posts.")}
                )

            if not timezone_name:
                raise serializers.ValidationError(
                    {"timezone": ("Timezone is required for scheduled posts.")}
                )

        return attrs


class PostScheduleActionSerializer(serializers.Serializer):
    """Input shared by the Calendar schedule and reschedule actions."""

    publish_date = serializers.DateField(required=True)
    publish_time = serializers.TimeField(required=True)
    timezone = serializers.CharField(required=True, allow_blank=False)

    def validate_timezone(self, value):
        return validate_timezone_name(value)

    def validate(self, attrs):
        scheduled_at = timezone.datetime.combine(
            attrs["publish_date"],
            attrs["publish_time"],
        ).replace(tzinfo=ZoneInfo(attrs["timezone"]))
        if scheduled_at <= timezone.now():
            raise serializers.ValidationError(
                {"publish_time": "Scheduled publishing must be in the future."}
            )
        return attrs
