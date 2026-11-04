import logging
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.shortcuts import redirect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.responses import success_response
from apps.social_accounts.invitations import (
    InvalidInvitation,
    consume_invitation_oauth_attempt,
)

from .exceptions import InstagramIntegrationError
from .invitation_oauth import InvitationInstagramOAuthService

logger = logging.getLogger(__name__)


class InvitationInstagramStartSerializer(serializers.Serializer):
    acceptance_token = serializers.CharField(
        min_length=32,
        max_length=200,
        trim_whitespace=True,
        required=False,
    )
    resumption_token = serializers.CharField(
        min_length=32,
        max_length=4096,
        trim_whitespace=True,
        required=False,
    )

    def validate(self, attrs):
        if bool(attrs.get("acceptance_token")) == bool(attrs.get("resumption_token")):
            raise serializers.ValidationError("Provide one invitation session credential.")
        return attrs


class InvitationInstagramSelectionSerializer(serializers.Serializer):
    acceptance_token = serializers.CharField(
        min_length=32,
        max_length=200,
        trim_whitespace=True,
        required=False,
    )
    resumption_token = serializers.CharField(
        min_length=32,
        max_length=4096,
        trim_whitespace=True,
        required=False,
    )
    selection_key = serializers.UUIDField()

    def validate(self, attrs):
        if bool(attrs.get("acceptance_token")) == bool(attrs.get("resumption_token")):
            raise serializers.ValidationError("Provide one invitation session credential.")
        return attrs


def _invitation_redirect(**params):
    base_url = str(getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    url = f"{base_url}/social-invitations/accept"
    if params:
        url = f"{url}?{urlencode(params)}"
    return redirect(url)


class InvitationInstagramOAuthStartAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationInstagramStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            service = InvitationInstagramOAuthService()
            resumption_token = serializer.validated_data.get("resumption_token")
            if resumption_token:
                started = service.start_from_resumption(resumption_token)
                context = started["context"]
                data = {
                    "authorization_url": started["authorization_url"],
                    "invitation": {
                        "organization_name": context["organization_name"],
                        "platforms": context["allowed_platforms"],
                        "selected_platforms": context["selected_platforms"],
                        "connected_platforms": context["connected_platforms"],
                        "expires_at": context["expires_at"],
                    },
                }
            else:
                authorization_url = service.start(
                    serializer.validated_data["acceptance_token"]
                )
                data = {"authorization_url": authorization_url}
        except InvalidInvitation:
            return Response(
                {"detail": "This invitation session is invalid or unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InstagramIntegrationError:
            return Response(
                {"detail": "Instagram authorization is unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return success_response(
            data,
            message="Instagram authorization started.",
        )


class InvitationInstagramOAuthCallbackAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        state = (request.query_params.get("state") or "").strip()
        if not state:
            return _invitation_redirect(instagram_invitation_oauth="error")
        try:
            callback_context = consume_invitation_oauth_attempt(
                state,
                expected_platform="instagram",
            )
        except InvalidInvitation:
            logger.warning("Rejected invalid Instagram invitation OAuth state.")
            return _invitation_redirect(instagram_invitation_oauth="error")

        if request.query_params.get("error"):
            return _invitation_redirect(instagram_invitation_oauth="cancelled")
        code = (request.query_params.get("code") or "").strip()
        if not code:
            return _invitation_redirect(instagram_invitation_oauth="error")

        correlation_id = uuid4().hex
        try:
            session = InvitationInstagramOAuthService().stage_callback(
                callback_context,
                code,
            )
        except InvalidInvitation:
            return _invitation_redirect(instagram_invitation_oauth="error")
        except InstagramIntegrationError:
            logger.warning(
                "Instagram invitation OAuth failed correlation_id=%s.",
                correlation_id,
            )
            return _invitation_redirect(instagram_invitation_oauth="error")
        except Exception:
            logger.warning(
                "Unexpected Instagram invitation OAuth failure correlation_id=%s.",
                correlation_id,
            )
            return _invitation_redirect(instagram_invitation_oauth="error")

        return _invitation_redirect(
            instagram_invitation_oauth="preview",
            selection_key=str(session.selection_key),
        )


class InvitationInstagramPreviewAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationInstagramSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = InvitationInstagramOAuthService().get_staging_data(
                selection_key=serializer.validated_data["selection_key"],
                acceptance_token=serializer.validated_data.get("acceptance_token"),
                resumption_token=serializer.validated_data.get("resumption_token"),
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This Instagram preview is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InstagramIntegrationError:
            return Response(
                {"detail": "Unable to load the Instagram preview."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(data)


class InvitationInstagramConfirmAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationInstagramSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = InvitationInstagramOAuthService().confirm(
                selection_key=serializer.validated_data["selection_key"],
                acceptance_token=serializer.validated_data.get("acceptance_token"),
                resumption_token=serializer.validated_data.get("resumption_token"),
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This Instagram preview cannot be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InstagramIntegrationError:
            return Response(
                {"detail": "Unable to connect the selected Instagram account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(result, message="Instagram account connected.")


class InvitationInstagramDeclineAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationInstagramSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = InvitationInstagramOAuthService().decline(
                selection_key=serializer.validated_data["selection_key"],
                acceptance_token=serializer.validated_data.get("acceptance_token"),
                resumption_token=serializer.validated_data.get("resumption_token"),
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This Instagram preview cannot be declined."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(result, message="Instagram authorization declined.")
