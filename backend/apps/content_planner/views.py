from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ResourceNotFoundException
from apps.common.responses import success_response

from .selectors import (
    get_content_idea_by_id,
    get_content_ideas,
    get_content_planner_organizations,
    get_content_planner_statistics,
)
from .serializers import (
    ContentIdeaCreateSerializer,
    ContentIdeaReadSerializer,
    ContentIdeaUpdateSerializer,
)
from .services import (
    create_content_idea,
    delete_content_idea,
    update_content_idea,
)


class ContentPlannerListCreateAPIView(APIView):
    """
    List content ideas and create a new content idea.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get(
            "search",
        )

        organization_id = request.query_params.get(
            "organization",
        )

        ideas = get_content_ideas(
            search=search,
            organization_id=organization_id,
        )

        organizations = get_content_planner_organizations()

        statistics = get_content_planner_statistics()

        idea_serializer = ContentIdeaReadSerializer(
            ideas,
            many=True,
            context={
                "request": request,
            },
        )

        organization_data = [
            {
                "id": str(organization["id"]),
                "name": organization["name"],
            }
            for organization in organizations
        ]

        return success_response(
            data={
                "filters": {
                    "organization": (
                        organization_id
                        if organization_id
                        else "all"
                    ),
                },
                "statistics": statistics,
                "organizations": organization_data,
                "ideas": idea_serializer.data,
            },
            message="Content Planner fetched successfully.",
        )

    def post(self, request):
        serializer = ContentIdeaCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            content_idea = create_content_idea(
                validated_data=serializer.validated_data,
            )
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = ContentIdeaReadSerializer(
            content_idea,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Content idea created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class ContentPlannerDetailAPIView(APIView):
    """
    Retrieve, update, and soft-delete a content idea.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, idea_id):
        content_idea = get_content_idea_by_id(
            idea_id=idea_id,
        )

        if not content_idea:
            raise ResourceNotFoundException(
                "Content idea not found.",
            )

        return content_idea

    def get(
        self,
        request,
        idea_id,
    ):
        content_idea = self.get_object(
            idea_id,
        )

        serializer = ContentIdeaReadSerializer(
            content_idea,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message="Content idea fetched successfully.",
        )

    def patch(
        self,
        request,
        idea_id,
    ):
        content_idea = self.get_object(
            idea_id,
        )

        serializer = ContentIdeaUpdateSerializer(
            content_idea,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            content_idea = update_content_idea(
                content_idea=content_idea,
                validated_data=serializer.validated_data,
            )
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = ContentIdeaReadSerializer(
            content_idea,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Content idea updated successfully.",
        )

    def delete(
        self,
        request,
        idea_id,
    ):
        content_idea = self.get_object(
            idea_id,
        )

        try:
            delete_content_idea(
                content_idea=content_idea,
            )
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(
            message="Content idea deleted successfully.",
            status_code=status.HTTP_200_OK,
        )