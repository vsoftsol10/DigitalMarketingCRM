from datetime import timedelta
import logging
import uuid

from cloudinary import api as cloudinary_api
from cloudinary import utils as cloudinary_utils
from cloudinary.exceptions import Error as CloudinaryError

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from cloudinary.exceptions import BadRequest as CloudinaryBadRequest

from apps.common.exceptions import BadRequestException, ResourceNotFoundException
from apps.common.responses import success_response
from apps.organizations.models import Organization
from apps.organizations.selectors import get_organization_by_id

from .selectors import (
    get_calendar_event_by_target_id,
    get_calendar_events,
    get_post_by_id,
    get_posts_for_organization,
)
from .serializers import (
    MediaUploadSessionCreateSerializer,
    MediaUploadSessionFinalizeSerializer,
    MediaUploadSessionReadSerializer,
    PostCreateSerializer,
    PostMediaInputSerializer,
    PostMediaReadSerializer,
    CalendarEventSerializer,
    PostReadSerializer,
    PostScheduleActionSerializer,
    PostUpdateSerializer,
)
from apps.social_accounts.models import SocialAccount, SocialAccountStatus
from .models import (
    MediaUploadSession,
    MediaUploadStatus,
    Post,
    PostMediaType,
    PostPlatform,
)
from .services import (
    MediaUploadValidationError,
    create_post,
    delete_post,
    delete_post_target,
    publish_post_now,
    publish_post_target_now,
    retry_post_target,
    schedule_post,
    schedule_post_target,
    update_post,
    upload_post_media,
)

CLOUDINARY_RESOURCE_TIMEOUT_SECONDS = 120
logger = logging.getLogger(__name__)


def _safe_cloudinary_error_message(exc):
    """Return bounded Cloudinary diagnostics without logging credentials."""

    message = str(exc or "Cloudinary verification failed.")
    for sensitive_value in (
        settings.CLOUDINARY_STORAGE.get("API_KEY"),
        settings.CLOUDINARY_STORAGE.get("API_SECRET"),
    ):
        if sensitive_value:
            message = message.replace(str(sensitive_value), "[REDACTED]")
    return message[:500]


def _get_owned_organization(organization_id, user):
    organization = get_organization_by_id(organization_id)
    if not organization:
        raise ResourceNotFoundException("Organization not found.")
    # Organizations do not currently have a separate membership table or
    # role model. The persisted owner is therefore the complete authorization
    # boundary for upload sessions; a NULL owner must not mean public access.
    if organization.created_by_id != user.id:
        raise PermissionDenied("You do not have access to this organization.")
    return organization


def _media_upload_response(session):
    cloud_name = settings.CLOUDINARY_STORAGE["CLOUD_NAME"]
    timestamp = int(timezone.now().timestamp())
    folder = session.cloudinary_public_id.rsplit("/", 1)[0]
    public_id = session.cloudinary_public_id.rsplit("/", 1)[1]
    signed_params = {
        "folder": folder,
        "public_id": public_id,
        "overwrite": "false",
        "timestamp": timestamp,
    }
    signature = cloudinary_utils.api_sign_request(
        signed_params,
        settings.CLOUDINARY_STORAGE["API_SECRET"],
    )
    resource_type = session.cloudinary_resource_type
    return {
        "session_id": str(session.id),
        "media_asset_id": str(session.id),
        "media_type": session.media_type,
        "upload_url": (
            f"https://api.cloudinary.com/v1_1/{cloud_name}/"
            f"{resource_type}/upload"
        ),
        "cloud_name": cloud_name,
        "api_key": settings.CLOUDINARY_STORAGE["API_KEY"],
        "timestamp": timestamp,
        "signature": signature,
        "folder": folder,
        "public_id": public_id,
        "overwrite": "false",
        "resource_type": resource_type,
        "chunk_size": settings.MEDIA_UPLOAD_CHUNK_SIZE_BYTES,
        "chunk_threshold": settings.MEDIA_UPLOAD_CHUNK_THRESHOLD_BYTES,
        "expires_at": session.expires_at,
    }


