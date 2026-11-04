"""Encryption for short-lived invitation delivery bearer tokens."""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core import signing


PLATFORM_RESUMPTION_SALT = "social-account-invitation-platform-resumption-v1"
PLATFORM_RESUMPTION_MAX_AGE = 72 * 60 * 60


class InvitationTokenEncryptionError(Exception):
    """Raised when a temporary invitation delivery token cannot be protected."""


def _fernet():
    key = getattr(settings, "META_CREDENTIAL_ENCRYPTION_KEY", "")
    if not key:
        raise InvitationTokenEncryptionError(
            "Invitation token encryption is not configured."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (TypeError, ValueError) as exc:
        raise InvitationTokenEncryptionError(
            "Invitation token encryption is misconfigured."
        ) from exc


def encrypt_invitation_token(token):
    if not token:
        raise InvitationTokenEncryptionError("Cannot encrypt an empty token.")
    return _fernet().encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_invitation_token(encrypted_token):
    if not encrypted_token:
        raise InvitationTokenEncryptionError("No pending delivery token is available.")
    try:
        return _fernet().decrypt(encrypted_token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
        raise InvitationTokenEncryptionError(
            "The pending delivery token could not be recovered."
        ) from exc


def create_platform_resumption_token(*, invitation_id, token_hash, platform):
    """Sign a platform-scoped continuation capability for an invitation link.

    The signed payload contains only the invitation identifier, active-token
    digest, and platform. It never contains the raw invitation token. The
    invitation lifecycle performs authoritative expiry, revocation, delivery,
    and token-digest checks whenever the capability is used.
    """
    return signing.dumps(
        {
            "invitation_id": str(invitation_id),
            "token_hash": token_hash,
            "platform": str(platform),
        },
        salt=PLATFORM_RESUMPTION_SALT,
        compress=True,
    )


def read_platform_resumption_token(token):
    """Verify a resumption capability's signature and bounded age."""
    if not isinstance(token, str) or not token or len(token) > 4096:
        raise signing.BadSignature("Invalid platform resumption token.")
    return signing.loads(
        token,
        salt=PLATFORM_RESUMPTION_SALT,
        max_age=PLATFORM_RESUMPTION_MAX_AGE,
    )
