from urllib.parse import urlencode

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import ResourceNotFoundException
from apps.organizations.selectors import get_organization_by_id

from .constants import META_OAUTH_AUTHORIZE_URL
from .oauth import create_oauth_state

from django.core import signing

from rest_framework.permissions import AllowAny
from rest_framework import status

from apps.accounts.models import User

from .client import MetaAPIClient
from .constants import META_OAUTH_STATE_MAX_AGE_SECONDS
from .exceptions import (
    MetaIntegrationError,
    MetaOAuthStateError,
)
from .oauth import validate_oauth_state


class MetaOAuthStartAPIView(APIView):
    """
    Start Meta OAuth flow for a selected organization.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_id = request.query_params.get("organization_id")

        if not organization_id:
            return Response(
                {"message": "Organization ID is required."},
                status=400,
            )

        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        # ----------------------------------------------------
        # Create secure OAuth state
        # ----------------------------------------------------

        state = create_oauth_state(
            organization_id=organization.organization_id,
            user_id=request.user.id,
        )

        # ----------------------------------------------------
        # OAuth parameters
        # ----------------------------------------------------

        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": settings.META_OAUTH_REDIRECT_URI,
            "state": state,
            "response_type": "code",
        }

        authorization_url = f"{META_OAUTH_AUTHORIZE_URL}" f"?{urlencode(params)}"

        return Response(
            {
                "authorization_url": authorization_url,
            }
        )


class MetaOAuthCallbackAPIView(APIView):
    """
    Handle the callback returned by Meta OAuth.

    This endpoint is intentionally public because Meta redirects
    the user's browser here. The signed state is used to restore
    and validate the authenticated OAuth context.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        # ====================================================
        # META ERROR
        # ====================================================

        error = request.query_params.get("error")

        if error:
            error_description = request.query_params.get(
                "error_description",
                "Meta authorization was cancelled or denied.",
            )

            return Response(
                {
                    "message": error_description,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # AUTHORIZATION CODE
        # ====================================================

        code = request.query_params.get("code")

        if not code:
            return Response(
                {
                    "message": ("Authorization code was not provided."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # STATE
        # ====================================================

        state = request.query_params.get("state")

        if not state:
            return Response(
                {
                    "message": "OAuth state is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            state_data = validate_oauth_state(
                state,
                max_age=META_OAUTH_STATE_MAX_AGE_SECONDS,
            )

        except (
            signing.BadSignature,
            signing.SignatureExpired,
        ) as exc:
            raise MetaOAuthStateError("Invalid or expired OAuth state.") from exc

        # ====================================================
        # STATE DATA
        # ====================================================

        organization_id = state_data.get("organization_id")

        user_id = state_data.get("user_id")

        if not organization_id or not user_id:
            raise MetaOAuthStateError("OAuth state is incomplete.")

        # ====================================================
        # USER VALIDATION
        # ====================================================

        user = User.objects.filter(
            id=user_id,
            is_deleted=False,
            is_active=True,
        ).first()

        if not user:
            return Response(
                {
                    "message": (
                        "The user who started the OAuth " "flow is no longer available."
                    ),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ====================================================
        # ORGANIZATION VALIDATION
        # ====================================================

        organization = get_organization_by_id(organization_id)

        if not organization:
            return Response(
                {
                    "message": "Organization not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ====================================================
        # CODE → ACCESS TOKEN
        # ====================================================

        client = MetaAPIClient()

        try:
            token_data = client.exchange_code_for_access_token(
                app_id=settings.META_APP_ID,
                app_secret=settings.META_APP_SECRET,
                redirect_uri=(settings.META_OAUTH_REDIRECT_URI),
                code=code,
            )

        except MetaIntegrationError as exc:
            return Response(
                {
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # TEMPORARY SUCCESS RESPONSE
        # ====================================================

        return Response(
            {
                "message": ("Meta OAuth authorization succeeded."),
                "organization_id": (organization.organization_id),
                "token_received": bool(token_data.get("access_token")),
            },
            status=status.HTTP_200_OK,
        )
