from django.db.models import Count, Exists, OuterRef, Prefetch, Q

from .models import (
    Organization,
    OrganizationContact,
    OrganizationSubscription,
    SubscriptionStatus,
)


def organization_queryset():
    """
    Optimized base queryset for organization read operations.

    The list/detail serializers use prefetched data to avoid
    N+1 database queries.

    Only data required by the organization representation is
    prefetched. Historical subscription records are not loaded
    for the organization list page.
    """

    current_subscription_queryset = OrganizationSubscription.objects.filter(
        is_deleted=False,
        is_current=True,
    ).select_related("plan")

    upcoming_subscription_queryset = (
        OrganizationSubscription.objects.filter(
            is_deleted=False,
            status=SubscriptionStatus.SCHEDULED,
            is_current=False,
        )
        .select_related("plan")
        .order_by(
            "start_date",
            "created_at",
        )
    )

    contact_queryset = OrganizationContact.objects.filter(
        is_deleted=False,
    ).order_by(
        "-is_primary",
        "name",
    )

    social_account_queryset = (
        Organization.social_accounts.rel.related_model.objects.filter(
            is_deleted=False,
        ).order_by(
            "platform",
            "account_name",
        )
    )

    return Organization.objects.filter(
        is_deleted=False,
    ).prefetch_related(
        Prefetch(
            "contacts",
            queryset=contact_queryset,
            to_attr="prefetched_contacts",
        ),
        Prefetch(
            "social_accounts",
            queryset=social_account_queryset,
            to_attr="prefetched_social_accounts",
        ),
        Prefetch(
            "subscriptions",
            queryset=current_subscription_queryset,
            to_attr="prefetched_current_subscriptions",
        ),
        Prefetch(
            "subscriptions",
            queryset=upcoming_subscription_queryset,
            to_attr="prefetched_upcoming_subscriptions",
        ),
    )


def get_organizations(
    *,
    search=None,
    status=None,
    subscription_status=None,
    ordering="-created_at",
):
    """
    Return organizations with optional search and filters.

    Search is implemented using EXISTS for related contacts
    to avoid expensive JOIN + DISTINCT operations.
    """

    queryset = organization_queryset()

    # =========================================================
    # SEARCH
    # =========================================================

    if search:
        search = search.strip()

        if search:
            matching_contact = OrganizationContact.objects.filter(
                organization_id=OuterRef("pk"),
                is_deleted=False,
            ).filter(Q(name__icontains=search) | Q(email__icontains=search))

            queryset = queryset.annotate(
                has_matching_contact=Exists(
                    matching_contact,
                ),
            ).filter(
                Q(name__icontains=search)
                | Q(organization_id__icontains=search)
                | Q(industry__icontains=search)
                | Q(has_matching_contact=True)
            )

    # =========================================================
    # ORGANIZATION STATUS
    # =========================================================

    if status:
        queryset = queryset.filter(
            status=status,
        )

    # =========================================================
    # SUBSCRIPTION STATUS
    # =========================================================

    if subscription_status:
        matching_subscription = OrganizationSubscription.objects.filter(
            organization_id=OuterRef("pk"),
            is_deleted=False,
            is_current=True,
            status=subscription_status,
        )

        queryset = queryset.filter(
            Exists(matching_subscription),
        )

    # =========================================================
    # ORDERING
    # =========================================================

    allowed_ordering = {
        "created_at": "created_at",
        "-created_at": "-created_at",
        "name": "name",
        "-name": "-name",
    }

    return queryset.order_by(
        allowed_ordering.get(
            ordering,
            "-created_at",
        )
    )


def get_organization_by_id(
    organization_id,
):
    """
    Return a single non-deleted organization
    using the public organization identifier.
    """

    return (
        organization_queryset()
        .filter(
            organization_id=organization_id,
        )
        .first()
    )


def get_organization_summary():
    """
    Return global aggregate metrics used by the
    Organization list page.

    These counts are intentionally calculated without
    applying search or status filters so tab counts and
    dashboard statistics remain globally consistent.
    """

    queryset = Organization.objects.filter(
        is_deleted=False,
    )

    total_clients = queryset.count()

    active_organizations = queryset.filter(
        status="ACTIVE",
    ).count()

    inactive_organizations = queryset.filter(
        status="INACTIVE",
    ).count()

    connected_accounts = (
        queryset.filter(
            social_accounts__is_deleted=False,
            social_accounts__status="connected",
        ).aggregate(
            total=Count(
                "social_accounts",
                distinct=True,
            )
        )[
            "total"
        ]
        or 0
    )

    active_subscriptions = (
        queryset.filter(
            subscriptions__is_current=True,
            subscriptions__status=SubscriptionStatus.ACTIVE,
            subscriptions__is_deleted=False,
        )
        .distinct()
        .count()
    )

    return {
        "total_clients": total_clients,
        "active_organizations": active_organizations,
        "inactive_organizations": inactive_organizations,
        "connected_accounts": connected_accounts,
        "active_subscriptions": active_subscriptions,
    }


def get_subscription_history(
    *,
    organization,
):
    """
    Return all subscription records for an organization.

    Current and historical subscriptions are returned,
    newest period first.
    """

    return (
        organization.subscriptions.select_related("plan")
        .filter(
            is_deleted=False,
        )
        .order_by(
            "-start_date",
            "-created_at",
        )
    )
