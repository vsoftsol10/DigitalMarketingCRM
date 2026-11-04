"""Services for bearer-token social-account invitations.

Raw tokens are never logged or stored as plaintext. A temporary delivery token
is encrypted only while its email delivery attempt is unresolved. Share links
are transferable bearer capabilities.
"""

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import quote, urlencode

from django.conf import settings
from django.core import signing
from django.db import models, transaction
from django.utils import timezone

from .models import (
    SocialAccountInvitation,
    SocialAccountInvitationAcceptance,
    SocialAccountInvitationAcceptanceStatus as AcceptanceStatus,
    SocialAccountInvitationDeliveryStatus as DeliveryStatus,
    SocialAccountInvitationMode as InvitationMode,
    SocialAccountInvitationOAuthAttempt,
    SocialAccountInvitationOAuthPlatform as InvitationOAuthPlatform,
    SocialAccountInvitationStatus as InvitationStatus,
    SocialAccount,
    SocialAccountInvitationAcceptanceAccount,
    SocialAccountStatus,
    SocialPlatform,
)
from .invitation_crypto import (
    create_platform_resumption_token,
    decrypt_invitation_token,
    encrypt_invitation_token,
    read_platform_resumption_token,
)


class InvitationError(Exception):
    """A safe, expected invitation lifecycle error."""


class InvalidInvitation(InvitationError):
    pass


class IncompleteInvitation(InvitationError):
    """The acceptance is valid, but required accounts are not connected yet."""


INVITATION_OAUTH_ATTEMPT_TTL = timedelta(minutes=10)
INVITATION_EXPIRY = timedelta(hours=72)


def _new_token():
    return secrets.token_urlsafe(32)


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _clear_invitation_oauth_secrets(acceptance_ids):
    acceptance_ids = tuple(acceptance_ids)
    if not acceptance_ids:
        return

    # Import lazily to avoid coupling app initialization to provider apps.
    from apps.integrations.meta.models import InvitationMetaOAuthSession
    from apps.integrations.instagram.models import (
        InvitationInstagramOAuthSession,
        InvitationInstagramOAuthStatus,
    )

    now = timezone.now()
    InvitationMetaOAuthSession.objects.filter(
        acceptance_id__in=acceptance_ids,
        is_deleted=False,
    ).update(
        encrypted_access_token="",
        encrypted_accounts="",
        updated_at=now,
    )
    InvitationInstagramOAuthSession.objects.filter(
        acceptance_id__in=acceptance_ids,
        status=InvitationInstagramOAuthStatus.STAGED,
        is_deleted=False,
    ).update(
        status=InvitationInstagramOAuthStatus.INVALIDATED,
        encrypted_access_token="",
        invalidated_at=now,
        updated_at=now,
    )


def _invalidate_acceptances_after_email_resend(invitation, now):
    """Invalidate live claims only once the replacement link was delivered."""
    acceptances = list(
        SocialAccountInvitationAcceptance.objects.select_for_update().filter(
            invitation=invitation,
            is_deleted=False,
            status=AcceptanceStatus.ACTIVE,
        ).order_by("pk")
    )
    if not acceptances:
        return 0

    acceptance_ids = []
    for acceptance in acceptances:
        acceptance_ids.append(acceptance.pk)
        if acceptance.expires_at <= now:
            acceptance.status = AcceptanceStatus.EXPIRED
            acceptance.save(update_fields=["status", "updated_at"])
        else:
            acceptance.status = AcceptanceStatus.CANCELLED
            acceptance.cancelled_at = now
            acceptance.save(update_fields=["status", "cancelled_at", "updated_at"])

    # Acceptance status already makes old OAuth states unusable; expiring the
    # outstanding attempts as well records that invalidation explicitly.
    SocialAccountInvitationOAuthAttempt.objects.filter(
        acceptance_id__in=acceptance_ids,
        is_deleted=False,
        expires_at__gt=now,
    ).update(expires_at=now, updated_at=now)
    _clear_invitation_oauth_secrets(acceptance_ids)
    return len(acceptance_ids)


def cleanup_expired_invitation_oauth_secrets(*, batch_size=200):
    """Clear secrets from one bounded batch of expired or unusable staging rows."""
    from django.db.models import Q

    from apps.integrations.meta.models import InvitationMetaOAuthSession
    from apps.integrations.instagram.models import (
        InvitationInstagramOAuthSession,
        InvitationInstagramOAuthStatus,
    )

    batch_size = max(1, min(int(batch_size), 500))
    now = timezone.now()
    unusable = (
        Q(acceptance__is_deleted=True)
        | Q(acceptance__status__in=(AcceptanceStatus.COMPLETED, AcceptanceStatus.EXPIRED, AcceptanceStatus.CANCELLED))
        | Q(acceptance__invitation__is_deleted=True)
        | Q(acceptance__invitation__status__in=(InvitationStatus.ACCEPTED, InvitationStatus.EXPIRED, InvitationStatus.REVOKED, InvitationStatus.EXHAUSTED))
        | Q(oauth_attempt__is_deleted=True)
        | Q(oauth_attempt__consumed_at__isnull=True)
    )
    expired = (
        Q(expires_at__lte=now)
        | Q(token_expires_at__lte=now)
        | Q(acceptance__expires_at__lte=now)
        | Q(acceptance__invitation__expires_at__lte=now)
        | Q(oauth_attempt__expires_at__lte=now)
    )

    # IDs are selected in deterministic, bounded batches. Conditional updates
    # make retries safe and avoid overwriting a session that has transitioned.
    meta_ids = list(
        InvitationMetaOAuthSession.objects.filter(
            is_deleted=False,
        ).filter(expired | unusable).filter(
            Q(encrypted_access_token__gt="") | Q(encrypted_accounts__gt=""),
        ).order_by("pk").values_list("pk", flat=True)[:batch_size]
    )
    meta_cleared = InvitationMetaOAuthSession.objects.filter(
        pk__in=meta_ids,
        is_deleted=False,
    ).update(
        encrypted_access_token="",
        encrypted_accounts="",
        updated_at=now,
    ) if meta_ids else 0

    expired_ig_ids = list(
        InvitationInstagramOAuthSession.objects.filter(
            is_deleted=False,
            status=InvitationInstagramOAuthStatus.STAGED,
            encrypted_access_token__gt="",
        ).filter(expired).order_by("pk").values_list("pk", flat=True)[:batch_size]
    )
    expired_ig_cleared = InvitationInstagramOAuthSession.objects.filter(
        pk__in=expired_ig_ids,
        is_deleted=False,
        status=InvitationInstagramOAuthStatus.STAGED,
    ).update(
        status=InvitationInstagramOAuthStatus.EXPIRED,
        encrypted_access_token="",
        invalidated_at=now,
        updated_at=now,
    ) if expired_ig_ids else 0

    invalid_ig_ids = list(
        InvitationInstagramOAuthSession.objects.filter(
            is_deleted=False,
            status=InvitationInstagramOAuthStatus.STAGED,
            encrypted_access_token__gt="",
        ).filter(unusable).order_by("pk").values_list("pk", flat=True)[:batch_size]
    )
    invalid_ig_cleared = InvitationInstagramOAuthSession.objects.filter(
        pk__in=invalid_ig_ids,
        is_deleted=False,
        status=InvitationInstagramOAuthStatus.STAGED,
    ).update(
        status=InvitationInstagramOAuthStatus.INVALIDATED,
        encrypted_access_token="",
        invalidated_at=now,
        updated_at=now,
    ) if invalid_ig_ids else 0

    expired_invitation_ids = list(
        SocialAccountInvitation.objects.filter(
            pending_delivery_token_encrypted__gt="",
        ).filter(
            Q(is_deleted=True)
            | Q(status__in=(
                InvitationStatus.ACCEPTED,
                InvitationStatus.EXPIRED,
                InvitationStatus.REVOKED,
                InvitationStatus.EXHAUSTED,
            ))
            | Q(expires_at__lte=now)
        ).order_by("pk").values_list("pk", flat=True)[:batch_size]
    )
    invitation_tokens_cleared = SocialAccountInvitation.objects.filter(
        pk__in=expired_invitation_ids,
        pending_delivery_token_encrypted__gt="",
    ).update(
        pending_token_hash="",
        pending_delivery_token_encrypted="",
        updated_at=now,
    ) if expired_invitation_ids else 0

    return {
        "meta_sessions_cleared": meta_cleared,
        "instagram_sessions_expired": expired_ig_cleared,
        "instagram_sessions_invalidated": invalid_ig_cleared,
        "invitation_delivery_tokens_cleared": invitation_tokens_cleared,
    }


