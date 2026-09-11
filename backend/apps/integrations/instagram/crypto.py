from django.conf import settings
from cryptography.fernet import Fernet

from .exceptions import InstagramIntegrationError


def _get_fernet():
    encryption_key = getattr(
        settings,
        "META_CREDENTIAL_ENCRYPTION_KEY",
        "",
    )

    if not encryption_key:
        raise InstagramIntegrationError(
            "Instagram credential encryption key is not configured."
        )

    try:
        return Fernet(
            encryption_key.encode()
            if isinstance(encryption_key, str)
            else encryption_key
        )
    except Exception as exc:
        raise InstagramIntegrationError(
            "Instagram credential encryption key is invalid."
        ) from exc


def encrypt_token(token):
    if not token:
        raise InstagramIntegrationError(
            "Cannot encrypt an empty Instagram access token."
        )

    return _get_fernet().encrypt(
        token.encode()
    ).decode()


def decrypt_token(encrypted_token):
    if not encrypted_token:
        raise InstagramIntegrationError(
            "Encrypted Instagram access token is empty."
        )

    try:
        return _get_fernet().decrypt(
            encrypted_token.encode()
        ).decode()
    except Exception as exc:
        raise InstagramIntegrationError(
            "Unable to decrypt Instagram access token."
        ) from exc