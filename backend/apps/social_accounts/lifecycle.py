from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.integrations.instagram.services import (
    InstagramCredentialService,
)
from apps.integrations.meta.services import (
    MetaCredentialService,
)

from .models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)


@transaction.atomic
def disconnect_social_account_with_credentials(
    *,
    social_account,
):
    """
    Disconnect a social account and revoke its provider-specific
    credential.

    This is the application-level orchestration boundary for the
    disconnect operation.

    Responsibilities:
        1. Lock the SocialAccount.
        2. Verify that it still exists and is not deleted.
        3. Revoke the provider-specific credential.
        4. Mark the SocialAccount as disconnected.

    Provider-specific credential handling remains inside the
    corresponding integration app.
    """

    social_account = (
        SocialAccount.objects.select_for_update()
        .filter(
            pk=social_account.pk,
            is_deleted=False,
        )
        .first()
    )

    if not social_account:
        raise ValidationError({"social_account": "Social account not found."})

    # --------------------------------------------------------
    # PROVIDER-SPECIFIC CREDENTIAL REVOCATION
    # --------------------------------------------------------

    if social_account.platform == SocialPlatform.FACEBOOK:
        MetaCredentialService.revoke_page_credential_for_disconnect(
            social_account=social_account,
        )

    elif social_account.platform == SocialPlatform.INSTAGRAM:
        InstagramCredentialService.revoke_for_disconnect(
            social_account=social_account,
        )

    else:
        raise ValidationError(
            {"platform": ("Disconnect is not supported for this " "social platform.")}
        )

    # --------------------------------------------------------
    # SOCIAL ACCOUNT STATE
    # --------------------------------------------------------

    social_account.status = SocialAccountStatus.DISCONNECTED
    social_account.is_valid = False

    social_account.save(
        update_fields=[
            "status",
            "is_valid",
            "updated_at",
        ]
    )

    return social_account