def _frontend_url(token):
    base_url = getattr(settings, "FRONTEND_URL", "").strip().rstrip("/")
    if not base_url:
        raise InvitationError("Invitation link configuration is unavailable.")
    # The fragment keeps bearer credentials out of HTTP request and referrer logs.
    return f"{base_url}/social-invitations/accept#{quote(token)}"


def platform_resumption_url(invitation, invitation_token, platform):
    """Build a platform-targeted email URL without placing secrets in queries.

    The signed continuation token is stored only in the URL fragment. Its
    authority is still bounded by the invitation's current token hash and
    lifecycle state when the backend validates it.
    """
    platform = str(platform or "").strip().lower()
    if platform not in invitation.allowed_platforms:
        raise InvitationError("The platform is not allowed by this invitation.")
    token_hash = _token_hash(invitation_token)
    resumption_token = create_platform_resumption_token(
        invitation_id=invitation.pk,
        token_hash=token_hash,
        platform=platform,
    )
    base_url = getattr(settings, "FRONTEND_URL", "").strip().rstrip("/")
    if not base_url:
        raise InvitationError("Invitation link configuration is unavailable.")
    query = urlencode({"connect": platform})
    fragment = quote(f"resume={resumption_token}", safe="=")
    return f"{base_url}/social-invitations/accept?{query}#{fragment}"


def create_invitation(*, organization, inviter, platforms, mode, expires_in_days=None,
                      recipient_email="", usage_limit=1):
    platforms = sorted(set(platforms))
    allowed = {SocialPlatform.FACEBOOK, SocialPlatform.INSTAGRAM}
    if not platforms or not set(platforms).issubset(allowed):
        raise InvitationError("Select Facebook, Instagram, or both.")
    if mode not in InvitationMode.values:
        raise InvitationError("Unsupported invitation mode.")
    if mode == InvitationMode.EMAIL:
        recipient_email = recipient_email.strip().casefold()
        if not recipient_email:
            raise InvitationError("An email address is required.")
        usage_limit = 1
        delivery_status = DeliveryStatus.PENDING_CONFIGURATION
    else:
        recipient_email = ""
        delivery_status = DeliveryStatus.NOT_REQUIRED

    token = _new_token()
    share_url = _frontend_url(token) if mode == InvitationMode.SHARE_LINK else None
    invitation = SocialAccountInvitation.objects.create(
        organization=organization,
        inviter=inviter,
        mode=mode,
        recipient_email=recipient_email,
        token_hash=_token_hash(token),
        allowed_platforms=platforms,
        # Invitation duration is a backend policy, shared by email and links.
        # Keep the legacy argument accepted for internal callers, but do not
        # allow API input or an older caller to extend the 72-hour lifetime.
        expires_at=timezone.now() + INVITATION_EXPIRY,
        usage_limit=usage_limit,
        delivery_status=delivery_status,
    )
    result = {"invitation": invitation}
    if mode == InvitationMode.SHARE_LINK:
        result["share_url"] = share_url
    # The initial raw email token is discarded. Email delivery starts through
    # the authenticated send endpoint, which stages a separate encrypted token.
    return result


def _prepare_email_invitation_delivery(
    invitation,
    *,
    allow_resend=False,
    retry_attempt_id=None,
):
    if invitation.mode != InvitationMode.EMAIL or not _usable_for_delivery(invitation):
        raise InvitationError("This email invitation cannot be delivered.")
    if invitation.pending_token_hash and invitation.delivery_attempts != retry_attempt_id:
        can_supersede_failed_resend = (
            allow_resend
            and invitation.delivery_status == DeliveryStatus.SENT
            and bool(invitation.delivery_error_code)
        )
        can_retry_failed_initial = (
            retry_attempt_id is None
            and invitation.delivery_status == DeliveryStatus.FAILED
        )
        if not (can_supersede_failed_resend or can_retry_failed_initial):
            raise InvitationError("An email delivery attempt is already in progress.")
    if invitation.delivery_status == DeliveryStatus.PENDING and invitation.delivery_attempts != retry_attempt_id:
        raise InvitationError("An email delivery attempt is already in progress.")
    if invitation.delivery_status == DeliveryStatus.SENT and not allow_resend:
        raise InvitationError("Use the explicit resend operation to invalidate a sent link.")
    if invitation.delivery_status not in {
        DeliveryStatus.PENDING_CONFIGURATION,
        DeliveryStatus.FAILED,
        DeliveryStatus.SENT,
        DeliveryStatus.PENDING,
    }:
        raise InvitationError("This email invitation cannot be delivered.")

    token = _new_token()
    invitation.pending_token_hash = _token_hash(token)
    try:
        invitation.pending_delivery_token_encrypted = encrypt_invitation_token(token)
    except Exception as exc:
        raise InvitationError(
            "Email delivery token encryption is unavailable."
        ) from exc
    if invitation.delivery_status != DeliveryStatus.SENT:
        invitation.delivery_status = DeliveryStatus.PENDING
    invitation.delivery_attempts += 1
    invitation.delivery_error_code = ""
    invitation.save(update_fields=[
        "pending_token_hash", "pending_delivery_token_encrypted",
        "delivery_status", "delivery_attempts",
        "delivery_error_code", "updated_at",
    ])
    return {
        "recipient_email": invitation.recipient_email,
        "token": token,
        "invitation_url": _frontend_url(token),
        "attempt_id": invitation.delivery_attempts,
    }


