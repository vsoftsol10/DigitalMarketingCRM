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

from .client import MetaAPIClient
from .exceptions import MetaAPIError, MetaIntegrationError
from .invitation_oauth import InvitationMetaOAuthService

logger = logging.getLogger(__name__)


class InvitationFacebookOAuthStartSerializer(serializers.Serializer):
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


class InvitationFacebookSelectionSerializer(serializers.Serializer):
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


class InvitationFacebookPageAddSerializer(InvitationFacebookSelectionSerializer):
    page_id = serializers.CharField(max_length=255, trim_whitespace=True)


def _invitation_redirect(**params):
    base_url = str(getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    url = f"{base_url}/social-invitations/accept"
    if params:
        url = f"{url}?{urlencode(params)}"
    return redirect(url)


def _callback_error():
    return _invitation_redirect(meta_oauth="error")


class InvitationFacebookOAuthStartAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationFacebookOAuthStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            service = InvitationMetaOAuthService()
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
                {"detail": "This invitation session is invalid or no longer available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MetaIntegrationError:
            return Response(
                {"detail": "Facebook authorization is unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return success_response(
            data,
            message="Facebook authorization started.",
        )


class InvitationFacebookOAuthCallbackAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        state = (request.query_params.get("state") or "").strip()
        if not state:
            return _callback_error()

        try:
            callback_context = consume_invitation_oauth_attempt(
                state,
                expected_platform="facebook",
            )
        except InvalidInvitation:
            logger.warning("Rejected invalid Facebook invitation OAuth state.")
            return _callback_error()

        # Provider cancellation still consumes this one-time state.
        if request.query_params.get("error"):
            return _invitation_redirect(meta_oauth="cancelled")

        code = (request.query_params.get("code") or "").strip()
        if not code:
            return _callback_error()

        correlation_id = uuid4().hex
        try:
            session = InvitationMetaOAuthService().create_selection_session(
                callback_context,
                code,
            )
        except InvalidInvitation:
            return _callback_error()
        except MetaAPIError as exc:
            details = MetaAPIClient.safe_error_metadata(exc)
            logger.warning(
                "Facebook invitation OAuth failed correlation_id=%s "
                "http_status=%s graph_error_code=%s graph_error_subcode=%s.",
                correlation_id,
                details["http_status"],
                details["graph_error_code"],
                details["graph_error_subcode"],
            )
            return _callback_error()
        except Exception:
            logger.warning(
                "Unexpected Facebook invitation OAuth failure correlation_id=%s.",
                correlation_id,
            )
            return _callback_error()

        return _invitation_redirect(
            meta_oauth="selection",
            selection_key=str(session.selection_key),
        )


class InvitationFacebookPageSelectionAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationFacebookSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = InvitationMetaOAuthService().get_selection_data(
                selection_key=serializer.validated_data["selection_key"],
                acceptance_token=serializer.validated_data.get("acceptance_token"),
                resumption_token=serializer.validated_data.get("resumption_token"),
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This Facebook Page selection is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MetaIntegrationError:
            return Response(
                {"detail": "Unable to load Facebook Pages."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(data)


class InvitationFacebookPageAddAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationFacebookPageAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = InvitationMetaOAuthService().add_page(
                selection_key=serializer.validated_data["selection_key"],
                acceptance_token=serializer.validated_data.get("acceptance_token"),
                resumption_token=serializer.validated_data.get("resumption_token"),
                page_id=serializer.validated_data["page_id"],
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This Facebook Page could not be added from this invitation."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MetaIntegrationError:
            return Response(
                {"detail": "Unable to connect the selected Facebook Page."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(
            result,
            message=(
                "Facebook Page is already connected."
                if result["already_connected"]
                else "Facebook Page connected successfully."
            ),
        )
