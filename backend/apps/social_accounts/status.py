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
    def parent_meta_credential_needs_reconnect(social_account):
        status = SocialAccountLifecycleStatus.get_parent_user_credential_status(
            social_account,
        )
        return status in SocialAccountLifecycleStatus.PARENT_RECONNECT_STATUSES

    PARENT_RECONNECT_STATUSES = {
        MetaCredentialStatus.EXPIRED.lower(),
        MetaCredentialStatus.REVOKED.lower(),
        MetaCredentialStatus.INVALID.lower(),
        MetaCredentialStatus.ERROR.lower(),
    }

    @staticmethod
    def get_parent_user_credential_status(social_account):
        """Return the Facebook connection's USER credential status, if present."""
        if (
            social_account.platform != SocialPlatform.FACEBOOK
            or not social_account.connection_id
        ):
            return None

        cache_attribute = "_parent_user_credential_status_cache"
        if hasattr(social_account, cache_attribute):
            return getattr(social_account, cache_attribute)

        from apps.integrations.meta.selectors import get_meta_connection_credential

        parent = get_meta_connection_credential(
            social_connection=social_account.connection,
        )
        if parent is None:
            # The selector omits ACTIVE USER credentials that are not eligible
            # for provider operations. Still expose their stored lifecycle
            # status; this read-only display field must not make them usable.
            from apps.integrations.meta.models import MetaAccountCredential

            parent = MetaAccountCredential.objects.filter(
                social_connection_id=social_account.connection_id,
                credential_type=MetaCredentialType.USER,
                is_deleted=False,
            ).order_by("-updated_at", "-created_at", "-id").first()
        status = parent.status.lower() if parent else None
        setattr(social_account, cache_attribute, status)
        return status

    @staticmethod
    def page_needs_reconnect(social_account, credential_status):
        """Resolve reconnect need using only this account and its own credential."""
        if social_account.status in {
            SocialAccountStatus.DISCONNECTED,
            SocialAccountStatus.EXPIRED,
            SocialAccountStatus.ERROR,
        }:
            return True

        return credential_status in {
            InstagramCredentialStatus.EXPIRED.lower(),
            InstagramCredentialStatus.REVOKED.lower(),
            InstagramCredentialStatus.ERROR.lower(),
            MetaCredentialStatus.EXPIRED.lower(),
            MetaCredentialStatus.REVOKED.lower(),
            MetaCredentialStatus.INVALID.lower(),
            MetaCredentialStatus.ERROR.lower(),
        }

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

        return (
            SocialAccountLifecycleStatus.page_needs_reconnect(
                social_account,
                credential_status,
            )
            or SocialAccountLifecycleStatus.parent_meta_credential_needs_reconnect(
                social_account,
            )
        )
