from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import (
    ResourceNotFoundException,
)
from apps.common.responses import success_response

from apps.organizations.selectors import (
    get_organization_by_id,
)

from .selectors import (
    get_social_account_by_id,
    get_social_accounts_for_organization,
)

from .serializers import (
    SocialAccountCreateSerializer,
    SocialAccountReadSerializer,
    SocialAccountUpdateSerializer,
)

from .services import (
    create_social_account,
    delete_social_account,
    disconnect_social_account,
    update_social_account,
)


class OrganizationSocialAccountListCreateAPIView(APIView):
    """
    List and create social accounts belonging
    to a specific organization.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get_organization(
        self,
        organization_id,
    ):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        return organization

    # ========================================================
    # LIST
    # ========================================================

    def get(
        self,
        request,
        organization_id,
    ):
        organization = self.get_organization(organization_id)

        queryset = get_social_accounts_for_organization(organization.organization_id)

        serializer = SocialAccountReadSerializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message=("Social accounts fetched successfully."),
        )

    # ========================================================
    # CREATE
    # ========================================================

    def post(
        self,
        request,
        organization_id,
    ):
        organization = self.get_organization(organization_id)

        serializer = SocialAccountCreateSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        social_account = create_social_account(
            organization=organization,
            validated_data=serializer.validated_data,
        )

        response_serializer = SocialAccountReadSerializer(
            social_account,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message=("Social account connected successfully."),
            status_code=status.HTTP_201_CREATED,
        )


class OrganizationSocialAccountDetailAPIView(APIView):
    """
    Retrieve, update, disconnect, and delete a
    social account belonging to a specific organization.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get_organization(
        self,
        organization_id,
    ):
        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        return organization

    def get_object(
        self,
        organization,
        social_account_id,
    ):
        social_account = get_social_account_by_id(
            social_account_id=social_account_id,
            organization_id=organization.organization_id,
        )

        if not social_account:
            raise ResourceNotFoundException("Social account not found.")

        return social_account

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        request,
        organization_id,
        social_account_id,
    ):
        organization = self.get_organization(organization_id)

        social_account = self.get_object(
            organization=organization,
            social_account_id=social_account_id,
        )

        serializer = SocialAccountReadSerializer(
            social_account,
            context={
                "request": request,
            },
        )

        return success_response(
            data=serializer.data,
            message=("Social account fetched successfully."),
        )

    # ========================================================
    # PATCH
    # ========================================================

    def patch(
        self,
        request,
        organization_id,
        social_account_id,
    ):
        organization = self.get_organization(organization_id)

        social_account = self.get_object(
            organization=organization,
            social_account_id=social_account_id,
        )

        serializer = SocialAccountUpdateSerializer(
            social_account,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        social_account = update_social_account(
            social_account=social_account,
            validated_data=serializer.validated_data,
        )

        response_serializer = SocialAccountReadSerializer(
            social_account,
            context={
                "request": request,
            },
        )

        return success_response(
            data=response_serializer.data,
            message=("Social account updated successfully."),
        )

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        request,
        organization_id,
        social_account_id,
    ):
        organization = self.get_organization(organization_id)

        social_account = self.get_object(
            organization=organization,
            social_account_id=social_account_id,
        )

        delete_social_account(social_account=social_account)

        return success_response(
            message=("Social account deleted successfully."),
            status_code=status.HTTP_200_OK,
        )
