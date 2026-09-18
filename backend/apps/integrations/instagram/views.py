# before reconect change

# import logging
# from urllib.parse import urlencode

# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.shortcuts import redirect

# from rest_framework.permissions import IsAuthenticated
# from rest_framework.views import APIView

# from apps.common.exceptions import (
#     BadRequestException,
#     ResourceNotFoundException,
# )
# from apps.common.responses import success_response
# from apps.organizations.selectors import (
#     get_organization_by_id,
# )

# from .exceptions import (
#     InstagramIntegrationError,
#     InstagramOAuthConfigurationError,
#     InstagramOAuthStateError,
# )
# from .oauth import validate_oauth_state
# from .services import InstagramOAuthService

# logger = logging.getLogger(__name__)

# User = get_user_model()


# class InstagramOAuthStartAPIView(APIView):
#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def get(
#         self,
#         request,
#     ):
#         organization_id = request.query_params.get("organization_id")

#         if not organization_id:
#             raise BadRequestException("organization_id is required.")

#         organization = get_organization_by_id(organization_id)

#         if not organization:
#             raise ResourceNotFoundException("Organization not found.")

#         if organization.created_by_id != request.user.id:
#             raise BadRequestException("You do not have access to this organization.")

#         try:
#             service = InstagramOAuthService()

#             authorization_url = service.build_authorization_url(
#                 organization=organization,
#                 user=request.user,
#             )

#         except InstagramOAuthConfigurationError:
#             logger.exception("Instagram OAuth configuration error.")

#             raise BadRequestException("Instagram OAuth is not configured correctly.")

#         except InstagramIntegrationError as exc:
#             raise BadRequestException(str(exc))

#         return success_response(
#             data={
#                 "authorization_url": authorization_url,
#             },
#             message=("Instagram authorization URL " "generated successfully."),
#         )


# class InstagramOAuthCallbackAPIView(APIView):
#     permission_classes = []
#     authentication_classes = []

#     def get(
#         self,
#         request,
#     ):
#         error = request.query_params.get("error")

#         if error:
#             return self._redirect_error(
#                 request.query_params.get(
#                     "error_description",
#                     "Instagram authorization was cancelled or denied.",
#                 )
#             )

#         code = request.query_params.get("code")

#         state = request.query_params.get("state")

#         if not code:
#             return self._redirect_error("Instagram authorization code is missing.")

#         if not state:
#             return self._redirect_error("Instagram OAuth state is missing.")

#         try:
#             state_data = validate_oauth_state(state)

#             organization_id = state_data.get("organization_id")

#             user_id = state_data.get("user_id")

#             if not organization_id or not user_id:
#                 raise InstagramOAuthStateError("Instagram OAuth state is incomplete.")

#             organization = get_organization_by_id(organization_id)

#             if not organization:
#                 raise InstagramOAuthStateError(
#                     "Instagram OAuth organization is invalid."
#                 )

#             user = User.objects.filter(
#                 pk=user_id,
#                 is_active=True,
#                 is_deleted=False,
#             ).first()

#             if not user:
#                 raise InstagramOAuthStateError("Instagram OAuth user is invalid.")

#             if organization.created_by_id != user.id:
#                 raise InstagramOAuthStateError(
#                     "Instagram OAuth organization access is invalid."
#                 )

#             service = InstagramOAuthService()

#             social_account = service.handle_callback(
#                 code=code,
#                 organization=organization,
#                 user=user,
#             )

#             return self._redirect_success(
#                 organization_id=organization.organization_id,
#                 social_account_id=str(social_account.id),
#             )

#         except InstagramOAuthStateError as exc:
#             logger.warning(
#                 "Instagram OAuth state validation failed: %s",
#                 exc,
#             )

#             return self._redirect_error(str(exc))

#         except InstagramIntegrationError as exc:
#             logger.exception("Instagram OAuth integration failed.")

#             return self._redirect_error(str(exc))

#         except Exception:
#             logger.exception("Unexpected Instagram OAuth callback error.")

#             return self._redirect_error(
#                 "Instagram connection failed. Please try again."
#             )

#     def _redirect_success(
#         self,
#         *,
#         organization_id,
#         social_account_id,
#     ):
#         frontend_url = getattr(
#             settings,
#             "FRONTEND_URL",
#             "",
#         ).rstrip("/")

#         return redirect(
#             (
#                 f"{frontend_url}/organizations/"
#                 f"{organization_id}/overview"
#                 f"?instagram_oauth=success"
#                 f"&social_account_id={social_account_id}"
#             )
#         )

#     def _redirect_error(
#         self,
#         message,
#     ):
#         frontend_url = getattr(
#             settings,
#             "FRONTEND_URL",
#             "",
#         ).rstrip("/")

#         query = urlencode(
#             {
#                 "instagram_oauth": "error",
#                 "message": message,
#             }
#         )

#         return redirect(f"{frontend_url}/?{query}")


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
from apps.social_accounts.models import (
    SocialAccount,
    SocialPlatform,
)