class OrganizationMediaUploadSessionAPIView(APIView):
    """Create, inspect, and finalize a direct signed Cloudinary upload."""

    permission_classes = [IsAuthenticated]

    def get_session(self, organization_id, session_id, user, lock=False):
        organization = _get_owned_organization(organization_id, user)
        queryset = MediaUploadSession.objects
        if lock:
            queryset = queryset.select_for_update()
        session = queryset.filter(
            id=session_id,
            organization=organization,
            created_by=user,
            is_deleted=False,
        ).first()
        if not session:
            raise ResourceNotFoundException("Media upload session not found.")
        return organization, session

    def post(self, request, organization_id, session_id=None):
        organization = _get_owned_organization(organization_id, request.user)

        if session_id is None:
            serializer = MediaUploadSessionCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            now = timezone.now()
            session = MediaUploadSession.objects.create(
                organization=organization,
                created_by=request.user,
                original_filename=data["filename"],
                content_type=data["content_type"],
                media_type=data["media_type"],
                expected_size=data["size"],
                cloudinary_public_id=(
                    f"post-media/{organization.pk}/{uuid.uuid4().hex}"
                ),
                cloudinary_resource_type=(
                    "video"
                    if data["media_type"] == PostMediaType.VIDEO
                    else "image"
                ),
                expires_at=now + timedelta(
                    seconds=settings.MEDIA_UPLOAD_SESSION_TTL_SECONDS
                ),
            )
            return success_response(
                data=_media_upload_response(session),
                message="Media upload session created.",
                status_code=status.HTTP_201_CREATED,
            )

        serializer = MediaUploadSessionFinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            _organization, session = self.get_session(
                organization_id,
                session_id,
                request.user,
                lock=True,
            )
            if session.status == MediaUploadStatus.READY:
                return success_response(
                    data=MediaUploadSessionReadSerializer(session).data,
                    message="Media upload already finalized.",
                )
            if session.status in {
                MediaUploadStatus.EXPIRED,
                MediaUploadStatus.CANCELLED,
            }:
                raise BadRequestException("The media upload session is no longer active.")
            if session.expires_at <= timezone.now():
                session.status = MediaUploadStatus.EXPIRED
                session.error_message = "The media upload session has expired."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)

            data = serializer.validated_data
            expected_resource_type = session.cloudinary_resource_type
            expected_public_id = session.cloudinary_public_id
            submitted_public_id = data["public_id"]
            if (
                submitted_public_id != expected_public_id
                or data["resource_type"] != expected_resource_type
            ):
                raise BadRequestException("The uploaded media reference is invalid.")

            session.status = MediaUploadStatus.PROCESSING
            session.save(update_fields=["status", "updated_at"])

            try:
                resource = cloudinary_api.resource(
                    expected_public_id,
                    resource_type=expected_resource_type,
                    type="upload",
                    context=True,
                    media_metadata=True,
                    timeout=CLOUDINARY_RESOURCE_TIMEOUT_SECONDS,
                )
            except CloudinaryError as exc:
                logger.warning(
                    "Cloudinary media verification request failed "
                    "session_id=%s resource_type=%s error_type=%s error=%s",
                    session.id,
                    expected_resource_type,
                    type(exc).__name__,
                    _safe_cloudinary_error_message(exc),
                )
                session.status = MediaUploadStatus.FAILED
                session.error_message = "Cloudinary could not verify the uploaded asset."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message) from exc

            if (
                resource.get("public_id") != expected_public_id
                or resource.get("resource_type") != expected_resource_type
                or not str(resource.get("secure_url") or "").startswith("https://")
                or not resource.get("asset_id")
                or resource.get("version") is None
            ):
                session.status = MediaUploadStatus.FAILED
                session.error_message = "Cloudinary returned an invalid media asset."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)

            submitted_asset_id = data.get("asset_id")
            if submitted_asset_id and submitted_asset_id != resource.get("asset_id"):
                session.status = MediaUploadStatus.FAILED
                session.error_message = "Cloudinary returned an invalid media asset."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)

            actual_bytes = int(resource.get("bytes") or 0)
            max_bytes = (
                settings.MEDIA_UPLOAD_MAX_IMAGE_BYTES
                if session.media_type == PostMediaType.IMAGE
                else settings.MEDIA_UPLOAD_MAX_VIDEO_BYTES
            )
            if actual_bytes > max_bytes:
                session.status = MediaUploadStatus.FAILED
                session.error_message = "The uploaded asset exceeds the current media upload limit."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)
            if actual_bytes != session.expected_size:
                session.status = MediaUploadStatus.FAILED
                session.error_message = "The uploaded asset size does not match the selected file."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)

            metadata = {
                key: resource.get(key)
                for key in (
                    "format",
                    "resource_type",
                    "width",
                    "height",
                    "duration",
                    "frame_rate",
                    "bit_rate",
                    "video_codec",
                    "audio_codec",
                    "audio_frequency",
                    "bytes",
                )
                if resource.get(key) is not None
            }
            actual_format = str(metadata.get("format") or "").lower()
            allowed_formats = {"jpeg", "jpg", "png", "webp"}
            if session.media_type == PostMediaType.VIDEO:
                allowed_formats = {"mp4", "mov"}
            if actual_format not in allowed_formats:
                session.status = MediaUploadStatus.FAILED
                session.error_message = "The uploaded media format is not supported."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)
            if session.media_type == PostMediaType.VIDEO and not all(
                metadata.get(key) is not None
                for key in ("width", "height", "duration")
            ):
                missing_fields = [
                    key
                    for key in ("width", "height", "duration")
                    if metadata.get(key) is None
                ]
                logger.warning(
                    "Cloudinary media verification returned incomplete video metadata "
                    "session_id=%s resource_type=%s missing_fields=%s "
                    "resource_keys=%s returned_public_id_matches=%s "
                    "returned_resource_type=%s has_secure_url=%s has_asset_id=%s "
                    "version=%s",
                    session.id,
                    expected_resource_type,
                    missing_fields,
                    sorted(resource.keys()),
                    resource.get("public_id") == expected_public_id,
                    resource.get("resource_type"),
                    bool(resource.get("secure_url")),
                    bool(resource.get("asset_id")),
                    resource.get("version"),
                )
                session.status = MediaUploadStatus.FAILED
                session.error_message = "Cloudinary could not inspect the video metadata."
                session.save(update_fields=["status", "error_message", "updated_at"])
                raise BadRequestException(session.error_message)
            session.status = MediaUploadStatus.READY
            session.bytes_uploaded = actual_bytes
            session.cloudinary_asset_id = resource.get("asset_id", "")
            session.cloudinary_version = resource.get("version")
            session.cloudinary_secure_url = resource.get("secure_url", "")
            session.metadata = metadata
            session.finalized_at = timezone.now()
            session.error_message = ""
            session.save(
                update_fields=[
                    "status",
                    "bytes_uploaded",
                    "cloudinary_asset_id",
                    "cloudinary_version",
                    "cloudinary_secure_url",
                    "metadata",
                    "finalized_at",
                    "error_message",
                    "updated_at",
                ]
            )

        return success_response(
            data=MediaUploadSessionReadSerializer(session).data,
            message="Media uploaded and verified.",
        )

    def get(self, request, organization_id, session_id):
        with transaction.atomic():
            _organization, session = self.get_session(
                organization_id,
                session_id,
                request.user,
                lock=True,
            )
            if (
                session.attached_post_id is None
                and session.expires_at <= timezone.now()
                and session.status not in {
                    MediaUploadStatus.EXPIRED,
                    MediaUploadStatus.CANCELLED,
                }
            ):
                session.status = MediaUploadStatus.EXPIRED
                session.error_message = "The media upload session has expired."
                session.save(update_fields=["status", "error_message", "updated_at"])

            data = MediaUploadSessionReadSerializer(session).data
            # A long-running chunked upload can outlive Cloudinary's signature
            # window. Return a fresh signed payload only for an active,
            # unattached session that has not expired.
            if (
                session.attached_post_id is None
                and session.expires_at > timezone.now()
                and session.status not in {
                    MediaUploadStatus.READY,
                    MediaUploadStatus.EXPIRED,
                    MediaUploadStatus.CANCELLED,
                }
            ):
                data["upload"] = _media_upload_response(session)
        return success_response(
            data=data,
            message="Media upload session fetched.",
        )


