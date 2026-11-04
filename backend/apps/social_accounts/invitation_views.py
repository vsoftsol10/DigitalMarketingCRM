from django.utils import timezone
from django.db.models import Exists, OuterRef
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization
from apps.common.responses import success_response

from .invitation_serializers import (
    EmailInvitationCreateSerializer,
    InvitationAcceptanceCancelSerializer,
    InvitationAcceptanceCompleteSerializer,
    InvitationClaimSerializer,
    InvitationOAuthAttemptCreateSerializer,
    InvitationPlatformResumptionSerializer,
    InvitationTokenSerializer,
    ShareInvitationCreateSerializer,
)
from .invitation_delivery import deliver_prepared_invitation_email
from .invitations import (
    InvitationError,
    IncompleteInvitation,
    InvalidInvitation,
    claim_invitation,
    cancel_invitation_acceptance,
    complete_invitation_acceptance,
    complete_invitation_acceptance_for_resumption,
    create_invitation,
    create_invitation_oauth_attempt,
    get_invitation_management_status,
    prepare_email_invitation_delivery,
    revoke_invitation,
    resume_invitation_platform,
    resend_email_invitation_delivery,
    retry_email_invitation_delivery,
    validate_invitation,
)
from .models import (
    SocialAccountInvitation,
    SocialAccountInvitationAcceptance,
    SocialAccountInvitationAcceptanceStatus,
    SocialAccountInvitationDeliveryStatus,
    SocialAccountInvitationMode,
)


def _delivery_attempt_status(invitation):
    if invitation.pending_token_hash:
        return "failed" if invitation.delivery_error_code else "pending"
    return invitation.delivery_status


