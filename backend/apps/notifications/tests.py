from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.activities.models import ActivityEventType, ActivitySource
from apps.activities.services import create_activity_log
from apps.dashboard.selectors import get_dashboard_data
from apps.organizations.models import (
    BillingCycle,
    Organization,
    OrganizationSubscription,
    SubscriptionStatus,
)
from apps.organizations.services import renew_subscription, start_new_subscription
from apps.organizations.subscription_service import expire_due_subscriptions
from apps.organizations.tasks import send_plan_expiry_reminders_task
from apps.plans.models import Plan
from apps.posts.models import Post, PostPlatform, PostStatus, SocialPlatform

from .models import UserNotification, UserNotificationType


class UserNotificationLifecycleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="notification-owner@example.com",
            first_name="Notification",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-NOTIFICATION",
            name="Notification Organization",
            slug="notification-organization",
            industry="Retail",
            created_by=self.user,
        )
        self.plan = Plan.objects.create(
            name="Notification Plan",
            code="notification-plan",
            plan_type="standard",
            description="Plan for notification tests.",
        )
        self.post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="A notification test post",
        )
        self.target = PostPlatform.objects.create(
            post=self.post,
            platform=SocialPlatform.FACEBOOK,
            content_type="POST",
            status=PostStatus.FAILED,
        )
        self.client.force_authenticate(self.user)

    def create_activity(self, *, event_type, key, target=None, subscription=None):
        return create_activity_log(
            organization=self.organization,
            post=self.post if target else None,
            post_platform=target,
            subscription=subscription,
            event_type=event_type,
            source=ActivitySource.SYSTEM,
            idempotency_key=key,
        )

    def test_failed_post_is_idempotent_action_and_reopened_on_new_failure(self):
        activity = self.create_activity(
            event_type=ActivityEventType.POST_FAILED,
            key=f"post-platform:{self.target.id}:failed:1",
            target=self.target,
        )
        self.create_activity(
            event_type=ActivityEventType.POST_FAILED,
            key=f"post-platform:{self.target.id}:failed:1",
            target=self.target,
        )
        notification = UserNotification.objects.get(
            event_type=UserNotificationType.FAILED_POST,
        )
        self.assertEqual(UserNotification.objects.count(), 1)
        self.assertEqual(notification.source_activity, activity)
        self.assertEqual(notification.post_platform, self.target)
        self.assertEqual(
            [item["target_id"] for item in get_dashboard_data(user=self.user)["notifications"]],
            [self.target.id],
        )

        self.client.post(f"/api/notifications/{notification.id}/read/")
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

        self.target.status = PostStatus.PUBLISHING
        self.target.save(update_fields=["status", "updated_at"])
        self.assertEqual(
            [item["target_id"] for item in get_dashboard_data(user=self.user)["notifications"]],
            [self.target.id],
        )
        self.target.status = PostStatus.FAILED
        self.target.save(update_fields=["status", "updated_at"])
        self.create_activity(
            event_type=ActivityEventType.POST_FAILED,
            key=f"post-platform:{self.target.id}:failed:2",
            target=self.target,
        )
        notification.refresh_from_db()
        self.assertEqual(UserNotification.objects.filter(event_type=UserNotificationType.FAILED_POST).count(), 1)
        self.assertIsNone(notification.read_at)
        self.assertIsNone(notification.resolved_at)

    def test_successful_publish_resolves_failure_and_creates_one_success_notification(self):
        self.create_activity(
            event_type=ActivityEventType.POST_FAILED,
            key=f"post-platform:{self.target.id}:failed:1",
            target=self.target,
        )
        self.target.status = PostStatus.PUBLISHED
        self.target.save(update_fields=["status", "updated_at"])

        self.create_activity(
            event_type=ActivityEventType.POST_PUBLISHED,
            key=f"post-platform:{self.target.id}:published:1",
            target=self.target,
        )
        self.create_activity(
            event_type=ActivityEventType.POST_PUBLISHED,
            key=f"post-platform:{self.target.id}:published:1",
            target=self.target,
        )

        failure = UserNotification.objects.get(event_type=UserNotificationType.FAILED_POST)
        published = UserNotification.objects.get(event_type=UserNotificationType.POST_PUBLISHED)
        self.assertIsNotNone(failure.resolved_at)
        self.assertEqual(published.title, "Post Published")
        self.assertEqual(published.post_platform, self.target)
        self.assertEqual(UserNotification.objects.filter(event_type=UserNotificationType.POST_PUBLISHED).count(), 1)
        self.assertTrue(UserNotification.objects.filter(id=failure.id).exists())
        response = self.client.get("/api/notifications/")
        self.assertEqual(
            [item["type"] for item in response.data["data"]["notifications"]],
            [UserNotificationType.POST_PUBLISHED],
        )
        self.assertEqual(get_dashboard_data(user=self.user)["notifications"], [])

    def test_expired_subscription_is_actionable_then_activation_resolves_it(self):
        self.target.status = PostStatus.PUBLISHED
        self.target.save(update_fields=["status", "updated_at"])
        subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() - timedelta(days=1),
        )
        self.assertEqual(expire_due_subscriptions(), 1)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, SubscriptionStatus.EXPIRED)

        self.assertEqual(
            [item["type"] for item in get_dashboard_data(user=self.user)["notifications"]],
            ["SUBSCRIPTION_EXPIRED"],
        )
        expired_notification = UserNotification.objects.get(
            event_type=UserNotificationType.SUBSCRIPTION_EXPIRED,
        )
        self.assertEqual(expired_notification.subscription, subscription)

        active = start_new_subscription(
            organization=self.organization,
            plan=self.plan,
            billing_cycle=BillingCycle.MONTHLY,
            actor=self.user,
        )
        expired_notification.refresh_from_db()
        activation = UserNotification.objects.get(
            event_type=UserNotificationType.SUBSCRIPTION_ACTIVATED,
        )
        self.assertIsNotNone(expired_notification.resolved_at)
        self.assertEqual(activation.subscription, active)
        self.assertEqual(activation.title, "Subscription Activated")
        self.assertEqual(get_dashboard_data(user=self.user)["notifications"], [])

    def test_immediate_renewal_creates_header_notification_synchronously(self):
        self.target.status = PostStatus.PUBLISHED
        self.target.save(update_fields=["status", "updated_at"])
        expired_subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.EXPIRED,
            is_current=False,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() - timedelta(days=1),
        )
        self.create_activity(
            event_type=ActivityEventType.SUBSCRIPTION_EXPIRED,
            key=f"subscription:{expired_subscription.id}:expired",
            subscription=expired_subscription,
        )

        renewed_subscription = renew_subscription(
            organization=self.organization,
            actor=self.user,
        )

        activation = UserNotification.objects.get(
            event_type=UserNotificationType.SUBSCRIPTION_ACTIVATED,
        )
        self.assertEqual(activation.subscription, renewed_subscription)
        self.assertIsNotNone(
            UserNotification.objects.get(
                event_type=UserNotificationType.SUBSCRIPTION_EXPIRED,
            ).resolved_at
        )
        response = self.client.get("/api/notifications/")
        self.assertEqual(
            [item["type"] for item in response.data["data"]["notifications"]],
            [UserNotificationType.SUBSCRIPTION_ACTIVATED],
        )

    def test_expiry_reminder_task_records_header_notification_without_email_recipient(self):
        subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=3),
        )
        with patch(
            "apps.organizations.tasks.get_organization_billing_recipient",
            return_value=("", ""),
        ):
            send_plan_expiry_reminders_task.run()

        notification = UserNotification.objects.get()
        self.assertEqual(notification.event_type, UserNotificationType.SUBSCRIPTION_EXPIRING)
        self.assertEqual(notification.subscription, subscription)

    def test_expiring_soon_is_header_only_and_get_does_not_create_duplicates(self):
        subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=3),
        )
        self.create_activity(
            event_type=ActivityEventType.SUBSCRIPTION_EXPIRING,
            key=f"subscription:{subscription.id}:expiring",
            subscription=subscription,
        )

        dashboard = get_dashboard_data(user=self.user)
        self.assertFalse(
            any(item["type"] == "SUBSCRIPTION_EXPIRING" for item in dashboard["notifications"])
        )
        first = self.client.get("/api/notifications/")
        second = self.client.get("/api/notifications/")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["data"]["unread_count"], 1)
        self.assertEqual(second.data["data"]["unread_count"], 1)
        self.assertEqual(UserNotification.objects.count(), 1)

    def test_read_state_persists_and_read_notification_is_not_unread_after_reload(self):
        self.create_activity(
            event_type=ActivityEventType.POST_FAILED,
            key=f"post-platform:{self.target.id}:failed:1",
            target=self.target,
        )
        notification = UserNotification.objects.get()

        response = self.client.get("/api/notifications/")
        self.assertEqual(response.data["data"]["notifications"][0]["is_read"], False)
        marked = self.client.post(f"/api/notifications/{notification.id}/read/")
        self.assertEqual(marked.status_code, 200)
        reloaded = self.client.get("/api/notifications/")
        self.assertEqual(reloaded.data["data"]["notifications"], [])
        self.assertEqual(reloaded.data["data"]["unread_count"], 0)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
        self.assertIsNone(notification.resolved_at)

    def test_empty_notification_center_returns_zero_unread(self):
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["notifications"], [])
        self.assertEqual(response.data["data"]["unread_count"], 0)

    def test_read_endpoint_cannot_change_another_users_notification(self):
        other_user = User.objects.create_user(
            email="notification-other@example.com",
            first_name="Other",
            password="password",
        )
        notification = UserNotification.objects.create(
            recipient=other_user,
            organization=self.organization,
            post_platform=self.target,
            event_type=UserNotificationType.FAILED_POST,
            event_key=f"other-user-failure:{self.target.id}",
            title="Failed Post",
            message="Publishing failed.",
        )

        response = self.client.post(f"/api/notifications/{notification.id}/read/")
        notification.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(notification.read_at)