@transaction.atomic
def prepare_email_invitation_delivery(invitation):
    """Start one delivery attempt; repeated preparation cannot rotate its token."""
    invitation = SocialAccountInvitation.objects.select_for_update().get(pk=invitation.pk)
    return _prepare_email_invitation_delivery(invitation)


@transaction.atomic
def resend_email_invitation_delivery(invitation):
    """Prepare a replacement link while the previously sent link stays active."""
    invitation = SocialAccountInvitation.objects.select_for_update().get(pk=invitation.pk)
    if invitation.delivery_status != DeliveryStatus.SENT:
        raise InvitationError("Only a sent email invitation can be resent.")
    return _prepare_email_invitation_delivery(invitation, allow_resend=True)


@transaction.atomic
def retry_email_invitation_delivery(invitation, failed_attempt_id):
    """Recover an ambiguous attempt with its same token or retry a failed send."""
    invitation = SocialAccountInvitation.objects.select_for_update().get(pk=invitation.pk)
    if not _usable_for_delivery(invitation):
        raise InvitationError("This email invitation cannot be retried.")
    if invitation.delivery_attempts != failed_attempt_id:
        raise InvitationError("Only the current email delivery attempt can be retried.")
    if (
        invitation.pending_token_hash
        and invitation.delivery_status in {DeliveryStatus.PENDING, DeliveryStatus.SENT}
        and not invitation.delivery_error_code
    ):
        # Reuse the exact staged token for an ambiguous outcome. Multiple
        # emails may be sent, but each contains the same link and cannot make
        # an older token supersede a newer one.
        try:
            token = decrypt_invitation_token(
                invitation.pending_delivery_token_encrypted
            )
        except Exception as exc:
            raise InvitationError(
                "The current delivery attempt cannot be safely recovered."
            ) from exc
        return {
            "recipient_email": invitation.recipient_email,
            "token": token,
            "invitation_url": _frontend_url(token),
            "attempt_id": invitation.delivery_attempts,
        }
    resend_attempt = invitation.delivery_status == DeliveryStatus.SENT
    if invitation.delivery_status == DeliveryStatus.PENDING:
        # A missing response does not prove the provider rejected the message.
        # Keep this attempt and token available for a delayed success callback.
        retryable = False
    elif invitation.delivery_status == DeliveryStatus.FAILED:
        retryable = True
    elif invitation.delivery_status == DeliveryStatus.SENT:
        # A sent invitation can have a pending replacement while the provider
        # call is still in flight. Only supersede that resend after its failure
        # callback has marked the attempt retryable.
        retryable = bool(
            invitation.pending_token_hash and invitation.delivery_error_code
        )
    else:
        retryable = False
    if not retryable:
        raise InvitationError("Only the current failed email attempt can be retried.")
    return _prepare_email_invitation_delivery(
        invitation,
        allow_resend=resend_attempt,
        retry_attempt_id=failed_attempt_id,
    )


@transaction.atomic
def mark_email_invitation_sent(invitation, attempt_id, provider_message_id=""):
    if not isinstance(provider_message_id, str):
        raise InvitationError("The email provider message ID must be a string.")
    message_id_limit = SocialAccountInvitation._meta.get_field(
        "provider_message_id"
    ).max_length
    if "\x00" in provider_message_id or len(provider_message_id) > message_id_limit:
        raise InvitationError("The email provider message ID is invalid or too long.")

    invitation = SocialAccountInvitation.objects.select_for_update().get(pk=invitation.pk)
    current_attempt = (
        invitation.mode != InvitationMode.EMAIL
        or invitation.status != InvitationStatus.PENDING
        or invitation.delivery_attempts != attempt_id
    )
    if current_attempt:
        return False

    if not invitation.pending_token_hash:
        # Repeated callback for an already promoted attempt is idempotent.
        return (
            invitation.delivery_status == DeliveryStatus.SENT
            and not invitation.delivery_error_code
            and invitation.provider_message_id == provider_message_id
        )
    if invitation.delivery_status not in {
        DeliveryStatus.PENDING,
        DeliveryStatus.SENT,
        DeliveryStatus.FAILED,
    }:
        return False

    if invitation.expires_at <= timezone.now():
        invitation.status = InvitationStatus.EXPIRED
        invitation.delivery_status = DeliveryStatus.FAILED
        invitation.pending_token_hash = ""
        invitation.pending_delivery_token_encrypted = ""
        invitation.delivery_error_code = "invitation_expired"
        invitation.save(update_fields=[
            "status", "delivery_status", "pending_token_hash",
            "pending_delivery_token_encrypted",
            "delivery_error_code", "updated_at"
        ])
        return True
    invitation.token_hash = invitation.pending_token_hash
    invitation.pending_token_hash = ""
    invitation.pending_delivery_token_encrypted = ""
    invitation.delivery_status = DeliveryStatus.SENT
    invitation.provider_message_id = provider_message_id
    invitation.delivery_error_code = ""
    invitation.save(update_fields=[
        "token_hash", "pending_token_hash", "pending_delivery_token_encrypted",
        "delivery_status", "provider_message_id",
        "delivery_error_code", "updated_at"
    ])
    _invalidate_acceptances_after_email_resend(invitation, timezone.now())
    return True


