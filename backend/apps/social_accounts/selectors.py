from .models import SocialAccount


def social_account_queryset():
    """
    Base queryset for social-account read operations.
    """

    return (
        SocialAccount.objects.filter(is_deleted=False)
        .select_related("organization")
        .order_by(
            "platform",
            "account_name",
        )
    )


def get_social_accounts_for_organization(
    organization_id,
):
    """
    Return all active social accounts belonging
    to the given organization.
    """

    return social_account_queryset().filter(
        organization__organization_id=organization_id,
    )


def get_social_account_by_id(
    social_account_id,
    organization_id=None,
):
    """
    Return a single social account.

    When organization_id is provided, the account
    is additionally scoped to that organization.
    """

    queryset = social_account_queryset().filter(
        id=social_account_id,
    )

    if organization_id:
        queryset = queryset.filter(
            organization__organization_id=organization_id,
        )

    return queryset.first()
