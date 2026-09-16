from apps.integrations.instagram.models import (
    InstagramCredentialStatus,
)
from apps.integrations.meta.models import (
    MetaCredentialStatus,
    MetaCredentialType,
)

from .models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)


class SocialAccountLifecycleStatus:
    """
    Read-only resolver for frontend-facing social-account
    lifecycle information.

    This class does NOT change database state.
    Provider-specific lifecycle services remain responsible
    for changing credential/account states.
    """

    @staticmethod
    def get_credential_status(social_account):
        """
        Resolve the provider credential status for a social account.

        Returns a normalized lowercase status string.

        No access token or sensitive credential information
        is returned.
        """

        if social_account.platform == SocialPlatform.INSTAGRAM:
            credential = getattr(
                social_account,
                "instagram_credential",
                None,
            )

            if credential is None:
                return None

            return credential.status.lower()

        if social_account.platform == SocialPlatform.FACEBOOK:
            credential = getattr(
                social_account,
                "meta_credential",
                None,
            )

            if credential is None:
                return None

            # Only PAGE credentials belong to a Facebook
            # SocialAccount.
            if credential.credential_type != MetaCredentialType.PAGE:
                return None

            return credential.status.lower()

        return None

    @staticmethod
    def get_last_verified_at(social_account):
        """
        Return the provider credential's last verification time.
        """

        if social_account.platform == SocialPlatform.INSTAGRAM:
            credential = getattr(
                social_account,
                "instagram_credential",
                None,
            )

            return credential.last_verified_at if credential else None

        if social_account.platform == SocialPlatform.FACEBOOK:
            credential = getattr(
                social_account,
                "meta_credential",
                None,
            )

            if credential and credential.credential_type == MetaCredentialType.PAGE:
                return credential.last_verified_at

        return None

    @staticmethod
    def needs_reconnect(
        social_account,
        credential_status,
    ):
        """
        Determine whether the frontend should offer reconnect.

        Reconnect is required for states where the stored
        authorization/credential can no longer be used.
        """

        if social_account.status in {
            SocialAccountStatus.DISCONNECTED,
            SocialAccountStatus.EXPIRED,
            SocialAccountStatus.ERROR,
        }:
            return True

        if credential_status in {
            InstagramCredentialStatus.EXPIRED.lower(),
            InstagramCredentialStatus.REVOKED.lower(),
            InstagramCredentialStatus.ERROR.lower(),
            MetaCredentialStatus.EXPIRED.lower(),
            MetaCredentialStatus.REVOKED.lower(),
            MetaCredentialStatus.INVALID.lower(),
            MetaCredentialStatus.ERROR.lower(),
        }:
            return True

        return False
