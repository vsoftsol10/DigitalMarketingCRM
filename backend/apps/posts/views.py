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
    PostCreateSerializer,
    PostMediaInputSerializer,
    PostMediaReadSerializer,
    CalendarEventSerializer,
    PostReadSerializer,
    PostScheduleActionSerializer,
    PostUpdateSerializer,
)
from apps.social_accounts.models import SocialAccount, SocialAccountStatus
from .models import PostPlatform
from .services import (
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
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found.",
            )

        if organization.created_by_id and organization.created_by_id != user.id:
            raise PermissionDenied("You do not have access to this organization.")
        return organization

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

        try:
            post = create_post(
                organization=organization,
                created_by=request.user,
                validated_data=serializer.validated_data,
            )
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
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found.",
            )

        if organization.created_by_id and organization.created_by_id != user.id:
            raise PermissionDenied("You do not have access to this organization.")
        return organization

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
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found.",
            )

        if organization.created_by_id and organization.created_by_id != user.id:
            raise PermissionDenied("You do not have access to this organization.")
        return organization

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
