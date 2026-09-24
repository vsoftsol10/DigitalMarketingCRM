from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ResourceNotFoundException
from apps.common.pagination import StandardResultsSetPagination
from apps.common.responses import success_response

from .selectors import (
    get_organization_by_id,
    get_organization_options,
    get_organization_summary,
    get_organizations,
    get_subscription_history,
)
from .serializers import (
    OrganizationCreateSerializer,
    OrganizationReadSerializer,
    OrganizationOptionSerializer,
    OrganizationUpdateSerializer,
)

from .subscription_serializers import (
    SubscriptionChangePlanSerializer,
    SubscriptionHistorySerializer,
    SubscriptionRenewSerializer,
    SubscriptionStartSerializer,
)

from .services import (
    change_subscription_plan,
    create_organization,
    delete_organization,
    renew_subscription,
    update_organization,
    cancel_subscription,
    start_new_subscription,
)


class OrganizationListCreateAPIView(APIView):
    """
    List organizations and create a new organization.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        options_only = request.query_params.get("options") == "true"

        search = request.query_params.get("search")

        status_filter = request.query_params.get("status")

        subscription_status_filter = request.query_params.get("subscription_status")

        ordering = request.query_params.get(
            "ordering",
            "-created_at",
        )

        if options_only:
            queryset = get_organization_options(ordering=ordering)
            summary = None
            serializer_class = OrganizationOptionSerializer
        else:
            queryset = get_organizations(
                search=search,
                status=status_filter,
                subscription_status=subscription_status_filter,
                ordering=ordering,
            )
            summary = get_organization_summary()
            serializer_class = OrganizationReadSerializer

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = serializer_class(
            page,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data,
            summary=summary,
        )

    def post(self, request):
        serializer = OrganizationCreateSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        organization = create_organization(
            validated_data=serializer.validated_data,
            created_by=request.user,
        )

        response_serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message=("Organization created successfully."),
            status_code=status.HTTP_201_CREATED,
        )


class OrganizationDetailAPIView(APIView):
    """
    Retrieve, partially update, and soft-delete an
    organization.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, organization_id):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        return organization

    def get(
        self,
        request,
        organization_id,
    ):
        organization = self.get_object(organization_id)

        serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message=("Organization fetched successfully."),
        )

    def patch(
        self,
        request,
        organization_id,
    ):
        organization = self.get_object(organization_id)

        serializer = OrganizationUpdateSerializer(
            organization,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        organization = update_organization(
            organization=organization,
            validated_data=serializer.validated_data,
        )

        response_serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message=("Organization updated successfully."),
        )

    def delete(
        self,
        request,
        organization_id,
    ):
        organization = self.get_object(organization_id)

        delete_organization(organization=organization)

        return success_response(
            message=("Organization deleted successfully."),
            status_code=status.HTTP_200_OK,
        )


class OrganizationSubscriptionRenewAPIView(APIView):
    """
    Renew the current organization subscription.
    """

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        organization_id,
    ):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        serializer = SubscriptionRenewSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            subscription = renew_subscription(
                organization=organization,
                billing_cycle=serializer.validated_data.get("billing_cycle"),
                actor=request.user,
            )
            organization.refresh_from_db()
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Subscription renewed successfully.",
            status_code=status.HTTP_200_OK,
        )


class OrganizationSubscriptionChangePlanAPIView(APIView):
    """
    Change the organization's current subscription
    to another active plan and/or billing cycle.
    """

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        organization_id,
    ):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        serializer = SubscriptionChangePlanSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            subscription = change_subscription_plan(
                organization=organization,
                plan=serializer.validated_data["plan"],
                billing_cycle=serializer.validated_data["billing_cycle"],
            )
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Subscription plan changed successfully.",
            status_code=status.HTTP_200_OK,
        )


class OrganizationSubscriptionCancelAPIView(APIView):
    """
    Immediately cancel the organization's current subscription.
    """

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        organization_id,
    ):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        try:
            cancel_subscription(
                organization=organization,
                actor=request.user,
            )
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        organization.refresh_from_db()

        response_serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Subscription cancelled successfully.",
            status_code=status.HTTP_200_OK,
        )


class OrganizationSubscriptionStartAPIView(APIView):
    """
    Start a new subscription for an organization
    with no current subscription.
    """

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        organization_id,
    ):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        serializer = SubscriptionStartSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            start_new_subscription(
                organization=organization,
                plan=serializer.validated_data["plan"],
                billing_cycle=serializer.validated_data["billing_cycle"],
                actor=request.user,
            )
        except ValueError as exc:
            return success_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        organization.refresh_from_db()

        response_serializer = OrganizationReadSerializer(
            organization,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message="Subscription started successfully.",
            status_code=status.HTTP_200_OK,
        )

class OrganizationSubscriptionHistoryAPIView(
    APIView
):
    """
    Return the complete subscription history
    for an organization.
    """

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        organization_id,
    ):
        organization = get_organization_by_id(
            organization_id,
        )

        if not organization:
            raise ResourceNotFoundException(
                "Organization not found."
            )

        subscriptions = get_subscription_history(
            organization=organization,
        )

        serializer = SubscriptionHistorySerializer(
            subscriptions,
            many=True,
        )

        return success_response(
            data=serializer.data,
            message="Subscription history fetched successfully.",
        )