@transaction.atomic
def mark_email_invitation_failed(invitation, attempt_id, error_code):
    invitation = SocialAccountInvitation.objects.select_for_update().get(pk=invitation.pk)
    if (
        invitation.mode != InvitationMode.EMAIL
        or invitation.status != InvitationStatus.PENDING
        or invitation.delivery_attempts != attempt_id
        or not invitation.pending_token_hash
        or invitation.delivery_status not in {
            DeliveryStatus.PENDING,
            DeliveryStatus.SENT,
            DeliveryStatus.FAILED,
        }
    ):
        return False
    if invitation.delivery_status == DeliveryStatus.PENDING:
        invitation.delivery_status = DeliveryStatus.FAILED
    invitation.delivery_error_code = _sanitize_delivery_error_code(error_code)
    invitation.save(update_fields=[
        "delivery_status", "delivery_error_code", "updated_at",
    ])
    return True


_DELIVERY_ERROR_CODES = {
    "configuration_error",
    "request_error",
    "provider_rejected",
    "network_error",
    "invalid_provider_response",
    "delivery_error",
}


def _sanitize_delivery_error_code(error_code):
    """Persist only known machine codes, never provider exception text."""
    if not isinstance(error_code, str):
        return "delivery_error"
    normalized = error_code.strip().lower()
    return normalized if normalized in _DELIVERY_ERROR_CODES else "delivery_error"


def _usable_for_delivery(invitation):
    return (
        not invitation.is_deleted
        and invitation.status == InvitationStatus.PENDING
        and invitation.expires_at > timezone.now()
        and invitation.usage_count < invitation.usage_limit
    )


def _usable(invitation, now=None, active_reservations=0):
    now = now or timezone.now()
    if invitation.is_deleted or invitation.status != InvitationStatus.PENDING:
        return False
    if (
        invitation.expires_at <= now
        or invitation.usage_count + active_reservations >= invitation.usage_limit
    ):
        return False
    if invitation.mode == InvitationMode.EMAIL and invitation.delivery_status != DeliveryStatus.SENT:
        return False
    return True


def get_invitation_management_status(invitation, now=None):
    """Return the lifecycle status for display without mutating the invitation."""
    now = now or timezone.now()
    if invitation.status == InvitationStatus.PENDING:
        if invitation.expires_at <= now:
            return InvitationStatus.EXPIRED
        if invitation.usage_count >= invitation.usage_limit:
            return InvitationStatus.EXHAUSTED
    return invitation.status


def _lock_acceptance(session_token):
    token_digest = _token_hash(session_token)
    acceptance_ref = SocialAccountInvitationAcceptance.objects.filter(
        token_hash=token_digest,
        is_deleted=False,
    ).values("pk", "invitation_id").first()
    if acceptance_ref is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    # Every operation locks invitation first, then acceptance. This matches
    # claim_invitation and prevents claim/cancel/complete lock-order deadlocks.
    invitation = SocialAccountInvitation.objects.select_for_update().get(
        pk=acceptance_ref["invitation_id"]
    )
    acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().filter(
        pk=acceptance_ref["pk"],
        token_hash=token_digest,
        is_deleted=False,
    ).first()
    if acceptance is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    return acceptance, invitation


def _lock_acceptance_by_id(acceptance_id):
    acceptance_ref = SocialAccountInvitationAcceptance.objects.filter(
        pk=acceptance_id,
        is_deleted=False,
    ).values("pk", "invitation_id").first()
    if acceptance_ref is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    invitation = SocialAccountInvitation.objects.select_for_update().filter(
        pk=acceptance_ref["invitation_id"],
        is_deleted=False,
    ).first()
    if invitation is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().filter(
        pk=acceptance_ref["pk"],
        invitation=invitation,
        is_deleted=False,
    ).first()
    if acceptance is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    return acceptance, invitation


def _lock_active_acceptance(session_token):
    acceptance, invitation = _lock_acceptance(session_token)
    now = timezone.now()
    if (
        acceptance.status != AcceptanceStatus.ACTIVE
        or acceptance.expires_at <= now
        or not _usable(invitation, now)
    ):
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    return acceptance, invitation


def _lock_active_acceptance_by_id(acceptance_id):
    """Lock an active acceptance when a consumed OAuth state identifies it."""
    acceptance_ref = SocialAccountInvitationAcceptance.objects.filter(
        pk=acceptance_id,
        is_deleted=False,
    ).values("pk", "invitation_id").first()
    if acceptance_ref is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    invitation = SocialAccountInvitation.objects.select_for_update().filter(
        pk=acceptance_ref["invitation_id"],
        is_deleted=False,
    ).first()
    if invitation is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().filter(
        pk=acceptance_ref["pk"],
        invitation=invitation,
        is_deleted=False,
    ).first()
    now = timezone.now()
    if (
        acceptance is None
        or acceptance.status != AcceptanceStatus.ACTIVE
        or acceptance.expires_at <= now
        or not _usable(invitation, now)
    ):
        raise InvalidInvitation("This invitation session is invalid or no longer available.")
    return acceptance, invitation


def get_invitation_acceptance_context(session_token):
    """Validate a live acceptance and derive its organization/platform scope.

    OAuth adapters should use this at start and use
    ``persist_invitation_account`` immediately before account persistence,
    since revocation or expiry can occur after this read.
    """
    with transaction.atomic():
        acceptance, invitation = _lock_active_acceptance(session_token)
        return {
            "acceptance_id": acceptance.pk,
            "organization": invitation.organization,
            "allowed_platforms": tuple(invitation.allowed_platforms),
            "selected_platforms": tuple(acceptance.selected_platforms),
            "expires_at": acceptance.expires_at,
        }


def _read_resumption_claims(resumption_token, expected_platform=None):
    try:
        claims = read_platform_resumption_token(resumption_token)
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError) as exc:
        raise InvalidInvitation("This platform invitation link is invalid or expired.") from exc

    if not isinstance(claims, dict):
        raise InvalidInvitation("This platform invitation link is invalid or expired.")
    platform = str(claims.get("platform") or "").strip().lower()
    if (
        not claims.get("invitation_id")
        or not isinstance(claims.get("token_hash"), str)
        or len(claims["token_hash"]) != 64
        or platform not in InvitationOAuthPlatform.values
        or (expected_platform is not None and platform != str(expected_platform).lower())
    ):
        raise InvalidInvitation("This platform invitation link is invalid or expired.")
    return claims


def _validate_resumption_invitation(invitation, claims, now):
    platform = claims["platform"]
    if (
        invitation.is_deleted
        or invitation.mode != InvitationMode.EMAIL
        or invitation.status != InvitationStatus.PENDING
        or invitation.expires_at <= now
        or invitation.usage_count >= invitation.usage_limit
        or invitation.delivery_status != DeliveryStatus.SENT
        or invitation.token_hash != claims["token_hash"]
        or platform not in invitation.allowed_platforms
    ):
        raise InvalidInvitation("This platform invitation link is invalid or no longer available.")
    return platform


