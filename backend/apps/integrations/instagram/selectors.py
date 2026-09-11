from django.utils import timezone

from .models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
)


def get_instagram_credential(
    *,
    social_account,
):
    return (
        InstagramAccountCredential.objects.filter(
            social_account=social_account,
            is_deleted=False,
        )
        .first()
    )


def get_active_instagram_credential(
    *,
    social_account,
):
    credential = get_instagram_credential(
        social_account=social_account,
    )

    if not credential:
        return None

    if credential.status != InstagramCredentialStatus.ACTIVE:
        return None

    if (
        credential.token_expires_at
        and credential.token_expires_at <= timezone.now()
    ):
        return None

    return credential