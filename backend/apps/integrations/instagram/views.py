import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import (
    BadRequestException,
    ResourceNotFoundException,
)
from apps.common.responses import success_response
from apps.organizations.selectors import (
    get_organization_by_id,
)

from .exceptions import (
    InstagramIntegrationError,
    InstagramOAuthConfigurationError,
    InstagramOAuthStateError,
)
from .oauth import validate_oauth_state
from .services import InstagramOAuthService

logger = logging.getLogger(__name__)

User = get_user_model()


class InstagramOAuthStartAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        organization_id = request.query_params.get("organization_id")

        if not organization_id:
            raise BadRequestException("organization_id is required.")

        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        if organization.created_by_id != request.user.id:
            raise BadRequestException("You do not have access to this organization.")

        try:
            service = InstagramOAuthService()

            authorization_url = service.build_authorization_url(
                organization=organization,
                user=request.user,
            )

        except InstagramOAuthConfigurationError:
            logger.exception("Instagram OAuth configuration error.")

            raise BadRequestException("Instagram OAuth is not configured correctly.")

        except InstagramIntegrationError as exc:
            raise BadRequestException(str(exc))

        return success_response(
            data={
                "authorization_url": authorization_url,
            },
            message=("Instagram authorization URL " "generated successfully."),
        )


class InstagramOAuthCallbackAPIView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(
        self,
        request,
    ):
        error = request.query_params.get("error")

        if error:
            return self._redirect_error(
                request.query_params.get(
                    "error_description",
                    "Instagram authorization was cancelled or denied.",
                )
            )

        code = request.query_params.get("code")

        state = request.query_params.get("state")

        if not code:
            return self._redirect_error("Instagram authorization code is missing.")

        if not state:
            return self._redirect_error("Instagram OAuth state is missing.")

        try:
            state_data = validate_oauth_state(state)

            organization_id = state_data.get("organization_id")

            user_id = state_data.get("user_id")

            if not organization_id or not user_id:
                raise InstagramOAuthStateError("Instagram OAuth state is incomplete.")

            organization = get_organization_by_id(organization_id)

            if not organization:
                raise InstagramOAuthStateError(
                    "Instagram OAuth organization is invalid."
                )

            user = User.objects.filter(
                pk=user_id,
                is_active=True,
                is_deleted=False,
            ).first()

            if not user:
                raise InstagramOAuthStateError("Instagram OAuth user is invalid.")

            if organization.created_by_id != user.id:
                raise InstagramOAuthStateError(
                    "Instagram OAuth organization access is invalid."
                )

            service = InstagramOAuthService()

            social_account = service.handle_callback(
                code=code,
                organization=organization,
                user=user,
            )

            return self._redirect_success(
                organization_id=organization.organization_id,
                social_account_id=str(social_account.id),
            )

        except InstagramOAuthStateError as exc:
            logger.warning(
                "Instagram OAuth state validation failed: %s",
                exc,
            )

            return self._redirect_error(str(exc))

        except InstagramIntegrationError as exc:
            logger.exception("Instagram OAuth integration failed.")

            return self._redirect_error(str(exc))

        except Exception:
            logger.exception("Unexpected Instagram OAuth callback error.")

            return self._redirect_error(
                "Instagram connection failed. Please try again."
            )

    def _redirect_success(
        self,
        *,
        organization_id,
        social_account_id,
    ):
        frontend_url = getattr(
            settings,
            "FRONTEND_URL",
            "",
        ).rstrip("/")

        return redirect(
            (
                f"{frontend_url}/organizations/"
                f"{organization_id}/overview"
                f"?instagram_oauth=success"
                f"&social_account_id={social_account_id}"
            )
        )

    def _redirect_error(
        self,
        message,
    ):
        frontend_url = getattr(
            settings,
            "FRONTEND_URL",
            "",
        ).rstrip("/")

        query = urlencode(
            {
                "instagram_oauth": "error",
                "message": message,
            }
        )

        return redirect(f"{frontend_url}/?{query}")