def _resumption_context(acceptance, invitation):
    connected_platforms = set()
    associations = SocialAccountInvitationAcceptanceAccount.objects.filter(
        acceptance=acceptance,
        is_deleted=False,
        social_account__isnull=False,
    ).select_related("social_account", "social_account__connection")
    for association in associations:
        account = association.social_account
        if (
            account.is_deleted
            or account.organization_id != invitation.organization_id
            or association.platform != account.platform
            or association.platform_account_id != account.platform_account_id
            or account.platform not in acceptance.selected_platforms
            or account.status != SocialAccountStatus.CONNECTED
            or not account.is_valid
            or not _has_active_provider_credential(account)
        ):
            continue
        connected_platforms.add(account.platform)
    return {
        "acceptance_id": acceptance.pk,
        "organization": invitation.organization,
        "organization_name": invitation.organization.name,
        "allowed_platforms": tuple(invitation.allowed_platforms),
        "selected_platforms": tuple(acceptance.selected_platforms),
        "connected_platforms": tuple(sorted(connected_platforms)),
        "expires_at": acceptance.expires_at,
    }


def _carry_forward_valid_connected_accounts(invitation, acceptance):
    """Retain verified partial work when a 30-minute claim expires.

    Platform email links remain usable for the invitation lifetime. If a
    client authorizes one platform and returns for another after the short
    acceptance session expires, preserve the first connection through a new
    audit association instead of requiring that platform to be authorized
    again. The existing historical association is the evidence; current
    organization, platform, account, and credential state are rechecked.
    """
    prior_links = SocialAccountInvitationAcceptanceAccount.objects.filter(
        acceptance__invitation=invitation,
        acceptance__is_deleted=False,
        acceptance__status=AcceptanceStatus.EXPIRED,
        is_deleted=False,
        social_account__isnull=False,
        social_account__is_deleted=False,
    ).select_related("social_account", "social_account__connection").order_by("pk")
    for prior_link in prior_links:
        account = prior_link.social_account
        if (
            account.organization_id != invitation.organization_id
            or account.platform not in acceptance.selected_platforms
            or account.platform not in invitation.allowed_platforms
            or prior_link.platform != account.platform
            or prior_link.platform_account_id != account.platform_account_id
            or account.status != SocialAccountStatus.CONNECTED
            or not account.is_valid
            or not _has_active_provider_credential(account)
        ):
            continue
        SocialAccountInvitationAcceptanceAccount.objects.get_or_create(
            acceptance=acceptance,
            social_account=account,
            defaults={
                "platform": account.platform,
                "platform_account_id": account.platform_account_id,
            },
        )


@transaction.atomic
def resume_invitation_platform(resumption_token, *, expected_platform):
    """Create or resume the one active acceptance for a platform CTA.

    The signed capability is replayable until invitation expiry by design so
    separate email buttons/tabs can continue the same acceptance. Provider
    OAuth state remains a separate, one-time credential.
    """
    claims = _read_resumption_claims(resumption_token, expected_platform)
    try:
        invitation = SocialAccountInvitation.objects.select_for_update().get(
            pk=claims["invitation_id"],
            is_deleted=False,
        )
    except SocialAccountInvitation.DoesNotExist as exc:
        raise InvalidInvitation("This platform invitation link is invalid or no longer available.") from exc

    now = timezone.now()
    platform = _validate_resumption_invitation(invitation, claims, now)
    SocialAccountInvitationAcceptance.objects.filter(
        invitation=invitation,
        is_deleted=False,
        status=AcceptanceStatus.ACTIVE,
        expires_at__lte=now,
    ).update(status=AcceptanceStatus.EXPIRED, updated_at=now)

    acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().filter(
        invitation=invitation,
        is_deleted=False,
        status=AcceptanceStatus.ACTIVE,
        expires_at__gt=now,
    ).order_by("created_at", "pk").first()

    if acceptance is None:
        active_count = SocialAccountInvitationAcceptance.objects.filter(
            invitation=invitation,
            is_deleted=False,
            status=AcceptanceStatus.ACTIVE,
            expires_at__gt=now,
        ).count()
        if invitation.usage_count + active_count >= invitation.usage_limit:
            raise InvalidInvitation("This invitation is currently in use or has reached its limit.")
        acceptance = SocialAccountInvitationAcceptance.objects.create(
            invitation=invitation,
            token_hash=_token_hash(_new_token()),
            selected_platforms=sorted(set(invitation.allowed_platforms)),
            expires_at=min(invitation.expires_at, now + timedelta(minutes=30)),
        )
        _carry_forward_valid_connected_accounts(invitation, acceptance)

    if platform not in acceptance.selected_platforms:
        raise InvalidInvitation("This platform is not selected for the active invitation session.")
    return _resumption_context(acceptance, invitation)


@transaction.atomic
def get_invitation_acceptance_context_for_resumption(
    resumption_token,
    *,
    expected_platform,
    allow_completed=False,
):
    """Resolve a scoped CTA token to its invitation-bound acceptance."""
    claims = _read_resumption_claims(resumption_token, expected_platform)
    try:
        invitation = SocialAccountInvitation.objects.select_for_update().get(
            pk=claims["invitation_id"],
            is_deleted=False,
        )
    except SocialAccountInvitation.DoesNotExist as exc:
        raise InvalidInvitation("This platform invitation link is invalid or no longer available.") from exc

    now = timezone.now()
    platform = claims["platform"]
    completed_retry = (
        allow_completed and invitation.status == InvitationStatus.ACCEPTED
    )
    if (
        invitation.mode != InvitationMode.EMAIL
        or (invitation.expires_at <= now and not completed_retry)
        or invitation.token_hash != claims["token_hash"]
        or platform not in invitation.allowed_platforms
        or (invitation.status != InvitationStatus.PENDING and not completed_retry)
    ):
        raise InvalidInvitation("This platform invitation link is invalid or no longer available.")

    acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().filter(
        invitation=invitation,
        is_deleted=False,
        status=AcceptanceStatus.ACTIVE,
        expires_at__gt=now,
    ).order_by("created_at", "pk").first()
    if acceptance is None and allow_completed and invitation.status == InvitationStatus.ACCEPTED:
        acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().filter(
            invitation=invitation,
            is_deleted=False,
            status=AcceptanceStatus.COMPLETED,
        ).order_by("-completed_at", "-pk").first()
    if acceptance is None:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")

    if acceptance.status == AcceptanceStatus.ACTIVE:
        if not _usable(invitation, now) or acceptance.expires_at <= now:
            raise InvalidInvitation("This invitation session is invalid or no longer available.")
    elif not allow_completed or acceptance.status != AcceptanceStatus.COMPLETED:
        raise InvalidInvitation("This invitation session is invalid or no longer available.")

    if platform not in acceptance.selected_platforms:
        raise InvalidInvitation("This platform is not selected for the active invitation session.")
    return _resumption_context(acceptance, invitation)


