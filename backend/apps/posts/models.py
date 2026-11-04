import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel

from .storage import PostMediaCloudinaryStorage

# ============================================================
# POST ENUMS
# ============================================================


class PostPublishType(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    NOW = "NOW", "Publish Now"
    SCHEDULE = "SCHEDULE", "Schedule"


class PostStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SCHEDULED = "SCHEDULED", "Scheduled"
    PUBLISHING = "PUBLISHING", "Publishing"
    UNRESOLVED = "UNRESOLVED", "Unresolved"
    PUBLISHED = "PUBLISHED", "Published"
    PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED", "Partially Published"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class SocialPlatform(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    LINKEDIN = "linkedin", "LinkedIn"
    THREADS = "threads", "Threads"
    X = "x", "X"
    YOUTUBE = "youtube", "YouTube"


class PostMediaType(models.TextChoices):
    IMAGE = "IMAGE", "Image"
    VIDEO = "VIDEO", "Video"


class MediaUploadStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPLOADING = "UPLOADING", "Uploading"
    PROCESSING = "PROCESSING", "Processing"
    READY = "READY", "Ready"
    FAILED = "FAILED", "Failed"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"


# ============================================================
# POST
# ============================================================


class Post(BaseModel):
    """
    Represents a social media post created for an organization.

    Post stores platform-agnostic content and publishing state.

    Exact social destinations are stored in PostPlatform.

    OAuth credentials/tokens are NOT stored in this app.
    Provider-specific credentials belong to the integrations layer.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="posts",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_posts",
    )

    request_idempotency_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
    )

    # ---------------------------------------------------------
    # Content
    # ---------------------------------------------------------

    caption = models.TextField(
        blank=True,
    )

    # ---------------------------------------------------------
    # Publishing
    # ---------------------------------------------------------

    publish_type = models.CharField(
        max_length=20,
        choices=PostPublishType.choices,
        default=PostPublishType.DRAFT,
        db_index=True,
    )

    status = models.CharField(
        max_length=30,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
        db_index=True,
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    timezone = models.CharField(
        max_length=100,
        blank=True,
        default="UTC",
    )

    # ---------------------------------------------------------
    # Publishing result
    # ---------------------------------------------------------

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # Failure handling
    # ---------------------------------------------------------

    error_message = models.TextField(
        blank=True,
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
        ],
    )

    class Meta:
        db_table = "posts"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "status",
                ],
                name="post_org_status_idx",
            ),
            models.Index(
                fields=[
                    "organization",
                    "publish_type",
                ],
                name="post_org_type_idx",
            ),
            models.Index(
                fields=[
                    "scheduled_at",
                ],
                name="post_scheduled_idx",
            ),
            models.Index(
                fields=[
                    "created_by",
                ],
                name="post_created_by_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["organization", "request_idempotency_key"],
                condition=Q(request_idempotency_key__isnull=False),
                name="unique_post_request_idempotency",
            ),
        ]

    def __str__(self):
        caption = self.caption.strip()

        if caption:
            preview = caption[:60]
        else:
            preview = "Untitled Post"

        return f"{self.organization.name} - {preview}"


# ============================================================
# POST PLATFORM / TARGET
# ============================================================


class PostPlatform(BaseModel):
    """
    Represents one exact social-account target for a post.

    A post can target multiple accounts on the same platform.

    Example:

        Post
          ├── Facebook Page A
          ├── Facebook Page B
          ├── Instagram A
          └── Instagram B

    The social account belongs to the organization's
    SocialAccount table.

    Provider credentials are NOT stored here.
    """

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="platforms",
    )

    platform = models.CharField(
        max_length=20,
        choices=SocialPlatform.choices,
    )

    social_account = models.ForeignKey(
        "social_accounts.SocialAccount",
        on_delete=models.PROTECT,
        related_name="post_platforms",
        null=True,
        blank=True,
    )

    content_type = models.CharField(
        max_length=50,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
        db_index=True,
    )

    # Calendar can schedule one exact connected-account target without
    # changing sibling destinations on the same Post.
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    scheduled_timezone = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    external_post_id = models.CharField(
        max_length=255,
        blank=True,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    # Provider execution state is deliberately stored on the exact
    # destination. Credentials remain in the integrations apps.
    idempotency_key = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    provider_container_id = models.CharField(
        max_length=255,
        blank=True,
    )

    provider_state = models.JSONField(
        default=dict,
        blank=True,
    )

    publish_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    attempt_count = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        db_table = "post_platforms"

        ordering = [
            "platform",
            "created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "post",
                    "social_account",
                ],
                condition=(
                    Q(
                        is_deleted=False,
                        social_account__isnull=False,
                    )
                ),
                name="unique_active_post_social_account",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "post",
                    "platform",
                ],
                name="post_platform_idx",
            ),
            models.Index(
                fields=[
                    "social_account",
                ],
                name="post_social_account_idx",
            ),
            models.Index(
                fields=[
                    "status",
                ],
                name="post_platform_status_idx",
            ),
        ]

    def __str__(self):
        return f"{self.post_id} - {self.platform}"


# ============================================================
# POST MEDIA
# ============================================================


class PostMedia(BaseModel):
    """
    Media attached to a post.

    One post can contain multiple images/videos depending on
    platform requirements.
    """

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="media",
    )

    media_type = models.CharField(
        max_length=10,
        choices=PostMediaType.choices,
    )

    file = models.FileField(
        upload_to="posts/%Y/%m/%d/",
        storage=PostMediaCloudinaryStorage(),
        # Direct Cloudinary media uses a prefixed public ID plus a version
        # marker (for example, __video__/post-media/<org>/<asset>::v<version>).
        # Keep enough room for the full immutable Cloudinary reference.
        max_length=1024,
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
    )

    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        db_table = "post_media"

        ordering = [
            "sort_order",
            "created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "post",
                    "sort_order",
                ],
                name="post_media_order_idx",
            ),
            models.Index(
                fields=[
                    "media_type",
                ],
                name="post_media_type_idx",
            ),
        ]

    def __str__(self):
        return self.original_filename or f"Media {self.id}"


# ============================================================
# MEDIA UPLOAD SESSION
# ============================================================


class MediaUploadSession(BaseModel):
    """Durable state for a direct, signed Cloudinary upload."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="media_upload_sessions",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_upload_sessions",
    )

    attached_post = models.ForeignKey(
        "posts.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_upload_sessions",
    )

    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    media_type = models.CharField(max_length=10, choices=PostMediaType.choices)
    expected_size = models.PositiveBigIntegerField()
    bytes_uploaded = models.PositiveBigIntegerField(default=0)

    cloudinary_public_id = models.CharField(max_length=512)
    cloudinary_asset_id = models.CharField(max_length=255, blank=True)
    cloudinary_version = models.PositiveBigIntegerField(null=True, blank=True)
    cloudinary_secure_url = models.URLField(max_length=2048, blank=True)
    cloudinary_resource_type = models.CharField(max_length=20, default="image")

    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=MediaUploadStatus.choices,
        default=MediaUploadStatus.CREATED,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    expires_at = models.DateTimeField(db_index=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "media_upload_sessions"
        indexes = [
            models.Index(
                fields=["organization", "status"],
                name="media_upload_org_status_idx",
            ),
            models.Index(
                fields=["expires_at", "status"],
                name="media_upload_expiry_idx",
            ),
        ]

    @property
    def storage_name(self):
        version_suffix = (
            f"::v{self.cloudinary_version}"
            if self.cloudinary_version is not None
            else ""
        )
        if self.media_type == PostMediaType.VIDEO:
            return f"__video__/{self.cloudinary_public_id}{version_suffix}"
        return f"__image__/{self.cloudinary_public_id}{version_suffix}"
