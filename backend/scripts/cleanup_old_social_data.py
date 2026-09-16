from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionStatus,
)

from apps.integrations.instagram.models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
)

from apps.integrations.meta.models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaSocialAccountLink,
)


PROTECTED_ORG_ID = "ORG000022"

# Safety switch.
# This MUST remain False until you intentionally execute cleanup.
# CONFIRM_DELETE = False
CONFIRM_DELETE = True   


def run_cleanup():
    if not CONFIRM_DELETE:
        print("CLEANUP NOT EXECUTED.")
        print("Set CONFIRM_DELETE = True only when you are ready.")
        return

    # --------------------------------------------------------
    # Build target querysets
    # --------------------------------------------------------

    social_accounts = SocialAccount.objects.filter(
        is_deleted=False,
    ).exclude(
        organization__organization_id=PROTECTED_ORG_ID,
    )

    instagram_credentials = InstagramAccountCredential.objects.filter(
        is_deleted=False,
    ).exclude(
        social_account__organization__organization_id=PROTECTED_ORG_ID,
    )

    meta_page_credentials = MetaAccountCredential.objects.filter(
        is_deleted=False,
        credential_type=MetaCredentialType.PAGE,
    ).exclude(
        social_account__organization__organization_id=PROTECTED_ORG_ID,
    )

    meta_user_credentials = MetaAccountCredential.objects.filter(
        is_deleted=False,
        credential_type=MetaCredentialType.USER,
    ).exclude(
        social_connection__organization__organization_id=PROTECTED_ORG_ID,
    )

    social_connections = SocialConnection.objects.filter(
        is_deleted=False,
    ).exclude(
        organization__organization_id=PROTECTED_ORG_ID,
    )

    meta_links = MetaSocialAccountLink.objects.filter(
        is_deleted=False,
    ).exclude(
        organization__organization_id=PROTECTED_ORG_ID,
    )

    print("")
    print("==============================================")
    print("OLD SOCIAL DATA CLEANUP")
    print("==============================================")
    print("Protected organization:", PROTECTED_ORG_ID)
    print("----------------------------------------------")
    print("Social Accounts       :", social_accounts.count())
    print("Instagram Credentials :", instagram_credentials.count())
    print("Meta PAGE Credentials :", meta_page_credentials.count())
    print("Meta USER Credentials :", meta_user_credentials.count())
    print("Social Connections    :", social_connections.count())
    print("Meta Account Links    :", meta_links.count())
    print("----------------------------------------------")

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    protected_social_accounts = SocialAccount.objects.filter(
        organization__organization_id=PROTECTED_ORG_ID,
        is_deleted=False,
    ).count()

    protected_instagram_credentials = (
        InstagramAccountCredential.objects.filter(
            social_account__organization__organization_id=PROTECTED_ORG_ID,
            is_deleted=False,
        ).count()
    )

    protected_meta_credentials = MetaAccountCredential.objects.filter(
        Q(
            social_account__organization__organization_id=PROTECTED_ORG_ID,
        )
        | Q(
            social_connection__organization__organization_id=PROTECTED_ORG_ID,
        ),
        is_deleted=False,
    ).count()

    protected_connections = SocialConnection.objects.filter(
        organization__organization_id=PROTECTED_ORG_ID,
        is_deleted=False,
    ).count()

    protected_links = MetaSocialAccountLink.objects.filter(
        organization__organization_id=PROTECTED_ORG_ID,
        is_deleted=False,
    ).count()

    print("")
    print("PROTECTION CHECK")
    print("----------------------------------------------")
    print("ORG000022 SocialAccounts       :", protected_social_accounts)
    print("ORG000022 InstagramCredentials :", protected_instagram_credentials)
    print("ORG000022 MetaCredentials      :", protected_meta_credentials)
    print("ORG000022 SocialConnections     :", protected_connections)
    print("ORG000022 MetaLinks             :", protected_links)
    print("----------------------------------------------")

    if (
        protected_social_accounts == 0
        and protected_instagram_credentials == 0
        and protected_meta_credentials == 0
        and protected_connections == 0
        and protected_links == 0
    ):
        raise RuntimeError(
            "SAFETY CHECK FAILED: ORG000022 protection verification failed."
        )

    # --------------------------------------------------------
    # Execute inside one database transaction
    # --------------------------------------------------------

    now = timezone.now()

    with transaction.atomic():

        # ----------------------------------------------
        # Instagram credentials
        # ----------------------------------------------

        instagram_updated = instagram_credentials.update(
            status=InstagramCredentialStatus.REVOKED,
            is_deleted=True,
            deleted_at=now,
            updated_at=now,
        )

        # ----------------------------------------------
        # Meta PAGE credentials
        # ----------------------------------------------

        meta_page_updated = meta_page_credentials.update(
            status=MetaCredentialStatus.REVOKED,
            is_deleted=True,
            deleted_at=now,
            updated_at=now,
        )

        # ----------------------------------------------
        # Meta USER credentials
        # ----------------------------------------------

        meta_user_updated = meta_user_credentials.update(
            status=MetaCredentialStatus.REVOKED,
            is_deleted=True,
            deleted_at=now,
            updated_at=now,
        )

        # ----------------------------------------------
        # Social Accounts
        # ----------------------------------------------

        social_accounts_updated = social_accounts.update(
            status=SocialAccountStatus.DISCONNECTED,
            is_valid=False,
            is_deleted=True,
            deleted_at=now,
            updated_at=now,
        )

        # ----------------------------------------------
        # Meta relationship links
        # ----------------------------------------------

        meta_links_updated = meta_links.update(
            is_deleted=True,
            deleted_at=now,
            updated_at=now,
        )

        # ----------------------------------------------
        # Meta connections
        # ----------------------------------------------

        connections_updated = social_connections.update(
            status=SocialConnectionStatus.REVOKED,
            is_deleted=True,
            deleted_at=now,
            updated_at=now,
        )

    print("")
    print("==============================================")
    print("CLEANUP COMPLETED")
    print("==============================================")
    print("Instagram credentials :", instagram_updated)
    print("Meta PAGE credentials :", meta_page_updated)
    print("Meta USER credentials :", meta_user_updated)
    print("Social accounts       :", social_accounts_updated)
    print("Meta account links    :", meta_links_updated)
    print("Social connections    :", connections_updated)
    print("==============================================")
    print("ORG000022 WAS PROTECTED")
    print("==============================================")


if __name__ == "__main__":
    run_cleanup()