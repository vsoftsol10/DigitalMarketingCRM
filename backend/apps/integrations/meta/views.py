import logging
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization

from .client import MetaAPIError
from .constants import (
    META_OAUTH_AUTHORIZE_URL,
    META_OAUTH_STATE_MAX_AGE_SECONDS,
)
from .exceptions import (
    MetaOAuthConfigurationError,
    MetaOAuthStateError,
)
from .oauth import (
    create_oauth_state,
    validate_oauth_state,
)
from .services import MetaOAuthService

logger = logging.getLogger(__name__)


# ============================================================
# FRONTEND REDIRECT
# ============================================================


def _frontend_redirect(
    path: str,
    params=None,
):
    base_url = settings.FRONTEND_URL.rstrip("/")

    url = f"{base_url}/" f"{path.lstrip('/')}"

    if params:
        url = f"{url}?" f"{urlencode(params)}"

    return redirect(url)


# ============================================================
# OAUTH START
# ============================================================


class MetaOAuthStartAPIView(APIView):
    """
    Start Meta Facebook Login for Business OAuth.

    The organization is supplied by the frontend, but the
    organization ID is signed into OAuth state so the callback
    cannot safely substitute another organization.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        organization_id = (
            request.query_params.get(
                "organization_id",
            )
            or ""
        ).strip()

        if not organization_id:
            return Response(
                {
                    "success": False,
                    "message": ("organization_id is required."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        organization = Organization.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).first()

        if not organization:
            return Response(
                {
                    "success": False,
                    "message": "Organization not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not settings.META_APP_ID:
            raise MetaOAuthConfigurationError(
                "Meta App ID is not configured.",
            )

        if not settings.META_APP_SECRET:
            raise MetaOAuthConfigurationError(
                "Meta App Secret is not configured.",
            )

        if not settings.META_BUSINESS_LOGIN_CONFIG_ID:
            raise MetaOAuthConfigurationError(
                "Meta Business Login configuration ID " "is not configured.",
            )

        redirect_uri = (settings.META_OAUTH_REDIRECT_URI or "").strip()

        if not redirect_uri:
            raise MetaOAuthConfigurationError(
                "Meta OAuth redirect URI is not configured.",
            )

        # ----------------------------------------------------
        # SIGNED STATE
        # ----------------------------------------------------

        state = create_oauth_state(
            organization_id=organization.organization_id,
            user_id=request.user.id,
        )

        # ----------------------------------------------------
        # META AUTHORIZATION URL
        # ----------------------------------------------------

        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "config_id": (settings.META_BUSINESS_LOGIN_CONFIG_ID),
        }

        authorization_url = f"{META_OAUTH_AUTHORIZE_URL}" f"?{urlencode(params)}"

        return Response(
            {
                "success": True,
                "authorization_url": authorization_url,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# OAUTH CALLBACK
# ============================================================


class MetaOAuthCallbackAPIView(APIView):
    """
    Meta OAuth callback.

    This endpoint is intentionally AllowAny because the browser
    returns from Meta without the application's JWT.

    The signed OAuth state authenticates the flow context.
    """

    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        # ========================================================
        # CODE + STATE
        # ========================================================

        code = (request.query_params.get("code") or "").strip()

        state = (request.query_params.get("state") or "").strip()

        if not state:
            return _frontend_redirect(
                "/organizations",
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "Invalid Meta OAuth callback.",
                },
            )

        # ========================================================
        # VALIDATE SIGNED STATE
        # ========================================================

        try:
            state_data = validate_oauth_state(
                state,
                max_age=META_OAUTH_STATE_MAX_AGE_SECONDS,
            )

        except MetaOAuthStateError as exc:
            logger.warning(
                "Invalid Meta OAuth state.",
                exc_info=True,
            )

            return _frontend_redirect(
                "/organizations",
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": str(exc),
                },
            )

        organization_id = str(
            state_data.get("organization_id") or "",
        ).strip()

        user_id = state_data.get("user_id")

        # ========================================================
        # ORGANIZATION
        # ========================================================

        organization = Organization.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).first()

        if not organization:
            return _frontend_redirect(
                "/organizations",
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "Organization not found.",
                },
            )

        overview_path = f"/organizations/{organization_id}/overview"

        # ========================================================
        # PROVIDER ERROR
        # ========================================================

        error = (request.query_params.get("error") or "").strip()

        if error:
            error_description = (
                request.query_params.get(
                    "error_description",
                )
                or "Meta authorization was cancelled."
            )

            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": error_description,
                },
            )

        # ========================================================
        # AUTHORIZATION CODE
        # ========================================================

        if not code:
            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "Meta authorization code is missing.",
                },
            )

        # ========================================================
        # USER
        # ========================================================

        from django.contrib.auth import get_user_model

        User = get_user_model()

        user = User.objects.filter(
            id=user_id,
            is_deleted=False,
            is_active=True,
        ).first()

        if not user:
            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "User is no longer available.",
                },
            )

        # ========================================================
        # COMPLETE OAUTH
        # ========================================================

        try:
            result = MetaOAuthService().prepare_oauth(
                code=code,
                organization=organization,
                user=user,
            )

            accounts = result.get("accounts") or []

            facebook_count = sum(
                1
                for account in accounts
                if getattr(account, "platform", None) == "facebook"
            )

            instagram_count = sum(
                1
                for account in accounts
                if getattr(account, "platform", None) == "instagram"
            )

            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "success",
                    "platform": "meta",
                    "accounts_connected": len(accounts),
                    "facebook_connected": facebook_count,
                    "instagram_connected": instagram_count,
                    "organization_id": organization_id,
                },
            )

        except MetaAPIError as exc:
            logger.exception(
                "Meta OAuth API failure for organization=%s",
                organization_id,
            )

            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": str(exc),
                },
            )

        except Exception:
            logger.exception(
                "Unexpected Meta OAuth failure for organization=%s",
                organization_id,
            )

            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "Unable to connect Meta accounts.",
                },
            )
