"""Invitation email delivery adapter using the shared Brevo sender."""

from django.utils import timezone

from apps.notifications.services import BrevoEmailError, send_brevo_email

from .invitations import (
    mark_email_invitation_failed,
    mark_email_invitation_sent,
    platform_resumption_url,
)

INVITATION_EMAIL_EVENT = "SOCIAL_ACCOUNT_INVITATION"


def deliver_prepared_invitation_email(invitation, attempt):
    """Send one prepared attempt and record only definitive outcomes.

    A transport error or malformed success response may mean Brevo accepted
    the email but the application lost its response. Such attempts remain
    pending so no retry can supersede a link that may already be in a mailbox.
    There is no provider reconciliation webhook in the current integration.
    """
    platforms = set(invitation.allowed_platforms)
    facebook_enabled = "facebook" in platforms
    instagram_enabled = "instagram" in platforms
    expires_at = timezone.localtime(invitation.expires_at).strftime(
        "%B %d, %Y at %I:%M %p %Z"
    )
    params = {
        "OrganizationName": invitation.organization.name,
        "RecipientEmail": attempt["recipient_email"],
        # Retain the original single-link parameter for existing Brevo
        # templates while the external template is updated.
        "InvitationUrl": attempt["invitation_url"],
        "Platforms": ", ".join(platform.title() for platform in invitation.allowed_platforms),
        "ExpiresAt": expires_at,
        "InvitationExpiry": expires_at,
        "FacebookEnabled": facebook_enabled,
        "InstagramEnabled": instagram_enabled,
        "FacebookInvitationUrl": (
            platform_resumption_url(invitation, attempt["token"], "facebook")
            if facebook_enabled else ""
        ),
        "InstagramInvitationUrl": (
            platform_resumption_url(invitation, attempt["token"], "instagram")
            if instagram_enabled else ""
        ),
        "ExpiryHours": str(
            max(
                1,
                int((invitation.expires_at - timezone.now()).total_seconds() + 3599)
                // 3600,
            )
        ),
    }

    try:
        response = send_brevo_email(
            event_type=INVITATION_EMAIL_EVENT,
            recipient_email=attempt["recipient_email"],
            recipient_name=attempt["recipient_email"],
            params=params,
        )
    except BrevoEmailError as exc:
        if not exc.definitive:
            return "pending"
        mark_email_invitation_failed(
            invitation,
            attempt["attempt_id"],
            exc.error_code,
        )
        return "failed"
    except Exception:
        # Unknown failures are ambiguous; do not release the attempt for a
        # retry that would rotate a possibly delivered link.
        return "pending"

    if not isinstance(response, dict):
        return "pending"

    message_id = response.get("messageId", "")
    if not isinstance(message_id, str):
        return "pending"

    promoted = mark_email_invitation_sent(
        invitation,
        attempt["attempt_id"],
        provider_message_id=message_id,
    )
    if not promoted:
        return "stale"

    invitation.refresh_from_db()
    if invitation.status == "expired":
        return "expired"
    return "sent"