def _delivery_result(invitation, outcome):
    invitation.refresh_from_db()
    data = {
        "id": str(invitation.id),
        "status": get_invitation_management_status(invitation),
        "delivery_status": invitation.delivery_status,
        "delivery_attempt_status": _delivery_attempt_status(invitation),
        "delivery_error_code": invitation.delivery_error_code,
        "expires_at": invitation.expires_at,
        "retry_available": bool(
            invitation.pending_token_hash
            and (
                invitation.delivery_error_code
                or invitation.pending_delivery_token_encrypted
            )
        ),
        "resend_available": (
            invitation.delivery_status == SocialAccountInvitationDeliveryStatus.SENT
            and not invitation.pending_token_hash
            and invitation.status == "pending"
        ),
    }
    if outcome == "sent":
        return success_response(data, message="Invitation email sent.")
    if outcome == "failed":
        return Response(
            {
                "success": False,
                "code": "email_delivery_failed",
                "message": "The invitation email could not be sent. You can retry this delivery.",
                "data": data,
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )
    if outcome == "pending":
        data["retry_available"] = bool(invitation.pending_delivery_token_encrypted)
        return Response(
            {
                "success": False,
                "code": "delivery_confirmation_pending",
                "message": "The email provider response could not be confirmed. The attempt remains pending to protect any delivered link.",
                "data": data,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    if outcome == "expired":
        return Response(
            {
                "success": False,
                "code": "invitation_expired",
                "message": "The invitation expired before delivery could be confirmed.",
                "data": data,
            },
            status=status.HTTP_409_CONFLICT,
        )
    return Response(
        {
            "success": False,
            "code": "delivery_attempt_stale",
            "message": "This delivery attempt is no longer current. Refresh invitation status before retrying.",
            "data": data,
        },
        status=status.HTTP_409_CONFLICT,
    )


def _send_prepared_invitation_email(invitation, attempt):
    outcome = deliver_prepared_invitation_email(invitation, attempt)
    return _delivery_result(invitation, outcome)


class OrganizationInvitationMixin:
    permission_classes = [IsAuthenticated]

    def get_organization(self, organization_id):
        organization = Organization.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).first()
        if organization is None:
            return None
        # Existing explicit Instagram OAuth authorization rule. This feature
        # does not broaden or change authorization elsewhere in the CRM.
        if organization.created_by_id != self.request.user.id:
            return None
        return organization


def _get_managed_invitation(view, organization_id, invitation_id):
    organization = view.get_organization(organization_id)
    if organization is None:
        return None
    return SocialAccountInvitation.objects.filter(
        pk=invitation_id,
        organization=organization,
        is_deleted=False,
    ).first()


class OrganizationEmailInvitationCreateAPIView(OrganizationInvitationMixin, APIView):
    def post(self, request, organization_id):
        organization = self.get_organization(organization_id)
        if organization is None:
            return Response({"detail": "Organization not found or access denied."}, status=404)
        serializer = EmailInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = create_invitation(
                organization=organization,
                inviter=request.user,
                mode=SocialAccountInvitationMode.EMAIL,
                platforms=serializer.validated_data["platforms"],
                recipient_email=serializer.validated_data["email"],
            )
        except InvitationError as exc:
            return Response({"detail": str(exc)}, status=400)
        invitation = result["invitation"]
        return success_response({
            "id": str(invitation.id),
            "mode": invitation.mode,
            "status": invitation.status,
            "delivery_status": invitation.delivery_status,
            "platforms": invitation.allowed_platforms,
            "expires_at": invitation.expires_at,
        }, message="Email invitation created.", status_code=status.HTTP_201_CREATED)


class OrganizationShareInvitationCreateAPIView(OrganizationInvitationMixin, APIView):
    def post(self, request, organization_id):
        organization = self.get_organization(organization_id)
        if organization is None:
            return Response({"detail": "Organization not found or access denied."}, status=404)
        serializer = ShareInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = create_invitation(
                organization=organization,
                inviter=request.user,
                mode=SocialAccountInvitationMode.SHARE_LINK,
                platforms=serializer.validated_data["platforms"],
                usage_limit=serializer.validated_data["usage_limit"],
            )
        except InvitationError as exc:
            return Response({"detail": str(exc)}, status=400)
        invitation = result["invitation"]
        return success_response({
            "id": str(invitation.id),
            "mode": invitation.mode,
            "status": invitation.status,
            "platforms": invitation.allowed_platforms,
            "expires_at": invitation.expires_at,
            "usage_limit": invitation.usage_limit,
            "usage_count": invitation.usage_count,
            "bearer_link": True,
            "share_url": result["share_url"],
        }, message="Share link created.", status_code=status.HTTP_201_CREATED)


class OrganizationInvitationListAPIView(OrganizationInvitationMixin, APIView):
    def get(self, request, organization_id):
        organization = self.get_organization(organization_id)
        if organization is None:
            return Response({"detail": "Organization not found or access denied."}, status=404)
        completed_acceptance = SocialAccountInvitationAcceptance.objects.filter(
            invitation_id=OuterRef("pk"),
            is_deleted=False,
            status=SocialAccountInvitationAcceptanceStatus.COMPLETED,
        )
        rows = SocialAccountInvitation.objects.filter(
            organization=organization, is_deleted=False
        ).annotate(
            has_completed_acceptance=Exists(completed_acceptance),
        ).order_by("-created_at")
        now = timezone.now()
        data = [{
            "id": str(row.id),
            "mode": row.mode,
            "recipient_email": row.recipient_email if row.mode == "email" else None,
            "platforms": row.allowed_platforms,
            "status": get_invitation_management_status(row, now),
            # Share links remain reusable while capacity is available, so the
            # invitation status can stay pending after a successful use. Keep
            # that lifecycle unchanged and expose the authoritative acceptance
            # completion separately for management UIs.
            "has_completed_acceptance": row.has_completed_acceptance,
            "delivery_status": row.delivery_status,
            "delivery_attempt_status": _delivery_attempt_status(row),
            "delivery_error_code": row.delivery_error_code,
            "expires_at": row.expires_at,
            "usage_limit": row.usage_limit,
            "usage_count": row.usage_count,
            "created_at": row.created_at,
            "send_available": (
                row.mode == SocialAccountInvitationMode.EMAIL
                and row.delivery_status == SocialAccountInvitationDeliveryStatus.PENDING_CONFIGURATION
                and row.status == "pending"
                and row.expires_at > now
            ),
            "retry_available": bool(
                row.pending_token_hash
                and (
                    row.delivery_error_code
                    or row.pending_delivery_token_encrypted
                )
            ),
            "resend_available": (
                row.mode == SocialAccountInvitationMode.EMAIL
                and row.delivery_status == SocialAccountInvitationDeliveryStatus.SENT
                and not row.pending_token_hash
                and row.status == "pending"
            ),
            "revoke_available": row.status == "pending" and row.expires_at > now,
        } for row in rows]
        return success_response(data)


class OrganizationInvitationEmailSendAPIView(OrganizationInvitationMixin, APIView):
    def post(self, request, organization_id, invitation_id):
        invitation = _get_managed_invitation(self, organization_id, invitation_id)
        if invitation is None:
            return Response({"detail": "Invitation not found or access denied."}, status=404)
        if invitation.mode != SocialAccountInvitationMode.EMAIL or invitation.delivery_status != SocialAccountInvitationDeliveryStatus.PENDING_CONFIGURATION:
            return Response({"detail": "This invitation is not awaiting its initial email delivery."}, status=409)
        try:
            attempt = prepare_email_invitation_delivery(invitation)
        except InvitationError:
            return Response({"detail": "This invitation cannot be sent in its current state."}, status=409)
        return _send_prepared_invitation_email(invitation, attempt)


class OrganizationInvitationEmailRetryAPIView(OrganizationInvitationMixin, APIView):
    def post(self, request, organization_id, invitation_id):
        invitation = _get_managed_invitation(self, organization_id, invitation_id)
        if invitation is None:
            return Response({"detail": "Invitation not found or access denied."}, status=404)
        try:
            attempt = retry_email_invitation_delivery(
                invitation,
                invitation.delivery_attempts,
            )
        except InvitationError:
            return Response({"detail": "This invitation delivery cannot be retried yet."}, status=409)
        return _send_prepared_invitation_email(invitation, attempt)


class OrganizationInvitationEmailResendAPIView(OrganizationInvitationMixin, APIView):
    def post(self, request, organization_id, invitation_id):
        invitation = _get_managed_invitation(self, organization_id, invitation_id)
        if invitation is None:
            return Response({"detail": "Invitation not found or access denied."}, status=404)
        try:
            attempt = resend_email_invitation_delivery(invitation)
        except InvitationError:
            return Response({"detail": "This invitation cannot be resent in its current state."}, status=409)
        return _send_prepared_invitation_email(invitation, attempt)


class OrganizationInvitationRevokeAPIView(OrganizationInvitationMixin, APIView):
    def post(self, request, organization_id, invitation_id):
        organization = self.get_organization(organization_id)
        if organization is None:
            return Response({"detail": "Organization not found or access denied."}, status=404)
        invitation = SocialAccountInvitation.objects.filter(
            pk=invitation_id, organization=organization, is_deleted=False
        ).first()
        if invitation is None:
            return Response({"detail": "Invitation not found."}, status=404)
        revoke_invitation(invitation)
        return success_response({"id": str(invitation.id), "status": invitation.status})


class PublicInvitationValidateAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(validate_invitation(serializer.validated_data["token"]))


class PublicInvitationClaimAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            acceptance, raw_token = claim_invitation(
                serializer.validated_data["token"],
                serializer.validated_data.get("platforms"),
            )
        except InvalidInvitation:
            return Response({"detail": "This invitation is invalid or no longer available."}, status=400)
        return success_response({
            "acceptance_token": raw_token,
            "platforms": acceptance.selected_platforms,
            "expires_at": acceptance.expires_at,
        }, message="Invitation session created.", status_code=status.HTTP_201_CREATED)


class PublicInvitationAcceptanceCancelAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationAcceptanceCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            acceptance = cancel_invitation_acceptance(
                serializer.validated_data["acceptance_token"]
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This invitation session cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response({"status": acceptance.status})


class PublicInvitationAcceptanceCompleteAPIView(APIView):
    """Complete via acceptance_token; returns completed, incomplete, or unavailable status.

    HTTP 200 means completion was recorded, 409 means selected platforms still
    lack valid persisted account associations, and 400 means the acceptance or
    invitation is no longer usable.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationAcceptanceCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            if serializer.validated_data.get("resumption_token"):
                invitation = complete_invitation_acceptance_for_resumption(
                    serializer.validated_data["resumption_token"]
                )
            else:
                invitation = complete_invitation_acceptance(
                    serializer.validated_data["acceptance_token"]
                )
        except IncompleteInvitation as exc:
            return Response(
                {
                    "success": False,
                    "code": "incomplete_accounts",
                    "message": str(exc),
                    "data": {"status": "incomplete"},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except InvalidInvitation as exc:
            return Response(
                {
                    "success": False,
                    "code": "invalid_invitation",
                    "message": str(exc),
                    "data": {"status": "unavailable"},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(
            {
                "status": "completed",
                "invitation_status": invitation.status,
                "usage_count": invitation.usage_count,
            },
            message="Invitation completed.",
        )


class PublicInvitationOAuthAttemptCreateAPIView(APIView):
    """Start an anonymous, invitation-bound provider OAuth attempt."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationOAuthAttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            attempt, state = create_invitation_oauth_attempt(
                serializer.validated_data["acceptance_token"],
                serializer.validated_data["platform"],
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This invitation session is invalid or no longer available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(
            {
                "attempt_id": str(attempt.id),
                "platform": attempt.platform,
                "state": state,
                "expires_at": attempt.expires_at,
            },
            message="Invitation OAuth attempt created.",
            status_code=status.HTTP_201_CREATED,
        )


class PublicInvitationPlatformResumeAPIView(APIView):
    """Validate an email CTA and resume its invitation-bound acceptance."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationPlatformResumptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            context = resume_invitation_platform(
                serializer.validated_data["resumption_token"],
                expected_platform=serializer.validated_data["platform"],
            )
        except InvalidInvitation:
            return Response(
                {"detail": "This platform invitation link is invalid or no longer available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response({
            "organization_name": context["organization_name"],
            "platforms": context["allowed_platforms"],
            "selected_platforms": context["selected_platforms"],
            "connected_platforms": context["connected_platforms"],
            "expires_at": context["expires_at"],
            "platform": serializer.validated_data["platform"],
        }, message="Invitation session restored.")
