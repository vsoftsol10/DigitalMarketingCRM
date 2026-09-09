from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ResourceNotFoundException
from apps.common.responses import success_response
from apps.organizations.selectors import get_organization_by_id

from .selectors import (
    get_post_by_id,
    get_posts_for_organization,
)
from .serializers import (
    PostCreateSerializer,
    PostMediaInputSerializer,
    PostMediaReadSerializer,
    PostReadSerializer,
    PostUpdateSerializer,
)
from .services import (
    create_post,
    delete_post,
    update_post,
    upload_post_media,
)

# ============================================================
# ORGANIZATION POSTS - LIST / CREATE
# ============================================================


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

    def get_organization(
        self,
        organization_id,
    ):
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found.",
            )

        return organization

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        request,
        organization_id,
    ):
        organization = self.get_organization(
            organization_id,
        )

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
        organization = self.get_organization(
            organization_id,
        )

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

        post = create_post(
            organization=organization,
            created_by=request.user,
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
            message="Post created successfully.",
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

    def get_organization(
        self,
        organization_id,
    ):
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found.",
            )

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
        organization = self.get_organization(
            organization_id,
        )

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
        organization = self.get_organization(
            organization_id,
        )

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
        organization = self.get_organization(
            organization_id,
        )

        post = self.get_object(
            organization=organization,
            post_id=post_id,
        )

        delete_post(
            post=post,
        )

        return success_response(
            message="Post deleted successfully.",
            status_code=status.HTTP_200_OK,
        )


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

    def get_organization(
        self,
        organization_id,
    ):
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found.",
            )

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
        organization = self.get_organization(
            organization_id,
        )

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

        media = upload_post_media(
            post=post,
            uploaded_file=serializer.validated_data["file"],
            media_type=serializer.validated_data["media_type"],
        )

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
