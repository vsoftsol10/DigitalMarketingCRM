# reconect change

# # import logging
# # from urllib.parse import urlencode

# # from django.conf import settings
# # from django.contrib.auth import get_user_model
# # from django.shortcuts import redirect
# # from rest_framework import status
# # from rest_framework.permissions import AllowAny, IsAuthenticated
# # from rest_framework.response import Response
# # from rest_framework.views import APIView

# # from apps.organizations.models import Organization

# # from .client import MetaAPIError
# # from .constants import (
# #     META_OAUTH_AUTHORIZE_URL,
# #     META_OAUTH_STATE_MAX_AGE_SECONDS,
# # )
# # from .exceptions import (
# #     MetaOAuthConfigurationError,
# #     MetaOAuthStateError,
# # )
# # from .models import MetaOAuthSession
# # from .oauth import (
# #     create_oauth_state,
# #     validate_oauth_state,
# # )
# # from .services import MetaOAuthService

# # logger = logging.getLogger(__name__)


# # # ============================================================
# # # FRONTEND REDIRECT
# # # ============================================================


# # def _frontend_redirect(
# #     path: str,
# #     params=None,
# # ):
# #     base_url = settings.FRONTEND_URL.rstrip("/")

# #     url = f"{base_url}/{path.lstrip('/')}"

# #     if params:
# #         url = f"{url}?{urlencode(params)}"

# #     return redirect(url)


# # # ============================================================
# # # OAUTH START
# # # ============================================================


# # class MetaOAuthStartAPIView(APIView):
# #     """
# #     Start Meta Facebook Login for Business OAuth.
# #     """

# #     permission_classes = [
# #         IsAuthenticated,
# #     ]

# #     def get(
# #         self,
# #         request,
# #     ):
# #         organization_id = (request.query_params.get("organization_id") or "").strip()