def get_invitation_acceptance_context_by_id(acceptance_id):
    """Revalidate a consumed OAuth attempt's acceptance without a bearer token."""
    with transaction.atomic():
        acceptance, invitation = _lock_active_acceptance_by_id(acceptance_id)
        return {
            "acceptance_id": acceptance.pk,
            "organization": invitation.organization,
            "allowed_platforms": tuple(invitation.allowed_platforms),
            "selected_platforms": tuple(acceptance.selected_platforms),
            "expires_at": acceptance.expires_at,
        }


@transaction.atomic
def create_invitation_oauth_attempt(acceptance_token, platform):
    """Create a short-lived, one-time OAuth state for a claimed invitation."""
    platform = str(platform or "").strip().lower()
    if platform not in InvitationOAuthPlatform.values:
        raise InvalidInvitation("This platform is not available through the invitation.")

    context = get_invitation_acceptance_context(acceptance_token)
    if (
        platform not in context["allowed_platforms"]
        or platform not in context["selected_platforms"]
    ):
        raise InvalidInvitation("This platform is not available through the invitation.")

    now = timezone.now()
    expires_at = min(
        context["expires_at"],
        now + INVITATION_OAUTH_ATTEMPT_TTL,
    )
    if expires_at <= now:
        raise InvalidInvitation("This invitation session is no longer available.")

    acceptance = SocialAccountInvitationAcceptance.objects.get(
        pk=context["acceptance_id"],
        is_deleted=False,
    )
    # Keep only the newest outstanding state for this acceptance/platform.
    SocialAccountInvitationOAuthAttempt.objects.filter(
        acceptance=acceptance,
        platform=platform,
        consumed_at__isnull=True,
        is_deleted=False,
        expires_at__gt=now,
    ).update(expires_at=now, updated_at=now)

    raw_state = _new_token()
    attempt = SocialAccountInvitationOAuthAttempt.objects.create(
        acceptance=acceptance,
        platform=platform,
        state_hash=_token_hash(raw_state),
        expires_at=expires_at,
    )
    return attempt, raw_state


@transaction.atomic
def create_invitation_oauth_attempt_for_resumption(resumption_token, *, platform):
    """Create one-time provider state after validating a scoped email CTA."""
    platform = str(platform or "").strip().lower()
    if platform not in InvitationOAuthPlatform.values:
        raise InvalidInvitation("This platform is not available through the invitation.")
    context = resume_invitation_platform(
        resumption_token,
        expected_platform=platform,
    )
    acceptance, invitation = _lock_active_acceptance_by_id(context["acceptance_id"])
    if platform not in invitation.allowed_platforms or platform not in acceptance.selected_platforms:
        raise InvalidInvitation("This platform is not available through the invitation.")

    now = timezone.now()
    expires_at = min(context["expires_at"], now + INVITATION_OAUTH_ATTEMPT_TTL)
    if expires_at <= now:
        raise InvalidInvitation("This invitation session is no longer available.")
    SocialAccountInvitationOAuthAttempt.objects.filter(
        acceptance=acceptance,
        platform=platform,
        consumed_at__isnull=True,
        is_deleted=False,
        expires_at__gt=now,
    ).update(expires_at=now, updated_at=now)
    raw_state = _new_token()
    attempt = SocialAccountInvitationOAuthAttempt.objects.create(
        acceptance=acceptance,
        platform=platform,
        state_hash=_token_hash(raw_state),
        expires_at=expires_at,
    )
    return attempt, raw_state, context


@transaction.atomic
def consume_invitation_oauth_attempt(state, *, expected_platform=None):
    """Validate and atomically consume one invitation OAuth callback state.

    The caller must perform provider exchange and account persistence only
    after this succeeds. A callback failure requires a new attempt.
    """
    if not isinstance(state, str) or not state or len(state) > 200:
        raise InvalidInvitation("This OAuth attempt is invalid or no longer available.")
    if expected_platform is not None:
        expected_platform = str(expected_platform or "").strip().lower()
        if expected_platform not in InvitationOAuthPlatform.values:
            raise InvalidInvitation("This OAuth attempt is invalid or no longer available.")

    state_digest = _token_hash(state)
    attempt_ref = SocialAccountInvitationOAuthAttempt.objects.filter(
        state_hash=state_digest,
        is_deleted=False,
    ).values("pk", "acceptance_id", "acceptance__invitation_id").first()
    if attempt_ref is None:
        raise InvalidInvitation("This OAuth attempt is invalid or no longer available.")

    # Preserve the invitation lifecycle's invitation -> acceptance lock order,
    # then lock the attempt to serialize callback consumption.
    try:
        invitation = SocialAccountInvitation.objects.select_for_update().get(
            pk=attempt_ref["acceptance__invitation_id"],
            is_deleted=False,
        )
        acceptance = SocialAccountInvitationAcceptance.objects.select_for_update().get(
            pk=attempt_ref["acceptance_id"],
            is_deleted=False,
            invitation=invitation,
        )
        attempt = SocialAccountInvitationOAuthAttempt.objects.select_for_update().get(
            pk=attempt_ref["pk"],
            state_hash=state_digest,
            acceptance=acceptance,
            is_deleted=False,
        )
    except (
        SocialAccountInvitation.DoesNotExist,
        SocialAccountInvitationAcceptance.DoesNotExist,
        SocialAccountInvitationOAuthAttempt.DoesNotExist,
    ) as exc:
        raise InvalidInvitation("This OAuth attempt is invalid or no longer available.") from exc

    now = timezone.now()
    if (
        acceptance.status != AcceptanceStatus.ACTIVE
        or acceptance.expires_at <= now
        or not _usable(invitation, now)
        or attempt.is_consumed
        or attempt.expires_at <= now
        or attempt.platform not in invitation.allowed_platforms
        or attempt.platform not in acceptance.selected_platforms
        or (expected_platform is not None and attempt.platform != expected_platform)
    ):
        raise InvalidInvitation("This OAuth attempt is invalid or no longer available.")

    attempt.consumed_at = now
    attempt.save(update_fields=["consumed_at", "updated_at"])
    return {
        "attempt_id": attempt.pk,
        "acceptance_id": acceptance.pk,
        "organization": invitation.organization,
        "platform": attempt.platform,
        "expires_at": attempt.expires_at,
    }


