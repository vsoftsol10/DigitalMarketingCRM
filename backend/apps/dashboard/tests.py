from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.activities.models import ActivityEventType, ActivityLog, ActivitySource
from apps.organizations.models import Organization, OrganizationSubscription, SubscriptionStatus
from apps.plans.models import Plan
from apps.posts.models import Post, PostPlatform, PostStatus, SocialPlatform
from apps.social_accounts.models import SocialAccount, SocialAccountStatus


class DashboardAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="dashboard-owner@example.com",
            first_name="Dashboard",
            password="password",
        )
        self.other_user = User.objects.create_user(
            email="dashboard-other@example.com",
            first_name="Other",
            password="password",
        )
        self.organization = self.create_organization(self.user, "ORG-DASHBOARD", "Dashboard Org")
        self.other_organization = self.create_organization(self.other_user, "ORG-OTHER", "Other Org")
        self.plan = Plan.objects.create(
            name="Dashboard Plan",
            code="dashboard-plan",
            plan_type="standard",
            description="Dashboard test plan",
        )
        self.account = self.create_account(self.organization, "dashboard-account")
        self.other_account = self.create_account(self.other_organization, "other-account")

    def create_organization(self, user, organization_id, name):
        return Organization.objects.create(
            organization_id=organization_id,
            name=name,
            slug=organization_id.lower(),
            industry="Retail",
            created_by=user,
        )

    def create_account(self, organization, account_id, *, connected=True):
        return SocialAccount.objects.create(
            organization=organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id=account_id,
            account_name=account_id,
            status=SocialAccountStatus.CONNECTED if connected else SocialAccountStatus.DISCONNECTED,
            is_valid=connected,
        )

    def create_target(self, organization, account, status, **target_fields):
        post = Post.objects.create(
            organization=organization,
            created_by=organization.created_by,
            caption="Dashboard target caption",
            status=status,
        )
        return PostPlatform.objects.create(
            post=post,
            social_account=account,
            platform=SocialPlatform.FACEBOOK,
            content_type="POST",
            status=status,
            **target_fields,
        )

    def get_dashboard(self):
        self.client.force_authenticate(self.user)
        return self.client.get("/api/dashboard/")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_receives_dashboard(self):
        response = self.get_dashboard()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["recent_activities"], [])

    def test_organization_and_social_account_counts_are_owner_scoped(self):
        self.create_account(self.organization, "disconnected", connected=False)
        response = self.get_dashboard()
        statistics = response.data["data"]["statistics"]
        self.assertEqual(statistics["total_organizations"], 1)
        self.assertEqual(statistics["connected_social_accounts"], 1)

    def test_scheduled_and_published_target_counts_are_correct(self):
        now = timezone.now()
        self.create_target(
            self.organization, self.account, PostStatus.SCHEDULED,
            scheduled_at=now, scheduled_timezone="Asia/Kolkata",
        )
        self.create_target(
            self.organization, self.account, PostStatus.PUBLISHED,
            published_at=now, scheduled_timezone="Asia/Kolkata",
        )
        self.create_target(
            self.other_organization, self.other_account, PostStatus.SCHEDULED,
            scheduled_at=now, scheduled_timezone="Asia/Kolkata",
        )
        response = self.get_dashboard()
        data = response.data["data"]
        self.assertEqual(data["statistics"]["scheduled_posts_today"], 1)
        self.assertEqual(data["statistics"]["published_posts_today"], 1)
        self.assertEqual(len(data["today_schedule"]), 1)
        self.assertEqual(data["today_schedule"][0]["organization_id"], "ORG-DASHBOARD")

    def test_scheduled_targets_with_same_datetime_are_ordered_by_target_id(self):
        scheduled_at = timezone.now()
        first = self.create_target(
            self.organization,
            self.account,
            PostStatus.SCHEDULED,
            scheduled_at=scheduled_at,
            scheduled_timezone="Asia/Kolkata",
        )
        second = self.create_target(
            self.organization,
            self.account,
            PostStatus.SCHEDULED,
            scheduled_at=scheduled_at,
            scheduled_timezone="Asia/Kolkata",
        )

        response = self.get_dashboard()
        target_ids = [
            item["target_id"] for item in response.data["data"]["today_schedule"]
        ]

        self.assertEqual(target_ids, sorted([str(first.id), str(second.id)]))

    def test_failed_target_is_returned_but_unresolved_target_is_not(self):
        failed = self.create_target(
            self.organization, self.account, PostStatus.FAILED,
            error_message="Provider rejected the post.",
        )
        self.create_target(self.organization, self.account, PostStatus.UNRESOLVED)
        response = self.get_dashboard()
        notifications = response.data["data"]["notifications"]
        failed_notifications = [item for item in notifications if item["type"] == "FAILED_POST"]
        self.assertEqual(len(failed_notifications), 1)
        self.assertEqual(failed_notifications[0]["target_id"], str(failed.id))

    def test_failed_notification_exposes_bounded_safe_display_fields(self):
        raw_provider_error = (
            "Provider rejected the post. fbtrace_id=secret-trace "
            "access_token=secret-token"
        )
        target = self.create_target(
            self.organization,
            self.account,
            PostStatus.FAILED,
            error_message=raw_provider_error,
        )
        target.post.caption = "  First line\n\n" + ("post preview " * 40)
        target.post.save(update_fields=["caption", "updated_at"])

        response = self.get_dashboard()
        notification = next(
            item
            for item in response.data["data"]["notifications"]
            if item["type"] == "FAILED_POST" and item["target_id"] == str(target.id)
        )

        self.assertTrue(notification["post_title"].startswith("First line post preview"))
        self.assertLessEqual(len(notification["post_title"]), 80)
        self.assertLessEqual(len(notification["post_preview"]), 160)
        self.assertEqual(
            notification["failure_reason"],
            "Publishing failed. Review the target and retry it from Calendar.",
        )
        self.assertEqual(notification["message"], notification["failure_reason"])
        self.assertEqual(notification["error_message"], notification["failure_reason"])
        self.assertNotIn("fbtrace_id", str(notification))
        self.assertNotIn("secret-token", str(notification))

    def test_deleted_social_account_is_excluded_from_scheduled_and_failed_output(self):
        scheduled = self.create_target(
            self.organization,
            self.account,
            PostStatus.SCHEDULED,
            scheduled_at=timezone.now(),
            scheduled_timezone="Asia/Kolkata",
        )
        failed = self.create_target(
            self.organization,
            self.account,
            PostStatus.FAILED,
            error_message="Account was deleted.",
        )
        self.account.soft_delete()

        response = self.get_dashboard()
        data = response.data["data"]
        self.assertNotIn(
            str(scheduled.id),
            [item["target_id"] for item in data["today_schedule"]],
        )
        self.assertNotIn(
            str(failed.id),
            [
                item["target_id"]
                for item in data["notifications"]
                if item["type"] == "FAILED_POST"
            ],
        )

    def test_cross_organization_social_account_metadata_is_not_exposed(self):
        scheduled = self.create_target(
            self.organization,
            self.other_account,
            PostStatus.SCHEDULED,
            scheduled_at=timezone.now(),
            scheduled_timezone="Asia/Kolkata",
        )
        failed = self.create_target(
            self.organization,
            self.other_account,
            PostStatus.FAILED,
            error_message="Cross-organization target.",
        )

        response = self.get_dashboard()
        data = response.data["data"]
        scheduled_item = next(
            item for item in data["today_schedule"] if item["target_id"] == str(scheduled.id)
        )
        failed_item = next(
            item
            for item in data["notifications"]
            if item["type"] == "FAILED_POST" and item["target_id"] == str(failed.id)
        )
        self.assertEqual(scheduled_item["social_account"], "")
        self.assertEqual(failed_item["social_account"], "")

    def test_notifications_are_bounded_and_deterministically_ordered(self):
        targets = [
            self.create_target(
                self.organization,
                self.account,
                PostStatus.FAILED,
                error_message=f"Failure {index}",
            )
            for index in range(21)
        ]
        base_time = timezone.now()
        for index, target in enumerate(targets):
            PostPlatform.objects.filter(id=target.id).update(
                updated_at=base_time + timedelta(minutes=index),
            )

        response = self.get_dashboard()
        failed_notifications = [
            item
            for item in response.data["data"]["notifications"]
            if item["type"] == "FAILED_POST"
        ]
        self.assertEqual(len(failed_notifications), 20)
        self.assertEqual(
            failed_notifications[0]["target_id"],
            str(targets[-1].id),
        )
        self.assertNotIn(
            str(targets[0].id),
            [item["target_id"] for item in failed_notifications],
        )

    def test_recent_activities_are_owner_scoped_ordered_and_serialized(self):
        oldest = ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.ORGANIZATION_CREATED,
            source=ActivitySource.USER,
            actor=self.user,
            occurred_at=timezone.now() - timedelta(minutes=2),
            metadata={"organization_name": self.organization.name},
        )
        newest = ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_SCHEDULED,
            source=ActivitySource.USER,
            actor=self.user,
            occurred_at=timezone.now() - timedelta(minutes=1),
            metadata={
                "schedule_scope": "POST",
                "provider_payload": {"access_token": "must-not-leak"},
            },
        )
        ActivityLog.objects.create(
            organization=self.other_organization,
            event_type=ActivityEventType.POST_CREATED,
            source=ActivitySource.USER,
            actor=self.other_user,
        )

        response = self.get_dashboard()

        activities = response.data["data"]["recent_activities"]
        self.assertEqual([item["id"] for item in activities], [str(newest.id), str(oldest.id)])
        self.assertEqual(activities[0]["organization_id"], self.organization.organization_id)
        self.assertEqual(activities[0]["organization_name"], self.organization.name)
        self.assertEqual(activities[0]["actor_name"], self.user.full_name)
        self.assertEqual(activities[0]["actor_email"], self.user.email)
        self.assertEqual(activities[0]["metadata"], {"schedule_scope": "POST"})

    def test_recent_activities_are_bounded_and_support_missing_actor(self):
        base_time = timezone.now()
        activities = [
            ActivityLog.objects.create(
                organization=self.organization,
                event_type=ActivityEventType.POST_PUBLISHED,
                source=ActivitySource.SYSTEM,
                occurred_at=base_time + timedelta(minutes=index),
            )
            for index in range(11)
        ]

        response = self.get_dashboard()

        recent_activities = response.data["data"]["recent_activities"]
        self.assertEqual(len(recent_activities), 10)
        self.assertEqual(recent_activities[0]["id"], str(activities[-1].id))
        self.assertNotIn(str(activities[0].id), [item["id"] for item in recent_activities])
        self.assertEqual(recent_activities[0]["actor_name"], "")
        self.assertEqual(recent_activities[0]["actor_email"], "")

    def test_recent_activity_includes_safe_related_display_fields(self):
        scheduled_at = timezone.now() + timedelta(days=1)
        published_at = timezone.now()
        target = self.create_target(
            self.organization,
            self.account,
            PostStatus.PUBLISHED,
            scheduled_at=scheduled_at,
            published_at=published_at,
        )
        target.post.caption = "  Campaign launch\n\n" + ("preview " * 40)
        target.post.save(update_fields=["caption", "updated_at"])
        subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=30),
        )
        activity = ActivityLog.objects.create(
            organization=self.organization,
            post=target.post,
            post_platform=target,
            subscription=subscription,
            event_type=ActivityEventType.POST_PUBLISHED,
            source=ActivitySource.SYSTEM,
            occurred_at=timezone.now(),
            metadata={"scheduled_at": scheduled_at.isoformat()},
        )

        response = self.get_dashboard()
        item = next(
            activity_item
            for activity_item in response.data["data"]["recent_activities"]
            if activity_item["id"] == str(activity.id)
        )

        self.assertTrue(item["post_title"].startswith("Campaign launch preview"))
        self.assertLessEqual(len(item["post_title"]), 80)
        self.assertLessEqual(len(item["post_preview"]), 160)
        self.assertEqual(item["platform"], "FACEBOOK")
        self.assertEqual(item["social_account"], self.account.account_name)
        self.assertEqual(item["scheduled_at"], scheduled_at.isoformat().replace("+00:00", "Z"))
        self.assertEqual(item["published_at"], published_at.isoformat().replace("+00:00", "Z"))
        self.assertEqual(item["plan_name"], self.plan.name)
        self.assertEqual(item["expiry_date"], subscription.expiry_date.isoformat())

    def test_recent_activity_hides_deleted_plan_name(self):
        subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=30),
        )
        activity = ActivityLog.objects.create(
            organization=self.organization,
            subscription=subscription,
            event_type=ActivityEventType.SUBSCRIPTION_ACTIVATED,
            source=ActivitySource.USER,
        )
        self.plan.soft_delete()

        response = self.get_dashboard()
        item = next(
            activity_item
            for activity_item in response.data["data"]["recent_activities"]
            if activity_item["id"] == str(activity.id)
        )

        self.assertEqual(item["plan_name"], "")
        self.assertEqual(item["expiry_date"], subscription.expiry_date.isoformat())

    def test_deleted_related_post_does_not_prevent_activity_display(self):
        target = self.create_target(
            self.organization,
            self.account,
            PostStatus.DRAFT,
        )
        activity = ActivityLog.objects.create(
            organization=self.organization,
            post=target.post,
            post_platform=target,
            event_type=ActivityEventType.POST_CREATED,
            source=ActivitySource.USER,
            actor=self.user,
        )
        target.post.soft_delete()
        target.soft_delete()

        response = self.get_dashboard()

        self.assertIn(
            str(activity.id),
            [item["id"] for item in response.data["data"]["recent_activities"]],
        )

    def test_active_subscription_hides_historical_expired_notification(self):
        active_subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=3),
        )
        expired_subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.EXPIRED,
            is_current=False,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() - timedelta(days=1),
        )

        response = self.get_dashboard()
        notifications = response.data["data"]["notifications"]

        self.assertIn(
            f"subscription-expiring:{active_subscription.id}",
            [item["id"] for item in notifications],
        )
        expiring_notification = next(
            item
            for item in notifications
            if item["id"] == f"subscription-expiring:{active_subscription.id}"
        )
        self.assertEqual(expiring_notification["days_remaining"], 3)
        self.assertNotIn(
            f"subscription-expired:{expired_subscription.id}",
            [item["id"] for item in notifications],
        )

    def test_only_latest_expired_subscription_is_returned_without_active_subscription(self):
        older_subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.EXPIRED,
            is_current=False,
            start_date=timezone.localdate() - timedelta(days=90),
            expiry_date=timezone.localdate() - timedelta(days=60),
        )
        latest_subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.EXPIRED,
            is_current=False,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() - timedelta(days=1),
        )

        response = self.get_dashboard()
        expired_notifications = [
            notification
            for notification in response.data["data"]["notifications"]
            if notification["type"] == "SUBSCRIPTION_EXPIRED"
        ]

        self.assertEqual(len(expired_notifications), 1)
        self.assertEqual(
            expired_notifications[0]["id"],
            f"subscription-expired:{latest_subscription.id}",
        )
        self.assertNotEqual(
            expired_notifications[0]["id"],
            f"subscription-expired:{older_subscription.id}",
        )

    def test_deleted_plan_metadata_is_not_exposed(self):
        subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            is_current=True,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=1),
        )
        self.plan.soft_delete()

        response = self.get_dashboard()
        notification = next(
            item
            for item in response.data["data"]["notifications"]
            if item["id"] == f"subscription-expiring:{subscription.id}"
        )
        self.assertEqual(notification["organization_id"], self.organization.organization_id)
        self.assertNotIn("plan_name", notification)
        self.assertNotIn(self.plan.name, notification["message"])
