from datetime import timedelta

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.organizations.models import OrganizationSubscription, SubscriptionStatus
from apps.posts.models import PostStatus

from .models import UserNotification, UserNotificationType


def _user_notification_queryset(*, user):
    today = timezone.localdate()
    active_current_subscription = OrganizationSubscription.objects.filter(
        organization_id=OuterRef("organization_id"),
        is_deleted=False,
        is_current=True,
        status=SubscriptionStatus.ACTIVE,
    )
    relevant_state = (
        Q(
            event_type=UserNotificationType.FAILED_POST,
            post_platform__isnull=False,
            post_platform__is_deleted=False,
            post_platform__post__is_deleted=False,
            post_platform__status=PostStatus.FAILED,
        )
        | Q(
            event_type=UserNotificationType.SUBSCRIPTION_EXPIRED,
            subscription__isnull=False,
            subscription__is_deleted=False,
            subscription__status=SubscriptionStatus.EXPIRED,
            has_active_subscription=False,
        )
        | Q(
            event_type=UserNotificationType.SUBSCRIPTION_EXPIRING,
            subscription__isnull=False,
            subscription__is_deleted=False,
            subscription__is_current=True,
            subscription__status=SubscriptionStatus.ACTIVE,
            subscription__expiry_date__gte=today,
            subscription__expiry_date__lte=today + timedelta(days=3),
        )
        | Q(
            event_type=UserNotificationType.POST_PUBLISHED,
            post_platform__isnull=False,
        )
        | Q(
            event_type=UserNotificationType.SUBSCRIPTION_ACTIVATED,
            subscription__isnull=False,
        )
    )

    queryset = (
        UserNotification.objects.filter(
            recipient=user,
            organization__created_by=user,
            organization__is_deleted=False,
            is_deleted=False,
            resolved_at__isnull=True,
            read_at__isnull=True,
        )
        .annotate(has_active_subscription=Exists(active_current_subscription))
        .filter(relevant_state)
        .filter(Q(read_at__isnull=True) | Q(created_at__gte=timezone.now() - timedelta(days=30)))
        .select_related(
            "organization",
            "post_platform__post",
            "post_platform__social_account",
            "subscription__plan",
        )
        .order_by("-created_at", "-id")
    )
    return queryset


def get_user_notifications(*, user, limit=50):
    """Return only owner-scoped, unresolved notifications still relevant now."""
    return _user_notification_queryset(user=user)[:limit]


def get_user_notification_unread_count(*, user):
    return _user_notification_queryset(user=user).filter(read_at__isnull=True).count()