@transaction.atomic
def persist_invitation_account(session_token, persist_account):
    """Run local account persistence under invitation/acceptance locks.

    ``persist_account`` must perform the existing provider credential and
    SocialAccount persistence and return the saved SocialAccount. Network
    provider calls should happen before this callback. The outer transaction
    rolls back partial account writes if the invitation is no longer usable.
    This does not finish the acceptance: a Facebook selection session may add
    multiple Pages, and a combined invitation may authorize both platforms.
    """
    acceptance, invitation = _lock_active_acceptance(session_token)
    return _persist_invitation_account_locked(acceptance, invitation, persist_account)


@transaction.atomic
def persist_invitation_account_for_acceptance(acceptance_id, persist_account):
    """Persist through an acceptance resolved by a signed platform capability."""
    acceptance, invitation = _lock_active_acceptance_by_id(acceptance_id)
    return _persist_invitation_account_locked(acceptance, invitation, persist_account)


def _persist_invitation_account_locked(acceptance, invitation, persist_account):
    social_account = persist_account(
        organization=invitation.organization,
        allowed_platforms=tuple(invitation.allowed_platforms),
        selected_platforms=tuple(acceptance.selected_platforms),
    )
    if not isinstance(social_account, SocialAccount) or not social_account.pk:
        raise InvitationError("Account persistence did not return a saved social account.")

    saved_account = SocialAccount.objects.select_for_update().filter(
        pk=social_account.pk,
        organization=invitation.organization,
        platform__in=acceptance.selected_platforms,
        status=SocialAccountStatus.CONNECTED,
        is_valid=True,
        is_deleted=False,
    ).first()
    if saved_account is None:
        raise InvitationError("The persisted account is outside the invitation scope.")
    if not _has_active_provider_credential(saved_account):
        raise InvitationError("The persisted account has no active provider credential.")

    SocialAccountInvitationAcceptanceAccount.objects.get_or_create(
        acceptance=acceptance,
        social_account=saved_account,
        defaults={
            "platform": saved_account.platform,
            "platform_account_id": saved_account.platform_account_id,
        },
    )
    return saved_account


def _has_active_provider_credential(social_account):
    now = timezone.now()
    if social_account.platform == SocialPlatform.FACEBOOK:
        from apps.integrations.meta.models import (
            MetaAccountCredential,
            MetaCredentialStatus,
            MetaCredentialType,
        )
        from apps.social_accounts.models import SocialConnectionProvider, SocialConnectionStatus

        if not social_account.connection_id:
            return False
        page_credential = MetaAccountCredential.objects.filter(
            social_account=social_account,
            credential_type=MetaCredentialType.PAGE,
            status=MetaCredentialStatus.ACTIVE,
            access_token__gt="",
            is_deleted=False,
        ).filter(
            models.Q(token_expires_at__isnull=True)
            | models.Q(token_expires_at__gt=now)
        ).exists()
        user_credential = MetaAccountCredential.objects.filter(
            social_connection_id=social_account.connection_id,
            credential_type=MetaCredentialType.USER,
            status=MetaCredentialStatus.ACTIVE,
            access_token__gt="",
            is_deleted=False,
        ).filter(
            models.Q(token_expires_at__isnull=True)
            | models.Q(token_expires_at__gt=now),
            models.Q(provider_is_valid__isnull=True)
            | models.Q(provider_is_valid=True),
            models.Q(provider_expires_at__isnull=True)
            | models.Q(provider_expires_at__gt=now),
            models.Q(data_access_expires_at__isnull=True)
            | models.Q(data_access_expires_at__gt=now),
        ).exists()
        return (
            social_account.connection.provider == SocialConnectionProvider.META
            and social_account.connection.status == SocialConnectionStatus.ACTIVE
            and not social_account.connection.is_deleted
            and page_credential
            and user_credential
        )

    if social_account.platform == SocialPlatform.INSTAGRAM:
        from apps.integrations.instagram.models import (
            InstagramAccountCredential,
            InstagramCredentialStatus,
        )

        return InstagramAccountCredential.objects.filter(
            social_account=social_account,
            status=InstagramCredentialStatus.ACTIVE,
            encrypted_access_token__gt="",
            is_deleted=False,
        ).filter(
            models.Q(token_expires_at__isnull=True)
            | models.Q(token_expires_at__gt=now)
        ).exists()
    return False


def validate_invitation(token):
    now = timezone.now()
    try:
        invitation = (
            SocialAccountInvitation.objects.select_related("organization")
            .annotate(
                active_reservations=models.Count(
                    "acceptances",
                    filter=models.Q(
                        acceptances__is_deleted=False,
                        acceptances__status=AcceptanceStatus.ACTIVE,
                        acceptances__expires_at__gt=now,
                    ),
                ),
            )
            .get(token_hash=_token_hash(token), is_deleted=False)
        )
    except SocialAccountInvitation.DoesNotExist:
        return {"valid": False, "usable": False}

    if invitation.status == InvitationStatus.PENDING and invitation.expires_at <= now:
        invitation.status = InvitationStatus.EXPIRED
        invitation.pending_token_hash = ""
        invitation.pending_delivery_token_encrypted = ""
        invitation.save(update_fields=[
            "status", "pending_token_hash",
            "pending_delivery_token_encrypted", "updated_at",
        ])
        _invalidate_instagram_oauth_staging(
            invitation.acceptances.filter(is_deleted=False).values_list("pk", flat=True)
        )
    usable = _usable(invitation, now, invitation.active_reservations)
    if invitation.usage_count >= invitation.usage_limit and invitation.status == InvitationStatus.PENDING:
        invitation.status = InvitationStatus.EXHAUSTED
        invitation.save(update_fields=["status", "updated_at"])
    return {
        "valid": True,
        "usable": usable,
        "organization_name": invitation.organization.name if usable else None,
        "platforms": invitation.allowed_platforms if usable else [],
        "expires_at": invitation.expires_at if usable else None,
        "bearer_link": invitation.mode == InvitationMode.SHARE_LINK,
        "email_delivery_pending": (
            invitation.mode == InvitationMode.EMAIL
            and invitation.delivery_status != DeliveryStatus.SENT
        ),
    }


