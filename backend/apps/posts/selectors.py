from django.db.models import Prefetch

from .models import Post, PostMedia, PostPlatform

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
