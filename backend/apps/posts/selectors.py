from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db.models import Prefetch, Q

from .models import Post, PostMedia, PostPlatform


CALENDAR_VISIBLE_STATUSES = {
    "DRAFT",
    "SCHEDULED",
    "PUBLISHING",
    "UNRESOLVED",
    "PUBLISHED",
    "FAILED",
}


def get_calendar_event_status(target):
    """Return the calendar status for one exact publishing destination."""

    # Calendar represents this exact PostPlatform destination. Aggregate post
    # state must never overwrite a sibling target's lifecycle state.
    return (target.status or target.post.status or "").upper()


def get_calendar_event_datetime(target):
    """Choose the lifecycle timestamp represented by a calendar event."""

    status = get_calendar_event_status(target)
    post = target.post

    if status == "SCHEDULED":
        return target.scheduled_at or post.scheduled_at
    if status == "PUBLISHED":
        return target.published_at or post.published_at
    if status == "FAILED":
        return target.published_at or post.published_at or post.scheduled_at or post.created_at
    return post.created_at


def get_calendar_event_local_datetime(target):
    event_datetime = get_calendar_event_datetime(target)
    if not event_datetime:
        return None
    try:
        return event_datetime.astimezone(
            ZoneInfo(target.scheduled_timezone or target.post.timezone or "UTC")
        )
    except ZoneInfoNotFoundError:
        return event_datetime.astimezone(ZoneInfo("UTC"))


def get_calendar_events(*, user, month=None, search="", organization_id="", social_account_id="", content_type="", status=""):
    """Return owned PostPlatform rows with all data needed by Calendar."""

    media_queryset = PostMedia.objects.filter(is_deleted=False).order_by("sort_order")
    queryset = (
        PostPlatform.objects.filter(
            is_deleted=False,
            post__is_deleted=False,
            post__organization__created_by=user,
        )
        .select_related("post", "post__organization", "social_account")
        .prefetch_related(Prefetch("post__media", queryset=media_queryset))
    )

    if organization_id:
        queryset = queryset.filter(post__organization__organization_id=organization_id)
    if social_account_id:
        queryset = queryset.filter(social_account_id=social_account_id)
    if content_type:
        queryset = queryset.filter(content_type__iexact=content_type)
    if search:
        queryset = queryset.filter(
            Q(post__caption__icontains=search)
            | Q(post__organization__name__icontains=search)
            | Q(social_account__account_name__icontains=search)
            | Q(social_account__username__icontains=search)
            | Q(platform__icontains=search)
            | Q(content_type__icontains=search)
        )

    targets = list(queryset.order_by("post__created_at", "created_at"))
    requested_status = status.upper()
    targets = [
        target
        for target in targets
        if (not requested_status or get_calendar_event_status(target) == requested_status)
    ]

    if month:
        try:
            month_start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        except ValueError:
            return []
        targets = [
            target
            for target in targets
            if (event_datetime := get_calendar_event_local_datetime(target))
            and event_datetime.date().year == month_start.year
            and event_datetime.date().month == month_start.month
        ]

    return sorted(
        targets,
        key=lambda target: (
            get_calendar_event_local_datetime(target) is None,
            get_calendar_event_local_datetime(target),
            str(target.id),
        ),
    )

# ============================================================
# GET CALENDAR EVENT BY TARGET ID
# ============================================================
def get_calendar_event_by_target_id(*, user, target_id):
    """Return one owned Calendar target with the list endpoint's related data."""

    media_queryset = PostMedia.objects.filter(is_deleted=False).order_by("sort_order")
    return (
        PostPlatform.objects.filter(
            id=target_id,
            is_deleted=False,
            post__is_deleted=False,
            post__organization__created_by=user,
        )
        .select_related("post", "post__organization", "social_account")
        .prefetch_related(Prefetch("post__media", queryset=media_queryset))
        .first()
    )


# ============================================================
# GET POSTS FOR ORGANIZATION
# ============================================================


def get_posts_for_organization(
    organization_id,
):
    """
    Return all active posts belonging to an organization.

    Only active PostPlatform and PostMedia records are prefetched.
    """

    active_platforms = PostPlatform.objects.filter(
        is_deleted=False,
    ).select_related(
        "social_account",
        "social_account__connection",
    )

    active_media = PostMedia.objects.filter(
        is_deleted=False,
    )

    return (
        Post.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        )
        .select_related(
            "organization",
            "created_by",
        )
        .prefetch_related(
            Prefetch(
                "platforms",
                queryset=active_platforms,
            ),
            Prefetch(
                "media",
                queryset=active_media,
            ),
        )
        .order_by(
            "-created_at",
        )
    )


# ============================================================
# GET SINGLE POST
# ============================================================


def get_post_by_id(
    *,
    post_id,
    organization_id,
):
    """
    Return a single active post belonging to the given
    organization.

    Organization filtering is mandatory to maintain tenant
    isolation.
    """

    active_platforms = PostPlatform.objects.filter(
        is_deleted=False,
    ).select_related(
        "social_account",
        "social_account__connection",
    )

    active_media = PostMedia.objects.filter(
        is_deleted=False,
    )

    return (
        Post.objects.filter(
            id=post_id,
            organization_id=organization_id,
            is_deleted=False,
        )
        .select_related(
            "organization",
            "created_by",
        )
        .prefetch_related(
            Prefetch(
                "platforms",
                queryset=active_platforms,
            ),
            Prefetch(
                "media",
                queryset=active_media,
            ),
        )
        .first()
    )
