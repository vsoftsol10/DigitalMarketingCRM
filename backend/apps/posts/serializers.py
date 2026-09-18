from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from rest_framework import serializers

from .models import (
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
        max_size = 10 * 1024 * 1024  # 10 MB

        if uploaded_file.size > max_size:
            raise serializers.ValidationError(
                {"file": "Image size must not exceed 10 MB."}
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
        max_size = 50 * 1024 * 1024
        allowed_types = {"video/mp4"}
        content_type = (getattr(uploaded_file, "content_type", "") or "").lower()

        if uploaded_file.size > max_size:
            raise serializers.ValidationError(
                {"file": "Video size must not exceed 50 MB."}
            )

        if content_type not in allowed_types:
            raise serializers.ValidationError(
                {"file": "Unsupported video format. Only MP4 is allowed."}
            )


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