class MediaUploadPolicyAPIView(APIView):
    """Expose only the authenticated media upload byte limits."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            data={
                "image_max_size_bytes": settings.MEDIA_UPLOAD_MAX_IMAGE_BYTES,
                "video_max_size_bytes": settings.MEDIA_UPLOAD_MAX_VIDEO_BYTES,
            },
            message="Media upload policy fetched.",
        )

# ============================================================
# ORGANIZATION POSTS - LIST / CREATE
# ============================================================


class CalendarEventsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        targets = get_calendar_events(
            user=request.user,
            month=request.query_params.get("month", ""),
            search=request.query_params.get("search", "").strip(),
            organization_id=request.query_params.get("organization", ""),
            social_account_id=request.query_params.get("social_account", ""),
            content_type=request.query_params.get("content_type", ""),
            status=request.query_params.get("status", ""),
        )
        return success_response(
            data=CalendarEventSerializer(targets, many=True).data,
            message="Calendar events fetched successfully.",
        )


class CalendarEventDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, target_id):
        target = get_calendar_event_by_target_id(
            user=request.user,
            target_id=target_id,
        )
        if not target:
            raise ResourceNotFoundException("Calendar event not found.")

        return success_response(
            data=CalendarEventSerializer(target).data,
            message="Calendar event fetched successfully.",
        )


class CalendarFiltersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_queryset = Organization.objects.filter(
            created_by=request.user,
            is_deleted=False,
        ).order_by("name")
        accounts = (
            SocialAccount.objects.filter(
                organization__created_by=request.user,
                organization__is_deleted=False,
                is_deleted=False,
                status=SocialAccountStatus.CONNECTED,
                is_valid=True,
            )
            .select_related("organization")
            .order_by("platform", "account_name", "username")
        )
        content_types = (
            PostPlatform.objects.filter(
                post__organization__created_by=request.user,
                post__is_deleted=False,
                is_deleted=False,
            )
            .exclude(content_type="")
            .values_list("content_type", flat=True)
            .distinct()
            .order_by("content_type")
        )
        return success_response(
            data={
                "organizations": [
                    {"value": organization.organization_id, "label": organization.name}
                    for organization in organization_queryset
                ],
                "social_accounts": [
                    {
                        "value": str(account.id),
                        "label": f"{account.platform.title()} — {account.account_name or account.username or account.platform_account_id}",
                    }
                    for account in accounts
                ],
                "contentTypes": [
                    {"value": content_type, "label": content_type.title()}
                    for content_type in content_types
                ],
                "statuses": [
                    {"value": value, "label": label}
                    for value, label in (
                        ("DRAFT", "Draft"),
                        ("SCHEDULED", "Scheduled"),
                        ("PUBLISHING", "Publishing"),
                        ("UNRESOLVED", "Unresolved"),
                        ("PUBLISHED", "Published"),
                        ("FAILED", "Failed"),
                    )
                ],
            },
            message="Calendar filters fetched successfully.",
        )


class OrganizationPostListCreateAPIView(APIView):
    """
    List and create posts belonging to an organization.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    def get_organization(self, organization_id, user):
        return _get_owned_organization(organization_id, user)

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        request,
        organization_id,
    ):
        organization = self.get_organization(organization_id, request.user)

        queryset = get_posts_for_organization(
            organization.id,
        )

        serializer = PostReadSerializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message="Posts fetched successfully.",
        )

    # ========================================================
    # POST
    # ========================================================

    def post(
        self,
        request,
        organization_id,
    ):
        organization = self.get_organization(organization_id, request.user)

        serializer = PostCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "organization": organization,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if len(idempotency_key) > 128:
            raise BadRequestException("Idempotency-Key must not exceed 128 characters.")

        try:
            post = create_post(
                organization=organization,
                created_by=request.user,
                validated_data=serializer.validated_data,
                idempotency_key=idempotency_key or None,
            )
        except IntegrityError:
            if not idempotency_key:
                raise
            post = Post.objects.filter(
                organization=organization,
                request_idempotency_key=idempotency_key,
                is_deleted=False,
            ).first()
            if not post:
                raise
        except MediaUploadValidationError as exc:
            raise BadRequestException(str(exc)) from exc
        except CloudinaryBadRequest as exc:
            raise BadRequestException(
                "Media upload failed. Please upload a valid supported media file."
            ) from exc

        response_serializer = PostReadSerializer(
            post,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message=(
                "Post created and queued for publishing."
                if post.publish_type == "NOW"
                else "Post created successfully."
            ),
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================
# POST DETAIL
# ============================================================


class OrganizationPostDetailAPIView(APIView):
    """
    Retrieve, update, and delete a post belonging to a
    specific organization.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    def get_organization(self, organization_id, user):
        return _get_owned_organization(organization_id, user)

    def get_object(
        self,
        organization,
        post_id,
    ):
        post = get_post_by_id(
            post_id=post_id,
            organization_id=organization.id,
        )

        if not post:
            raise ResourceNotFoundException(
                "Post not found.",
            )

        return post

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        request,
        organization_id,
        post_id,
    ):
        organization = self.get_organization(organization_id, request.user)

        post = self.get_object(
            organization=organization,
            post_id=post_id,
        )

        serializer = PostReadSerializer(
            post,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message="Post fetched successfully.",
        )

    # ========================================================
    # PATCH
    # ========================================================

    def patch(
        self,
        request,
        organization_id,
        post_id,
    ):
        organization = self.get_organization(organization_id, request.user)

        post = self.get_object(
            organization=organization,
            post_id=post_id,
        )

        serializer = PostUpdateSerializer(
            post,
            data=request.data,
            partial=True,
            context={
                "request": request,
                "organization": organization,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        post = update_post(
            post=post,
            validated_data=serializer.validated_data,
        )

        response_serializer = PostReadSerializer(
            post,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Post updated successfully.",
        )

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        request,
        organization_id,
        post_id,
    ):
        organization = self.get_organization(organization_id, request.user)

        post = self.get_object(
            organization=organization,
            post_id=post_id,
        )

        try:
            delete_post(post=post)
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(
            message="Post deleted successfully.",
            status_code=status.HTTP_200_OK,
        )


class OrganizationPostScheduleAPIView(OrganizationPostDetailAPIView):
    """Schedule a draft or reschedule an existing scheduled post."""

    def post(self, request, organization_id, post_id):
        organization = self.get_organization(organization_id, request.user)
        post = self.get_object(organization=organization, post_id=post_id)
        is_reschedule = post.status == "SCHEDULED"
        serializer = PostScheduleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            post = schedule_post(
                post_id=post.id,
                organization_id=organization.id,
                reschedule=is_reschedule,
                publish_date=serializer.validated_data["publish_date"],
                publish_time=serializer.validated_data["publish_time"],
                timezone_name=serializer.validated_data["timezone"],
                actor=request.user,
            )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(
            data=PostReadSerializer(post, context={"request": request}).data,
            message="Post rescheduled successfully." if is_reschedule else "Post scheduled successfully.",
        )


class OrganizationPostTargetScheduleAPIView(OrganizationPostDetailAPIView):
    """Schedule or reschedule exactly one Calendar-selected destination."""

    def post(self, request, organization_id, post_id, target_id):
        organization = self.get_organization(organization_id, request.user)
        post = self.get_object(organization=organization, post_id=post_id)
        serializer = PostScheduleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            target = schedule_post_target(
                post_id=post.id,
                organization_id=organization.id,
                target_id=target_id,
                publish_date=serializer.validated_data["publish_date"],
                publish_time=serializer.validated_data["publish_time"],
                timezone_name=serializer.validated_data["timezone"],
                actor=request.user,
            )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(
            data=PostReadSerializer(post, context={"request": request}).data,
            message=(
                "Post rescheduled successfully."
                if target.status == "SCHEDULED" and target.scheduled_at
                else "Post scheduled successfully."
            ),
        )


class OrganizationPostPublishNowAPIView(OrganizationPostDetailAPIView):
    """Publish one scheduled post immediately through the existing task."""

    def post(self, request, organization_id, post_id):
        organization = self.get_organization(organization_id, request.user)
        post = self.get_object(organization=organization, post_id=post_id)
        try:
            post = publish_post_now(post_id=post.id, organization_id=organization.id)
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(
            data=PostReadSerializer(post, context={"request": request}).data,
            message="Post queued for publishing.",
        )


class OrganizationPostTargetRetryAPIView(OrganizationPostDetailAPIView):
    """Retry exactly one failed publishing destination."""

    def post(self, request, organization_id, post_id, target_id):
        organization = self.get_organization(organization_id, request.user)
        post = self.get_object(organization=organization, post_id=post_id)
        try:
            post, _target = retry_post_target(
                post_id=post.id,
                organization_id=organization.id,
                target_id=target_id,
            )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(
            data=PostReadSerializer(post, context={"request": request}).data,
            message="Publishing retry queued.",
        )


class OrganizationPostTargetPublishNowAPIView(OrganizationPostDetailAPIView):
    """Immediately publish exactly one Calendar-selected destination."""

    def post(self, request, organization_id, post_id, target_id):
        organization = self.get_organization(organization_id, request.user)
        post = self.get_object(organization=organization, post_id=post_id)
        try:
            post, _target = publish_post_target_now(
                post_id=post.id,
                organization_id=organization.id,
                target_id=target_id,
            )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(
            data=PostReadSerializer(post, context={"request": request}).data,
            message="Publishing target queued.",
        )


class OrganizationPostTargetDetailAPIView(OrganizationPostDetailAPIView):
    """Delete exactly one Calendar-selected destination."""

    def delete(self, request, organization_id, post_id, target_id):
        organization = self.get_organization(organization_id, request.user)
        post = self.get_object(organization=organization, post_id=post_id)
        try:
            delete_post_target(
                post_id=post.id,
                organization_id=organization.id,
                target_id=target_id,
            )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        return success_response(message="Publishing target deleted successfully.")


# ============================================================
# POST MEDIA CREATE
# ============================================================


class OrganizationPostMediaCreateAPIView(APIView):
    """
    Upload a single media file to an existing post.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_organization(self, organization_id, user):
        return _get_owned_organization(organization_id, user)

    def get_object(
        self,
        organization,
        post_id,
    ):
        post = get_post_by_id(
            post_id=post_id,
            organization_id=organization.id,
        )

        if not post:
            raise ResourceNotFoundException(
                "Post not found.",
            )

        return post

    # ========================================================
    # POST
    # ========================================================

    def post(
        self,
        request,
        organization_id,
        post_id,
    ):
        organization = self.get_organization(organization_id, request.user)

        post = self.get_object(
            organization=organization,
            post_id=post_id,
        )

        serializer = PostMediaInputSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            media = upload_post_media(
                post=post,
                uploaded_file=serializer.validated_data["file"],
                media_type=serializer.validated_data["media_type"],
            )
        except CloudinaryBadRequest as exc:
            raise BadRequestException(
                "Media upload failed. Please upload a valid supported media file."
            ) from exc

        response_serializer = PostMediaReadSerializer(
            media,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Post media uploaded successfully.",
            status_code=status.HTTP_201_CREATED,
        )