from .exceptions import (
    InstagramIntegrationError,
    InstagramOAuthConfigurationError,
    InstagramOAuthStateError,
)
from .constants import INSTAGRAM_OAUTH_SCOPES
from .oauth import (
    OAUTH_ACTION_CONNECT,
    OAUTH_ACTION_RECONNECT,
    create_oauth_nonce,
    create_oauth_state,
    validate_oauth_state,
)
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

        action = (
            str(
                request.query_params.get(
                    "action",
                    OAUTH_ACTION_CONNECT,
                )
                or OAUTH_ACTION_CONNECT
            )
            .strip()
            .lower()
        )

        social_account_id = request.query_params.get("social_account_id")

        # ====================================================
        # BASIC VALIDATION
        # ====================================================

        if not organization_id:
            raise BadRequestException("organization_id is required.")

        if action not in {
            OAUTH_ACTION_CONNECT,
            OAUTH_ACTION_RECONNECT,
        }:
            raise BadRequestException("Invalid Instagram OAuth action.")

        # ====================================================
        # ORGANIZATION
        # ====================================================

        organization = get_organization_by_id(organization_id)

        if not organization:
            raise ResourceNotFoundException("Organization not found.")

        if organization.created_by_id != request.user.id:
            raise BadRequestException("You do not have access to this organization.")

        # ====================================================
        # RECONNECT TARGET VALIDATION
        # ====================================================

        if action == OAUTH_ACTION_RECONNECT:
            if not social_account_id:
                raise BadRequestException(
                    "social_account_id is required for reconnect."
                )

            social_account = SocialAccount.objects.filter(
                id=social_account_id,
                organization=organization,
                platform=SocialPlatform.INSTAGRAM,
                is_deleted=False,
            ).first()

            if not social_account:
                raise ResourceNotFoundException(
                    "The Instagram account selected for reconnect " "was not found."
                )

        try:
            # ==================================================
            # BUILD SIGNED OAUTH STATE
            # ==================================================

            nonce = create_oauth_nonce()

            state = create_oauth_state(
                organization_id=organization.organization_id,
                user_id=request.user.pk,
                nonce=nonce,
                action=action,
                social_account_id=(
                    social_account_id if action == OAUTH_ACTION_RECONNECT else None
                ),
            )

            service = InstagramOAuthService()

            # ==================================================
            # BUILD AUTHORIZATION URL
            #
            # Existing service method is used only for the
            # provider configuration/authorization parameters.
            # We generate the state here so reconnect metadata
            # is included.
            # ==================================================

            if action == OAUTH_ACTION_CONNECT:
                authorization_url = service.build_authorization_url(
                    organization=organization,
                    user=request.user,
                )

            else:
                params = {
                    "client_id": service.client.client_id,
                    "redirect_uri": service.client.redirect_uri,
                    "response_type": "code",
                    "scope": ",".join(INSTAGRAM_OAUTH_SCOPES),
                    "state": state,
                }

                authorization_url = (
                    "https://www.instagram.com/oauth/authorize?" f"{urlencode(params)}"
                )

        except InstagramOAuthConfigurationError:
            logger.exception("Instagram OAuth configuration error.")

            raise BadRequestException("Instagram OAuth is not configured correctly.")

        except InstagramOAuthStateError as exc:
            raise BadRequestException(str(exc))

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
            # ==================================================
            # VALIDATE SIGNED STATE
            # ==================================================

            state_data = validate_oauth_state(state)

            organization_id = state_data.get("organization_id")

            user_id = state_data.get("user_id")

            action = (
                str(
                    state_data.get(
                        "action",
                        OAUTH_ACTION_CONNECT,
                    )
                    or OAUTH_ACTION_CONNECT
                )
                .strip()
                .lower()
            )

            social_account_id = state_data.get("social_account_id")

            if not organization_id or not user_id:
                raise InstagramOAuthStateError("Instagram OAuth state is incomplete.")

            # ==================================================
            # ORGANIZATION
            # ==================================================

            organization = get_organization_by_id(organization_id)

            if not organization:
                raise InstagramOAuthStateError(
                    "Instagram OAuth organization is invalid."
                )

            # ==================================================
            # USER
            # ==================================================

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

            # ==================================================
            # RECONNECT TARGET
            # ==================================================

            if action == OAUTH_ACTION_RECONNECT:
                if not social_account_id:
                    raise InstagramOAuthStateError(
                        "Instagram reconnect account information is missing."
                    )

                social_account = SocialAccount.objects.filter(
                    id=social_account_id,
                    organization=organization,
                    platform=SocialPlatform.INSTAGRAM,
                    is_deleted=False,
                ).first()

                if not social_account:
                    raise InstagramOAuthStateError(
                        "The Instagram account selected for reconnect " "was not found."
                    )

                service = InstagramOAuthService()

                social_account = service.reconnect_existing_account(
                    code=code,
                    organization=organization,
                    user=user,
                    social_account_id=social_account_id,
                )

                return self._redirect_reconnect_success(
                    organization_id=organization.organization_id,
                    social_account_id=str(social_account.id),
                )

            # ==================================================
            # NORMAL CONNECT
            # ==================================================

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

    # ========================================================
    # NORMAL CONNECT SUCCESS
    # ========================================================

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

    # ========================================================
    # RECONNECT SUCCESS
    # ========================================================

    def _redirect_reconnect_success(
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
                f"?instagram_oauth=reconnect_success"
                f"&social_account_id={social_account_id}"
            )
        )

    # ========================================================
    # ERROR
    # ========================================================

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