# #         if not organization_id:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "organization_id is required.",
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         organization = Organization.objects.filter(
# #             organization_id=organization_id,
# #             is_deleted=False,
# #         ).first()

# #         if not organization:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Organization not found.",
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         if not settings.META_APP_ID:
# #             raise MetaOAuthConfigurationError(
# #                 "Meta App ID is not configured.",
# #             )

# #         if not settings.META_APP_SECRET:
# #             raise MetaOAuthConfigurationError(
# #                 "Meta App Secret is not configured.",
# #             )

# #         if not settings.META_BUSINESS_LOGIN_CONFIG_ID:
# #             raise MetaOAuthConfigurationError(
# #                 "Meta Business Login configuration ID is not configured.",
# #             )

# #         redirect_uri = (settings.META_OAUTH_REDIRECT_URI or "").strip()

# #         if not redirect_uri:
# #             raise MetaOAuthConfigurationError(
# #                 "Meta OAuth redirect URI is not configured.",
# #             )

# #         state = create_oauth_state(
# #             organization_id=organization.organization_id,
# #             user_id=request.user.id,
# #         )

# #         params = {
# #             "client_id": settings.META_APP_ID,
# #             "redirect_uri": redirect_uri,
# #             "state": state,
# #             "response_type": "code",
# #             "config_id": settings.META_BUSINESS_LOGIN_CONFIG_ID,
# #         }

# #         authorization_url = f"{META_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

# #         return Response(
# #             {
# #                 "success": True,
# #                 "authorization_url": authorization_url,
# #             },
# #             status=status.HTTP_200_OK,
# #         )


# # # ============================================================
# # # OAUTH CALLBACK
# # # ============================================================


# # class MetaOAuthCallbackAPIView(APIView):
# #     """
# #     Meta OAuth callback.

# #     The callback is AllowAny because Meta redirects the browser
# #     without the application's JWT.

# #     The signed OAuth state authenticates the OAuth flow context.
# #     """

# #     permission_classes = [
# #         AllowAny,
# #     ]

# #     def get(
# #         self,
# #         request,
# #     ):
# #         code = (request.query_params.get("code") or "").strip()

# #         state = (request.query_params.get("state") or "").strip()

# #         if not state:
# #             return _frontend_redirect(
# #                 "/organizations",
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": "Invalid Meta OAuth callback.",
# #                 },
# #             )

# #         # ====================================================
# #         # VALIDATE STATE
# #         # ====================================================

# #         try:
# #             state_data = validate_oauth_state(
# #                 state,
# #                 max_age=META_OAUTH_STATE_MAX_AGE_SECONDS,
# #             )

# #         except MetaOAuthStateError as exc:
# #             logger.warning(
# #                 "Invalid Meta OAuth state.",
# #                 exc_info=True,
# #             )

# #             return _frontend_redirect(
# #                 "/organizations",
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": str(exc),
# #                 },
# #             )

# #         organization_id = str(
# #             state_data.get("organization_id") or "",
# #         ).strip()

# #         user_id = state_data.get("user_id")

# #         # ====================================================
# #         # ORGANIZATION
# #         # ====================================================

# #         organization = Organization.objects.filter(
# #             organization_id=organization_id,
# #             is_deleted=False,
# #         ).first()

# #         if not organization:
# #             return _frontend_redirect(
# #                 "/organizations",
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": "Organization not found.",
# #                 },
# #             )

# #         overview_path = f"/organizations/{organization_id}/overview"

# #         # ====================================================
# #         # META PROVIDER ERROR
# #         # ====================================================

# #         error = (request.query_params.get("error") or "").strip()

# #         if error:
# #             error_description = (
# #                 request.query_params.get(
# #                     "error_description",
# #                 )
# #                 or "Meta authorization was cancelled."
# #             )

# #             return _frontend_redirect(
# #                 overview_path,
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": error_description,
# #                 },
# #             )

# #         # ====================================================
# #         # AUTHORIZATION CODE
# #         # ====================================================

# #         if not code:
# #             return _frontend_redirect(
# #                 overview_path,
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": "Meta authorization code is missing.",
# #                 },
# #             )

# #         # ====================================================
# #         # USER
# #         # ====================================================

# #         User = get_user_model()

# #         user = User.objects.filter(
# #             id=user_id,
# #             is_deleted=False,
# #             is_active=True,
# #         ).first()

# #         if not user:
# #             return _frontend_redirect(
# #                 overview_path,
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": "User is no longer available.",
# #                 },
# #             )

# #         # ====================================================
# #         # COMPLETE OAUTH DISCOVERY
# #         # ====================================================

# #         try:
# #             result = MetaOAuthService().prepare_oauth(
# #                 code=code,
# #                 organization=organization,
# #                 user=user,
# #             )

# #             # ------------------------------------------------
# #             # DIRECT CONNECTION
# #             # ------------------------------------------------

# #             if result.get("status") == "connected":
# #                 accounts = result.get("accounts") or []

# #                 facebook_count = sum(
# #                     1
# #                     for account in accounts
# #                     if getattr(
# #                         account,
# #                         "platform",
# #                         None,
# #                     )
# #                     == "facebook"
# #                 )

# #                 instagram_count = sum(
# #                     1
# #                     for account in accounts
# #                     if getattr(
# #                         account,
# #                         "platform",
# #                         None,
# #                     )
# #                     == "instagram"
# #                 )

# #                 return _frontend_redirect(
# #                     overview_path,
# #                     {
# #                         "social_connect": "success",
# #                         "platform": "meta",
# #                         "accounts_connected": len(accounts),
# #                         "facebook_connected": facebook_count,
# #                         "instagram_connected": instagram_count,
# #                         "organization_id": organization_id,
# #                     },
# #                 )

# #             # ------------------------------------------------
# #             # MULTIPLE PAGES
# #             # ------------------------------------------------

# #             if result.get("status") == "selection_required":
# #                 session = result.get("session")

# #                 if not session:
# #                     raise MetaAPIError(
# #                         "Meta Page selection session was not created.",
# #                     )

# #                 return _frontend_redirect(
# #                     overview_path,
# #                     {
# #                         "social_connect": "selection",
# #                         "platform": "meta",
# #                         "selection_key": str(
# #                             session.selection_key,
# #                         ),
# #                     },
# #                 )

# #             raise MetaAPIError(
# #                 "Unexpected Meta OAuth result.",
# #             )

# #         except MetaAPIError as exc:
# #             logger.exception(
# #                 "Meta OAuth API failure for organization=%s",
# #                 organization_id,
# #             )

# #             return _frontend_redirect(
# #                 overview_path,
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": str(exc),
# #                 },
# #             )

# #         except Exception:
# #             logger.exception(
# #                 "Unexpected Meta OAuth failure for organization=%s",
# #                 organization_id,
# #             )

# #             return _frontend_redirect(
# #                 overview_path,
# #                 {
# #                     "social_connect": "error",
# #                     "platform": "meta",
# #                     "reason": "Unable to connect Meta accounts.",
# #                 },
# #             )


# # # ============================================================
# # # PAGE SELECTION
# # # ============================================================


# # class MetaOAuthSelectionAPIView(APIView):
# #     """
# #     Return the temporary Facebook Page selection data.

# #     Tokens are never returned to the frontend.
# #     """

# #     permission_classes = [
# #         IsAuthenticated,
# #     ]

# #     def get(
# #         self,
# #         request,
# #     ):
# #         selection_key = (request.query_params.get("selection_key") or "").strip()

# #         organization_id = (request.query_params.get("organization_id") or "").strip()

# #         if not selection_key:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "selection_key is required.",
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         if not organization_id:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "organization_id is required.",
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         organization = Organization.objects.filter(
# #             organization_id=organization_id,
# #             is_deleted=False,
# #         ).first()

# #         if not organization:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Organization not found.",
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         session = MetaOAuthSession.objects.filter(
# #             selection_key=selection_key,
# #         ).first()

# #         if not session:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Meta authorization session was not found.",
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         try:
# #             data = MetaOAuthService().get_selection_data(
# #                 session=session,
# #                 organization=organization,
# #                 user=request.user,
# #             )

# #             return Response(
# #                 {
# #                     "success": True,
# #                     "data": data,
# #                 },
# #                 status=status.HTTP_200_OK,
# #             )

# #         except MetaAPIError as exc:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": str(exc),
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         except Exception:
# #             logger.exception(
# #                 "Unable to load Meta Page selection.",
# #             )

# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Unable to load Meta Pages.",
# #                 },
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             )


# # # ============================================================
# # # PAGE SELECTION CONFIRM
# # # ============================================================


# # class MetaOAuthSelectionConfirmAPIView(APIView):
# #     """
# #     Confirm one Facebook Page selected by the user.

# #     Frontend sends only:
# #         selection_key
# #         organization_id
# #         page_id

# #     Access tokens remain server-side.
# #     """

# #     permission_classes = [
# #         IsAuthenticated,
# #     ]

# #     def post(
# #         self,
# #         request,
# #     ):
# #         selection_key = str(
# #             request.data.get("selection_key") or "",
# #         ).strip()

# #         organization_id = str(
# #             request.data.get("organization_id") or "",
# #         ).strip()

# #         page_id = str(
# #             request.data.get("page_id") or "",
# #         ).strip()

# #         if not selection_key:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "selection_key is required.",
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         if not organization_id:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "organization_id is required.",
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         if not page_id:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "page_id is required.",
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         organization = Organization.objects.filter(
# #             organization_id=organization_id,
# #             is_deleted=False,
# #         ).first()

# #         if not organization:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Organization not found.",
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         session = MetaOAuthSession.objects.filter(
# #             selection_key=selection_key,
# #         ).first()

# #         if not session:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Meta authorization session was not found.",
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         try:
# #             result = MetaOAuthService().confirm_selection(
# #                 session=session,
# #                 organization=organization,
# #                 user=request.user,
# #                 page_id=page_id,
# #             )

# #             accounts = result.get("accounts") or []

# #             facebook_count = sum(
# #                 1
# #                 for account in accounts
# #                 if getattr(
# #                     account,
# #                     "platform",
# #                     None,
# #                 )
# #                 == "facebook"
# #             )

# #             instagram_count = sum(
# #                 1
# #                 for account in accounts
# #                 if getattr(
# #                     account,
# #                     "platform",
# #                     None,
# #                 )
# #                 == "instagram"
# #             )

# #             return Response(
# #                 {
# #                     "success": True,
# #                     "message": "Meta accounts connected successfully.",
# #                     "data": {
# #                         "accounts_connected": len(accounts),
# #                         "facebook_connected": facebook_count,
# #                         "instagram_connected": instagram_count,
# #                     },
# #                 },
# #                 status=status.HTTP_200_OK,
# #             )

# #         except MetaAPIError as exc:
# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": str(exc),
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         except Exception:
# #             logger.exception(
# #                 "Unable to confirm Meta Page selection.",
# #             )

# #             return Response(
# #                 {
# #                     "success": False,
# #                     "message": "Unable to connect the selected Meta Page.",
# #                 },
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             )

# import logging
# from urllib.parse import urlencode

# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.shortcuts import redirect
# from rest_framework import status
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from apps.organizations.models import Organization

# from .client import MetaAPIError
# from .constants import (
#     META_OAUTH_AUTHORIZE_URL,
#     META_OAUTH_STATE_MAX_AGE_SECONDS,
# )
# from .exceptions import (
#     MetaOAuthConfigurationError,
#     MetaOAuthStateError,
# )
# from .models import MetaOAuthSession
# from .oauth import (
#     create_oauth_state,
#     validate_oauth_state,
# )
# from .services import MetaOAuthService

# logger = logging.getLogger(__name__)


# # ============================================================
# # FRONTEND REDIRECT
# # ============================================================


# def _frontend_redirect(
#     path: str,
#     params=None,
# ):
#     base_url = settings.FRONTEND_URL.rstrip("/")

#     url = f"{base_url}/{path.lstrip('/')}"

#     if params:
#         url = f"{url}?{urlencode(params)}"

#     return redirect(url)


# # ============================================================
# # OAUTH START
# # ============================================================


# class MetaOAuthStartAPIView(APIView):
#     """
#     Start Meta OAuth for connecting Facebook Pages.
#     """

#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def get(
#         self,
#         request,
#     ):
#         organization_id = (request.query_params.get("organization_id") or "").strip()

#         if not organization_id:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "organization_id is required.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         organization = Organization.objects.filter(
#             organization_id=organization_id,
#             is_deleted=False,
#         ).first()

#         if not organization:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "Organization not found.",
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         if not settings.META_APP_ID:
#             raise MetaOAuthConfigurationError(
#                 "Meta App ID is not configured.",
#             )

#         if not settings.META_APP_SECRET:
#             raise MetaOAuthConfigurationError(
#                 "Meta App Secret is not configured.",
#             )

#         if not settings.META_BUSINESS_LOGIN_CONFIG_ID:
#             raise MetaOAuthConfigurationError(
#                 "Meta Business Login configuration ID is not configured.",
#             )

#         redirect_uri = (settings.META_OAUTH_REDIRECT_URI or "").strip()

#         if not redirect_uri:
#             raise MetaOAuthConfigurationError(
#                 "Meta OAuth redirect URI is not configured.",
#             )

#         state = create_oauth_state(
#             organization_id=organization.organization_id,
#             user_id=request.user.id,
#         )

#         params = {
#             "client_id": settings.META_APP_ID,
#             "redirect_uri": redirect_uri,
#             "state": state,
#             "response_type": "code",
#             "config_id": settings.META_BUSINESS_LOGIN_CONFIG_ID,
#         }

#         authorization_url = f"{META_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

#         return Response(
#             {
#                 "success": True,
#                 "authorization_url": authorization_url,
#             },
#             status=status.HTTP_200_OK,
#         )


# # ============================================================
# # OAUTH CALLBACK
# # ============================================================


# class MetaOAuthCallbackAPIView(APIView):
#     """
#     Handle Meta OAuth callback for Facebook Page connection.

#     Meta redirects the browser without the application's JWT,
#     therefore this endpoint is intentionally AllowAny.

#     The signed OAuth state authenticates the OAuth flow context.
#     """

#     permission_classes = [
#         AllowAny,
#     ]

#     def get(
#         self,
#         request,
#     ):
#         code = (request.query_params.get("code") or "").strip()

#         state = (request.query_params.get("state") or "").strip()

#         # ====================================================
#         # STATE
#         # ====================================================

#         if not state:
#             return _frontend_redirect(
#                 "/organizations",
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": "Invalid Meta OAuth callback.",
#                 },
#             )

#         # ====================================================
#         # VALIDATE STATE
#         # ====================================================

#         try:
#             state_data = validate_oauth_state(
#                 state,
#                 max_age=META_OAUTH_STATE_MAX_AGE_SECONDS,
#             )

#         except MetaOAuthStateError as exc:
#             logger.warning(
#                 "Invalid Meta OAuth state.",
#                 exc_info=True,
#             )

#             return _frontend_redirect(
#                 "/organizations",
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": str(exc),
#                 },
#             )

#         organization_id = str(
#             state_data.get("organization_id") or "",
#         ).strip()

#         user_id = state_data.get("user_id")

#         # ====================================================
#         # ORGANIZATION
#         # ====================================================

#         organization = Organization.objects.filter(
#             organization_id=organization_id,
#             is_deleted=False,
#         ).first()

#         if not organization:
#             return _frontend_redirect(
#                 "/organizations",
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": "Organization not found.",
#                 },
#             )

#         overview_path = f"/organizations/{organization_id}/overview"

#         # ====================================================
#         # META PROVIDER ERROR
#         # ====================================================

#         error = (request.query_params.get("error") or "").strip()

#         if error:
#             error_description = (
#                 request.query_params.get(
#                     "error_description",
#                 )
#                 or "Meta authorization was cancelled."
#             )

#             return _frontend_redirect(
#                 overview_path,
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": error_description,
#                 },
#             )

#         # ====================================================
#         # AUTHORIZATION CODE
#         # ====================================================

#         if not code:
#             return _frontend_redirect(
#                 overview_path,
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": "Meta authorization code is missing.",
#                 },
#             )

#         # ====================================================
#         # USER
#         # ====================================================

#         User = get_user_model()

#         user = User.objects.filter(
#             id=user_id,
#             is_deleted=False,
#             is_active=True,
#         ).first()

#         if not user:
#             return _frontend_redirect(
#                 overview_path,
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": "User is no longer available.",
#                 },
#             )

#         # ====================================================
#         # COMPLETE FACEBOOK OAUTH
#         # ====================================================

#         try:
#             result = MetaOAuthService().prepare_oauth(
#                 code=code,
#                 organization=organization,
#                 user=user,
#             )

#             # ------------------------------------------------
#             # DIRECT FACEBOOK CONNECTION
#             # ------------------------------------------------

#             if result.get("status") == "connected":
#                 accounts = result.get("accounts") or []

#                 facebook_count = sum(
#                     1
#                     for account in accounts
#                     if getattr(
#                         account,
#                         "platform",
#                         None,
#                     )
#                     == "facebook"
#                 )

#                 return _frontend_redirect(
#                     overview_path,
#                     {
#                         "social_connect": "success",
#                         "platform": "meta",
#                         "accounts_connected": facebook_count,
#                         "facebook_connected": facebook_count,
#                         "organization_id": organization_id,
#                     },
#                 )

#             # ------------------------------------------------
#             # MULTIPLE FACEBOOK PAGES
#             # ------------------------------------------------

#             if result.get("status") == "selection_required":
#                 session = result.get("session")

#                 if not session:
#                     raise MetaAPIError(
#                         "Meta Page selection session was not created.",
#                     )

#                 return _frontend_redirect(
#                     overview_path,
#                     {
#                         "social_connect": "selection",
#                         "platform": "meta",
#                         "selection_key": str(
#                             session.selection_key,
#                         ),
#                     },
#                 )

#             raise MetaAPIError(
#                 "Unexpected Meta OAuth result.",
#             )

#         except MetaAPIError as exc:
#             logger.exception(
#                 "Meta OAuth API failure for organization=%s",
#                 organization_id,
#             )

#             return _frontend_redirect(
#                 overview_path,
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": str(exc),
#                 },
#             )

#         except Exception:
#             logger.exception(
#                 "Unexpected Meta OAuth failure for organization=%s",
#                 organization_id,
#             )

#             return _frontend_redirect(
#                 overview_path,
#                 {
#                     "social_connect": "error",
#                     "platform": "meta",
#                     "reason": "Unable to connect Facebook Page.",
#                 },
#             )


# # ============================================================
# # FACEBOOK PAGE SELECTION
# # ============================================================


# class MetaOAuthSelectionAPIView(APIView):
#     """
#     Return temporary Facebook Page selection data.

#     OAuth tokens are never returned to the frontend.
#     """

#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def get(
#         self,
#         request,
#     ):
#         selection_key = (request.query_params.get("selection_key") or "").strip()

#         organization_id = (request.query_params.get("organization_id") or "").strip()

#         # ====================================================
#         # VALIDATION
#         # ====================================================

#         if not selection_key:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "selection_key is required.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         if not organization_id:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "organization_id is required.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # ====================================================
#         # ORGANIZATION
#         # ====================================================

#         organization = Organization.objects.filter(
#             organization_id=organization_id,
#             is_deleted=False,
#         ).first()

#         if not organization:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "Organization not found.",
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         # ====================================================
#         # SESSION
#         # ====================================================

#         session = MetaOAuthSession.objects.filter(
#             selection_key=selection_key,
#         ).first()

#         if not session:
#             return Response(
#                 {
#                     "success": False,
#                     "message": ("Meta authorization session was not found."),
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         # ====================================================
#         # GET FACEBOOK PAGES
#         # ====================================================

#         try:
#             data = MetaOAuthService().get_selection_data(
#                 session=session,
#                 organization=organization,
#                 user=request.user,
#             )

#             return Response(
#                 {
#                     "success": True,
#                     "data": data,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except MetaAPIError as exc:
#             return Response(
#                 {
#                     "success": False,
#                     "message": str(exc),
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         except Exception:
#             logger.exception(
#                 "Unable to load Meta Page selection.",
#             )

#             return Response(
#                 {
#                     "success": False,
#                     "message": "Unable to load Facebook Pages.",
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )


# # ============================================================
# # FACEBOOK PAGE SELECTION CONFIRM
# # ============================================================


# class MetaOAuthSelectionConfirmAPIView(APIView):
#     """
#     Confirm one Facebook Page selected by the user.

#     Frontend sends:

#         selection_key
#         organization_id
#         page_id

#     OAuth access tokens remain server-side.
#     """

#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def post(
#         self,
#         request,
#     ):
#         selection_key = str(
#             request.data.get("selection_key") or "",
#         ).strip()

#         organization_id = str(
#             request.data.get("organization_id") or "",
#         ).strip()

#         page_id = str(
#             request.data.get("page_id") or "",
#         ).strip()

#         # ====================================================
#         # VALIDATION
#         # ====================================================

#         if not selection_key:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "selection_key is required.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         if not organization_id:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "organization_id is required.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         if not page_id:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "page_id is required.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # ====================================================
#         # ORGANIZATION
#         # ====================================================

#         organization = Organization.objects.filter(
#             organization_id=organization_id,
#             is_deleted=False,
#         ).first()

#         if not organization:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "Organization not found.",
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         # ====================================================
#         # SESSION
#         # ====================================================

#         session = MetaOAuthSession.objects.filter(
#             selection_key=selection_key,
#         ).first()

#         if not session:
#             return Response(
#                 {
#                     "success": False,
#                     "message": ("Meta authorization session was not found."),
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         # ====================================================
#         # CONFIRM FACEBOOK PAGE
#         # ====================================================

#         try:
#             result = MetaOAuthService().confirm_selection(
#                 session=session,
#                 organization=organization,
#                 user=request.user,
#                 page_id=page_id,
#             )

#             accounts = result.get("accounts") or []

#             facebook_count = sum(
#                 1
#                 for account in accounts
#                 if getattr(
#                     account,
#                     "platform",
#                     None,
#                 )
#                 == "facebook"
#             )

#             return Response(
#                 {
#                     "success": True,
#                     "message": ("Facebook Page connected successfully."),
#                     "data": {
#                         "accounts_connected": facebook_count,
#                         "facebook_connected": facebook_count,
#                     },
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except MetaAPIError as exc:
#             return Response(
#                 {
#                     "success": False,
#                     "message": str(exc),
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         except Exception:
#             logger.exception(
#                 "Unable to confirm Meta Page selection.",
#             )

#             return Response(
#                 {
#                     "success": False,
#                     "message": ("Unable to connect the selected Facebook Page."),
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )


import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization
from apps.social_accounts.models import (
    SocialAccount,
    SocialPlatform,
)

from .client import MetaAPIError
from .constants import (
    META_OAUTH_AUTHORIZE_URL,
    META_OAUTH_STATE_MAX_AGE_SECONDS,
)
from .exceptions import (
    MetaOAuthConfigurationError,
    MetaOAuthStateError,
)
from .models import MetaOAuthSession
from .oauth import (
    OAUTH_ACTION_CONNECT,
    OAUTH_ACTION_RECONNECT,
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

    url = f"{base_url}/{path.lstrip('/')}"

    if params:
        url = f"{url}?{urlencode(params)}"

    return redirect(url)


# ============================================================
# OAUTH START
# ============================================================


class MetaOAuthStartAPIView(APIView):
    """
    Start Meta OAuth for connecting or reconnecting
    Facebook Pages.

    CONNECT:
        /oauth/start/?organization_id=<id>

    RECONNECT:
        /oauth/start/
        ?organization_id=<id>
        &action=reconnect
        &social_account_id=<id>
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        # ====================================================
        # ORGANIZATION ID
        # ====================================================

        organization_id = (request.query_params.get("organization_id") or "").strip()

        if not organization_id:
            return Response(
                {
                    "success": False,
                    "message": "organization_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # ORGANIZATION
        # ====================================================

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

        # ====================================================
        # OAUTH ACTION
        # ====================================================

        action = (
            (request.query_params.get("action") or OAUTH_ACTION_CONNECT).strip().lower()
        )

        if action not in {
            OAUTH_ACTION_CONNECT,
            OAUTH_ACTION_RECONNECT,
        }:
            return Response(
                {
                    "success": False,
                    "message": "Invalid OAuth action.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # RECONNECT TARGET
        # ====================================================

        social_account_id = (
            request.query_params.get("social_account_id") or ""
        ).strip()

        target_account = None

        if action == OAUTH_ACTION_RECONNECT:

            if not social_account_id:
                return Response(
                    {
                        "success": False,
                        "message": ("social_account_id is required " "for reconnect."),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            target_account = SocialAccount.objects.filter(
                id=social_account_id,
                organization=organization,
                platform=SocialPlatform.FACEBOOK,
                is_deleted=False,
            ).first()

            if not target_account:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "The Facebook account selected "
                            "for reconnect was not found."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        # ====================================================
        # META CONFIGURATION
        # ====================================================

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

        # ====================================================
        # SIGNED OAUTH STATE
        # ====================================================

        state = create_oauth_state(
            organization_id=organization.organization_id,
            user_id=request.user.id,
            action=action,
            social_account_id=(target_account.id if target_account else None),
        )

        # ====================================================
        # META AUTHORIZATION URL
        # ====================================================

        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "config_id": settings.META_BUSINESS_LOGIN_CONFIG_ID,
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
    Handle Meta OAuth callback.

    Meta redirects the browser without the application's JWT,
    therefore this endpoint is intentionally AllowAny.

    The signed OAuth state authenticates and binds the flow to:

        - user
        - organization
        - action
        - reconnect target, when applicable
    """

    permission_classes = [
        AllowAny,
    ]

    def get(
        self,
        request,
    ):
        # ====================================================
        # CALLBACK PARAMETERS
        # ====================================================

        code = (request.query_params.get("code") or "").strip()

        state = (request.query_params.get("state") or "").strip()

        # ====================================================
        # STATE REQUIRED
        # ====================================================

        if not state:
            return _frontend_redirect(
                "/organizations",
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "Invalid Meta OAuth callback.",
                },
            )

        # ====================================================
        # VALIDATE SIGNED STATE
        # ====================================================

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

        # ====================================================
        # STATE DATA
        # ====================================================

        organization_id = str(
            state_data.get("organization_id") or "",
        ).strip()

        user_id = state_data.get(
            "user_id",
        )

        action = (
            str(
                state_data.get("action") or OAUTH_ACTION_CONNECT,
            )
            .strip()
            .lower()
        )

        social_account_id = str(
            state_data.get("social_account_id") or "",
        ).strip()

        # ====================================================
        # ACTION VALIDATION
        # ====================================================

        if action not in {
            OAUTH_ACTION_CONNECT,
            OAUTH_ACTION_RECONNECT,
        }:
            return _frontend_redirect(
                "/organizations",
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": "Invalid Meta OAuth action.",
                },
            )

        # ====================================================
        # RECONNECT TARGET VALIDATION
        # ====================================================

        if action == OAUTH_ACTION_RECONNECT and not social_account_id:
            return _frontend_redirect(
                "/organizations",
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": ("Reconnect target Facebook " "account is missing."),
                },
            )

        # ====================================================
        # ORGANIZATION
        # ====================================================

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

        overview_path = f"/organizations/" f"{organization_id}/overview"

        # ====================================================
        # META PROVIDER ERROR
        # ====================================================

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

        # ====================================================
        # AUTHORIZATION CODE
        # ====================================================

        if not code:
            return _frontend_redirect(
                overview_path,
                {
                    "social_connect": "error",
                    "platform": "meta",
                    "reason": ("Meta authorization code is missing."),
                },
            )

        # ====================================================
        # USER
        # ====================================================

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

        # ====================================================
        # RECONNECT TARGET — SECOND SERVER-SIDE VALIDATION
        # ====================================================

        if action == OAUTH_ACTION_RECONNECT:

            target_account = SocialAccount.objects.filter(
                id=social_account_id,
                organization=organization,
                platform=SocialPlatform.FACEBOOK,
                is_deleted=False,
            ).first()

            if not target_account:
                return _frontend_redirect(
                    overview_path,
                    {
                        "social_connect": "error",
                        "platform": "meta",
                        "reason": (
                            "The Facebook account selected "
                            "for reconnect no longer exists."
                        ),
                    },
                )

        # ====================================================
        # COMPLETE FACEBOOK OAUTH
        # ====================================================

        try:
            result = MetaOAuthService().prepare_oauth(
                code=code,
                organization=organization,
                user=user,
                action=action,
                social_account_id=social_account_id or None,
            )

            # =================================================
            # SUCCESS
            # =================================================

            if result.get("status") == "connected":

                accounts = result.get("accounts") or []

                facebook_count = sum(
                    1
                    for account in accounts
                    if getattr(
                        account,
                        "platform",
                        None,
                    )
                    == SocialPlatform.FACEBOOK
                )

                # ---------------------------------------------
                # RECONNECT SUCCESS
                # ---------------------------------------------

                if action == OAUTH_ACTION_RECONNECT:
                    return _frontend_redirect(
                        overview_path,
                        {
                            "social_connect": "reconnect_success",
                            "platform": "facebook",
                            "social_account_id": (social_account_id),
                            "accounts_connected": (facebook_count),
                            "facebook_connected": (facebook_count),
                            "organization_id": (organization_id),
                        },
                    )

                # ---------------------------------------------
                # NORMAL CONNECT SUCCESS
                # ---------------------------------------------

                return _frontend_redirect(
                    overview_path,
                    {
                        "social_connect": "success",
                        "platform": "meta",
                        "accounts_connected": (facebook_count),
                        "facebook_connected": (facebook_count),
                        "organization_id": (organization_id),
                    },
                )

            # =================================================
            # MULTIPLE FACEBOOK PAGES
            # =================================================

            if result.get("status") == "selection_required":

                # Reconnect must NEVER enter Page selection.
                if action == OAUTH_ACTION_RECONNECT:
                    raise MetaAPIError(
                        "Facebook reconnect could not resolve "
                        "the existing Page directly."
                    )

                session = result.get(
                    "session",
                )

                if not session:
                    raise MetaAPIError(
                        "Meta Page selection session " "was not created.",
                    )

                return _frontend_redirect(
                    overview_path,
                    {
                        "social_connect": "selection",
                        "platform": "meta",
                        "selection_key": str(
                            session.selection_key,
                        ),
                    },
                )

            # =================================================
            # UNEXPECTED RESULT
            # =================================================

            raise MetaAPIError(
                "Unexpected Meta OAuth result.",
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
                    "reason": ("Unable to connect Facebook Page."),
                },
            )


