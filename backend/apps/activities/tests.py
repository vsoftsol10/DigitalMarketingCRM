from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.posts.models import Post

from .models import ActivityEventType, ActivityLog, ActivitySource


class ActivityLogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="activity-owner@example.com",
            first_name="Activity",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-ACTIVITY",
            name="Activity Organization",
            slug="activity-organization",
            industry="Retail",
            created_by=self.user,
        )

    def test_activity_log_persists_organization_actor_and_metadata(self):
        occurred_at = timezone.now() - timedelta(minutes=5)

        activity = ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.ORGANIZATION_CREATED,
            actor=self.user,
            source=ActivitySource.USER,
            occurred_at=occurred_at,
            metadata={"organization_name": self.organization.name},
        )

        activity.refresh_from_db()
        self.assertEqual(activity.organization, self.organization)
        self.assertEqual(activity.actor, self.user)
        self.assertEqual(activity.source, ActivitySource.USER)
        self.assertEqual(activity.occurred_at, occurred_at)
        self.assertEqual(activity.metadata["organization_name"], self.organization.name)

    def test_nonempty_idempotency_key_is_unique_for_active_logs(self):
        ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_PUBLISHED,
            idempotency_key="post-target-1:published",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ActivityLog.objects.create(
                    organization=self.organization,
                    event_type=ActivityEventType.POST_PUBLISHED,
                    idempotency_key="post-target-1:published",
                )

    def test_empty_idempotency_keys_do_not_conflict(self):
        ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_CREATED,
        )
        ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_SCHEDULED,
        )

        self.assertEqual(ActivityLog.objects.count(), 2)

    def test_ordering_uses_occurred_at_then_id(self):
        earlier = ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_CREATED,
            occurred_at=timezone.now() - timedelta(minutes=1),
        )
        later = ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_SCHEDULED,
            occurred_at=timezone.now(),
        )

        self.assertEqual(list(ActivityLog.objects.all()), [later, earlier])

    def test_log_is_retained_when_related_post_is_soft_deleted(self):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="Historical activity post",
        )
        activity = ActivityLog.objects.create(
            organization=self.organization,
            event_type=ActivityEventType.POST_CREATED,
            post=post,
        )

        post.soft_delete()
        activity.refresh_from_db()

        self.assertTrue(post.is_deleted)
        self.assertEqual(activity.post_id, post.id)
