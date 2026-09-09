from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

from .exceptions import MetaIntegrationError


def _get_fernet():
    key = getattr(settings, "META_CREDENTIAL_ENCRYPTION_KEY", None)

    if not key:
        raise MetaIntegrationError(
            "Meta credential encryption key is not configured."
        )

    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise MetaIntegrationError(
            "Meta credential encryption key is invalid."
        ) from exc


def encrypt_token(token: str) -> str:
    if not token:
        raise MetaIntegrationError(
            "Cannot encrypt an empty Meta access token."
        )

    try:
        encrypted = _get_fernet().encrypt(token.encode())
    except Exception as exc:
        raise MetaIntegrationError(
            "Unable to encrypt Meta access token."
        ) from exc

    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        raise MetaIntegrationError(
            "Cannot decrypt an empty Meta access token."
        )

    try:
        decrypted = _get_fernet().decrypt(
            encrypted_token.encode()
        )
    except InvalidToken as exc:
        raise MetaIntegrationError(
            "Meta access token could not be decrypted."
        ) from exc

    return decrypted.decode()