@transaction.atomic
def claim_invitation(token, platforms=None):
    invitation = (
        SocialAccountInvitation.objects.select_for_update()
        .filter(token_hash=_token_hash(token), is_deleted=False)
        .first()
    )
    if invitation is None or not _usable(invitation):
        raise InvalidInvitation("This invitation is invalid or no longer available.")

    if platforms is None:
        platforms = invitation.allowed_platforms
    platforms = sorted(set(platforms))
    if not platforms or not set(platforms).issubset(set(invitation.allowed_platforms)):
        raise InvalidInvitation("The selected platform is not allowed by this invitation.")

    now = timezone.now()
    SocialAccountInvitationAcceptance.objects.filter(
        invitation=invitation,
        is_deleted=False,
        status=AcceptanceStatus.ACTIVE,
        expires_at__lte=now,
    ).update(status=AcceptanceStatus.EXPIRED, updated_at=now)
    active = SocialAccountInvitationAcceptance.objects.filter(
        invitation=invitation,
        is_deleted=False,
        status=AcceptanceStatus.ACTIVE,
        expires_at__gt=now,
    ).count()
    if invitation.usage_count + active >= invitation.usage_limit:
        raise InvalidInvitation("This invitation is currently in use or has reached its limit.")

    raw_session_token = _new_token()
    acceptance = SocialAccountInvitationAcceptance.objects.create(
        invitation=invitation,
        token_hash=_token_hash(raw_session_token),
        selected_platforms=platforms,
        expires_at=min(invitation.expires_at, now + timedelta(minutes=30)),
    )
    return acceptance, raw_session_token


@transaction.atomic
def complete_invitation_acceptance(session_token):
    acceptance, invitation = _lock_acceptance(session_token)
    return _complete_locked_invitation_acceptance(acceptance, invitation)


@transaction.atomic
def complete_invitation_acceptance_for_resumption(
    resumption_token, *, expected_platform=None
):
    context = get_invitation_acceptance_context_for_resumption(
        resumption_token,
        expected_platform=expected_platform,
        allow_completed=True,
    )
    acceptance, invitation = _lock_acceptance_by_id(context["acceptance_id"])
    return _complete_locked_invitation_acceptance(acceptance, invitation)


def _complete_locked_invitation_acceptance(acceptance, invitation):
    now = timezone.now()
    if acceptance.status == AcceptanceStatus.COMPLETED:
        return invitation
    if acceptance.status != AcceptanceStatus.ACTIVE or acceptance.expires_at <= now:
        raise InvalidInvitation("This invitation session is no longer available.")
    if not _usable(invitation, now):
        raise InvalidInvitation("This invitation is no longer available.")
    selected_platforms = set(acceptance.selected_platforms)
    allowed_platforms = set(invitation.allowed_platforms)
    if not selected_platforms or not selected_platforms.issubset(allowed_platforms):
        raise InvalidInvitation("This invitation session has an invalid platform scope.")

    # Lock and inspect the persisted audit links and their accounts. Client
    # supplied account IDs are never used as evidence of a successful connect.
    associations = list(
        acceptance.connected_accounts.select_for_update().filter(is_deleted=False)
    )
    account_ids = {
        association.social_account_id
        for association in associations
        if association.social_account_id is not None
    }
    accounts_by_id = {
        account.pk: account
        for account in SocialAccount.objects.select_for_update().filter(
            pk__in=account_ids,
        )
    }
    connected_platforms = set()
    for association in associations:
        account = accounts_by_id.get(association.social_account_id)
        if (
            account is None
            or account.is_deleted
            or account.organization_id != invitation.organization_id
            or account.platform not in selected_platforms
            or account.platform not in allowed_platforms
            or association.platform != account.platform
            or association.platform_account_id != account.platform_account_id
            or account.status != SocialAccountStatus.CONNECTED
            or not account.is_valid
            or not _has_active_provider_credential(account)
        ):
            continue
        connected_platforms.add(account.platform)
    if not set(acceptance.selected_platforms).issubset(connected_platforms):
        raise IncompleteInvitation(
            "Connect at least one usable account for every selected platform before completing this invitation."
        )

    acceptance.status = AcceptanceStatus.COMPLETED
    acceptance.completed_at = now
    acceptance.save(update_fields=["status", "completed_at", "updated_at"])
    _clear_invitation_oauth_secrets([acceptance.pk])
    invitation.usage_count += 1
    invitation.accepted_at = now
    if invitation.usage_count >= invitation.usage_limit:
        invitation.status = (
            InvitationStatus.ACCEPTED
            if invitation.mode == InvitationMode.EMAIL
            else InvitationStatus.EXHAUSTED
        )
    invitation.save(update_fields=["usage_count", "status", "accepted_at", "updated_at"])
    return invitation


@transaction.atomic
def cancel_invitation_acceptance(session_token):
    """Cancel an abandoned claim and release its reserved use."""
    acceptance, invitation = _lock_acceptance(session_token)
    if acceptance.status == AcceptanceStatus.CANCELLED:
        _clear_invitation_oauth_secrets([acceptance.pk])
        return acceptance
    if acceptance.status == AcceptanceStatus.COMPLETED:
        raise InvalidInvitation("A completed invitation session cannot be cancelled.")
    if acceptance.connected_accounts.filter(
        is_deleted=False,
        social_account__is_deleted=False,
    ).exists():
        raise InvalidInvitation("A session with a connected account cannot release its invitation use.")
    if acceptance.status == AcceptanceStatus.ACTIVE:
        now = timezone.now()
        if acceptance.expires_at <= now:
            acceptance.status = AcceptanceStatus.EXPIRED
            acceptance.save(update_fields=["status", "updated_at"])
        else:
            acceptance.status = AcceptanceStatus.CANCELLED
            acceptance.cancelled_at = now
            acceptance.save(update_fields=["status", "cancelled_at", "updated_at"])
    if acceptance.status in {AcceptanceStatus.CANCELLED, AcceptanceStatus.EXPIRED}:
        _clear_invitation_oauth_secrets([acceptance.pk])
    return acceptance


@transaction.atomic
def revoke_invitation(invitation):
    invitation = SocialAccountInvitation.objects.select_for_update().get(pk=invitation.pk)
    if invitation.status in (InvitationStatus.PENDING,):
        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = timezone.now()
        invitation.pending_token_hash = ""
        invitation.pending_delivery_token_encrypted = ""
        invitation.save(update_fields=[
            "status", "revoked_at", "pending_token_hash",
            "pending_delivery_token_encrypted", "updated_at",
        ])
    _clear_invitation_oauth_secrets(
        invitation.acceptances.filter(is_deleted=False).values_list("pk", flat=True),
    )
    return invitation