# ============================================================
# FACEBOOK PAGE SELECTION
# ============================================================


class MetaOAuthSelectionAPIView(APIView):
    """
    Return temporary Facebook Page selection data.

    OAuth tokens are never returned to the frontend.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        selection_key = (
            request.query_params.get(
                "selection_key",
            )
            or ""
        ).strip()

        organization_id = (
            request.query_params.get(
                "organization_id",
            )
            or ""
        ).strip()

        # ====================================================
        # VALIDATION
        # ====================================================

        if not selection_key:
            return Response(
                {
                    "success": False,
                    "message": "selection_key is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not organization_id:
            return Response(
                {
                    "success": False,
                    "message": "organization_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # ORGANIZATION
        # ====================================================

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

        # ====================================================
        # SESSION
        # ====================================================

        session = MetaOAuthSession.objects.filter(
            selection_key=selection_key,
        ).first()

        if not session:
            return Response(
                {
                    "success": False,
                    "message": ("Meta authorization session " "was not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ====================================================
        # GET FACEBOOK PAGES
        # ====================================================

        try:
            data = MetaOAuthService().get_selection_data(
                session=session,
                organization=organization,
                user=request.user,
            )

            return Response(
                {
                    "success": True,
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except MetaAPIError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception(
                "Unable to load Meta Page selection.",
            )

            return Response(
                {
                    "success": False,
                    "message": ("Unable to load Facebook Pages."),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# FACEBOOK PAGE SELECTION CONFIRM
# ============================================================


class MetaOAuthSelectionConfirmAPIView(APIView):
    """
    Confirm one Facebook Page selected by the user.

    Frontend sends:

        selection_key
        organization_id
        page_id

    OAuth access tokens remain server-side.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
    ):
        selection_key = str(
            request.data.get(
                "selection_key",
            )
            or "",
        ).strip()

        organization_id = str(
            request.data.get(
                "organization_id",
            )
            or "",
        ).strip()

        page_id = str(
            request.data.get(
                "page_id",
            )
            or "",
        ).strip()

        # ====================================================
        # VALIDATION
        # ====================================================

        if not selection_key:
            return Response(
                {
                    "success": False,
                    "message": "selection_key is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not organization_id:
            return Response(
                {
                    "success": False,
                    "message": "organization_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not page_id:
            return Response(
                {
                    "success": False,
                    "message": "page_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # ORGANIZATION
        # ====================================================

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

        # ====================================================
        # SESSION
        # ====================================================

        session = MetaOAuthSession.objects.filter(
            selection_key=selection_key,
        ).first()

        if not session:
            return Response(
                {
                    "success": False,
                    "message": ("Meta authorization session " "was not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ====================================================
        # CONFIRM FACEBOOK PAGE
        # ====================================================

        try:
            result = MetaOAuthService().confirm_selection(
                session=session,
                organization=organization,
                user=request.user,
                page_id=page_id,
            )

            accounts = result.get("accounts") or []

            facebook_count = sum(
                1
                for account in accounts
                if getattr(
                    account,
                    "platform",
                    None,
                )
                == SocialPlatform.FACEBOOK
            )

            return Response(
                {
                    "success": True,
                    "message": ("Facebook Page connected successfully."),
                    "data": {
                        "accounts_connected": (facebook_count),
                        "facebook_connected": (facebook_count),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except MetaAPIError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception(
                "Unable to confirm Meta Page selection.",
            )

            return Response(
                {
                    "success": False,
                    "message": ("Unable to connect the selected " "Facebook Page."),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
