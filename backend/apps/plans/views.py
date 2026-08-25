from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ResourceNotFoundException
from apps.common.responses import success_response

from .selectors import (
    get_plan_by_id,
    get_plans,
)
from .serializers import (
    PlanCreateSerializer,
    PlanReadSerializer,
    PlanUpdateSerializer,
)
from .services import (
    create_plan,
    delete_plan,
    update_plan,
)


class PlanListCreateAPIView(APIView):
    """
    List subscription plans and create a new plan.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    # ========================================================
    # LIST
    # ========================================================

    def get(self, request):
        status_filter = request.query_params.get(
            "status"
        )

        plan_type = request.query_params.get(
            "type"
        )

        search = request.query_params.get(
            "search"
        )

        ordering = request.query_params.get(
            "ordering",
            "-created_at",
        )

        queryset = get_plans(
            status=status_filter,
            plan_type=plan_type,
            search=search,
            ordering=ordering,
        )

        serializer = PlanReadSerializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message="Plans fetched successfully.",
        )

    # ========================================================
    # CREATE
    # ========================================================

    def post(self, request):
        """
        Create a normal plan.

        Custom plans should be created through the
        dedicated custom-plan flow.
        """

        is_custom = (
            request.query_params.get(
                "type"
            )
            == "custom"
        )

        serializer = PlanCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "is_custom": is_custom,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        plan = create_plan(
            validated_data=serializer.validated_data,
            is_custom=is_custom,
        )

        response_serializer = (
            PlanReadSerializer(
                plan,
                context={
                    "request": request,
                },
            )
        )

        return success_response(
            data=response_serializer.data,
            message="Plan created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class PlanDetailAPIView(APIView):
    """
    Retrieve, update and soft-delete a plan.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(self, plan_id):
        plan = get_plan_by_id(
            plan_id
        )

        if not plan:
            raise ResourceNotFoundException(
                "Plan not found."
            )

        return plan

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        request,
        plan_id,
    ):
        plan = self.get_object(
            plan_id
        )

        serializer = PlanReadSerializer(
            plan,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message="Plan fetched successfully.",
        )

    # ========================================================
    # PATCH
    # ========================================================

    def patch(
        self,
        request,
        plan_id,
    ):
        plan = self.get_object(
            plan_id
        )

        serializer = PlanUpdateSerializer(
            plan,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_plan = update_plan(
            plan=plan,
            validated_data=serializer.validated_data,
        )

        response_serializer = (
            PlanReadSerializer(
                updated_plan,
                context={
                    "request": request,
                },
            )
        )

        return success_response(
            data=response_serializer.data,
            message="Plan updated successfully.",
        )

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        request,
        plan_id,
    ):
        plan = self.get_object(
            plan_id
        )

        delete_plan(
            plan=plan
        )

        return success_response(
            message="Plan deleted successfully.",
            status_code=status.HTTP_200_OK,
        )