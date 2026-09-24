from django.db.models import Count, Q
from django.utils import timezone

from apps.organizations.models import Organization

from .models import ContentIdea


def content_idea_queryset(*, user):
    """
    Base queryset for Content Planner read operations.

    Excludes soft-deleted ideas and soft-deleted organizations.
    Organization is loaded in the same query to avoid unnecessary
    database queries when serializing the organization name.
    """

    return ContentIdea.objects.filter(
        is_deleted=False,
        organization__is_deleted=False,
        organization__created_by=user,
    ).select_related("organization").prefetch_related("selected_social_accounts")


def get_content_ideas(
    *,
    search=None,
    organization_id=None,
    user,
):
    """
    Return content ideas with optional search and organization filters.
    """

    queryset = content_idea_queryset(user=user)

    # =========================================================
    # SEARCH
    # =========================================================

    if search:
        search = search.strip()

        if search:
            queryset = queryset.filter(
                Q(caption__icontains=search)
                | Q(description__icontains=search)
                | Q(organization__name__icontains=search)
                | Q(content_type__icontains=search)
            )

    # =========================================================
    # ORGANIZATION FILTER
    # =========================================================

    if organization_id and organization_id != "all":
        queryset = queryset.filter(
            organization_id=organization_id,
        )

    # =========================================================
    # ORDERING
    # =========================================================

    return queryset.order_by(
        "target_publish_date",
        "-created_at",
    )


def get_content_idea_by_id(
    *,
    idea_id,
    user,
):
    """
    Return a single non-deleted content idea.
    """

    return (
        content_idea_queryset(user=user)
        .filter(
            id=idea_id,
        )
        .first()
    )


def get_content_planner_organizations(*, user):
    """
    Return active organizations for the Content Planner
    organization filter and create/edit forms.

    Only organizations with is_deleted=False are returned.
    """

    return (
        Organization.objects.filter(
            is_deleted=False,
            created_by=user,
        )
        .order_by("name")
        .values(
            "id",
            "organization_id",
            "name",
        )
    )


def get_content_planner_statistics(*, user):
    """
    Return Content Planner dashboard statistics.

    Statistics:
    - total_ideas:
        Total non-deleted content ideas.

    - planned_this_month:
        Content ideas whose target publish date falls inside
        the current calendar month.

    - using_content_planner:
        Active organizations with at least one non-deleted
        content idea.

    - not_using_content_planner:
        Active organizations that do not have any non-deleted
        content ideas.
    """

    today = timezone.localdate()

    month_start = today.replace(
        day=1,
    )

    if today.month == 12:
        next_month_start = today.replace(
            year=today.year + 1,
            month=1,
            day=1,
        )
    else:
        next_month_start = today.replace(
            month=today.month + 1,
            day=1,
        )

    total_ideas = ContentIdea.objects.filter(
        is_deleted=False,
        organization__is_deleted=False,
        organization__created_by=user,
    ).count()

    planned_this_month = ContentIdea.objects.filter(
        is_deleted=False,
        organization__is_deleted=False,
        organization__created_by=user,
        target_publish_date__gte=month_start,
        target_publish_date__lt=next_month_start,
    ).count()

    organization_statistics = Organization.objects.filter(
        is_deleted=False,
        created_by=user,
    ).annotate(
        active_content_ideas=Count(
            "content_ideas",
            filter=Q(
                content_ideas__is_deleted=False,
            ),
            distinct=True,
        )
    )

    using_content_planner = organization_statistics.filter(
        active_content_ideas__gt=0,
    ).count()

    not_using_content_planner = organization_statistics.filter(
        active_content_ideas=0,
    ).count()

    return {
        "total_ideas": total_ideas,
        "planned_this_month": planned_this_month,
        "using_content_planner": using_content_planner,
        "not_using_content_planner": not_using_content_planner,
    }
