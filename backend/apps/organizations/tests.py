from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.activities.models import ActivityEventType, ActivityLog, ActivitySource
from apps.plans.models import Plan

from .models import (
    BillingCycle,
    Organization,
    OrganizationSubscription,
    SubscriptionScheduleType,
    SubscriptionStatus,
)
from .services import (
    activate_due_scheduled_subscriptions,
    cancel_subscription,
    create_organization,
    renew_subscription,
    start_new_subscription,
)


class OrganizationSubscriptionActivityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="organization-activity@example.com",
            first_name="Organization",
            password="password",
        )
        self.plan = Plan.objects.create(
            name="Activity Plan",
            code="activity-plan",
            plan_type="standard",
            description="Plan used by activity tests.",
        )

    def create_organization(self, suffix):
        return Organization.objects.create(
            organization_id=f"ORG-ACTIVITY-{suffix}",
            name=f"Activity Organization {suffix}",
            slug=f"activity-organization-{suffix}",
            industry="Retail",
            created_by=self.user,
        )

    def create_subscription(self, organization, **overrides):
        defaults = {
            "organization": organization,
            "plan": self.plan,
            "billing_cycle": BillingCycle.MONTHLY,
            "status": SubscriptionStatus.ACTIVE,
            "start_date": timezone.localdate() - timedelta(days=30),
            "expiry_date": timezone.localdate(),
            "is_current": True,
        }
        defaults.update(overrides)
        return OrganizationSubscription.objects.create(**defaults)

    def test_creation_records_organization_and_initial_subscription_activities(self):
        organization = create_organization(
            validated_data={
                "name": "Created Activity Organization",
                "industry": "Retail",
                "subscription_plan": self.plan,
                "billing_cycle": BillingCycle.MONTHLY,
            },
            created_by=self.user,
        )

        activities = ActivityLog.objects.filter(organization=organization)
        self.assertEqual(activities.count(), 2)
        self.assertTrue(
            activities.filter(
                event_type=ActivityEventType.ORGANIZATION_CREATED,
                source=ActivitySource.USER,
                actor=self.user,
            ).exists()
        )
        self.assertTrue(
            activities.filter(
                event_type=ActivityEventType.SUBSCRIPTION_ACTIVATED,
                source=ActivitySource.USER,
                actor=self.user,
                subscription__isnull=False,
            ).exists()
        )

    def test_start_subscription_records_user_activation(self):
        organization = self.create_organization("start")

        subscription = start_new_subscription(
            organization=organization,
            plan=self.plan,
            billing_cycle=BillingCycle.MONTHLY,
            actor=self.user,
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                organization=organization,
                subscription=subscription,
                event_type=ActivityEventType.SUBSCRIPTION_ACTIVATED,
                source=ActivitySource.USER,
                actor=self.user,
            ).exists()
        )

    def test_immediate_renewal_records_user_renewal(self):
        organization = self.create_organization("immediate-renewal")
        self.create_subscription(
            organization,
            status=SubscriptionStatus.EXPIRED,
            is_current=False,
            expiry_date=timezone.localdate() - timedelta(days=1),
        )

        renewed_subscription = renew_subscription(
            organization=organization,
            actor=self.user,
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                organization=organization,
                subscription=renewed_subscription,
                event_type=ActivityEventType.SUBSCRIPTION_RENEWED,
                source=ActivitySource.USER,
                actor=self.user,
            ).exists()
        )

    def test_scheduled_renewal_logs_only_when_system_activation_occurs(self):
        organization = self.create_organization("scheduled-renewal")
        self.create_subscription(organization)

        scheduled_subscription = renew_subscription(
            organization=organization,
            actor=self.user,
        )

        self.assertEqual(scheduled_subscription.status, SubscriptionStatus.SCHEDULED)
        self.assertFalse(
            ActivityLog.objects.filter(
                subscription=scheduled_subscription,
                event_type=ActivityEventType.SUBSCRIPTION_RENEWED,
            ).exists()
        )

        activate_due_scheduled_subscriptions(
            as_of_date=scheduled_subscription.start_date,
        )
        activate_due_scheduled_subscriptions(
            as_of_date=scheduled_subscription.start_date,
        )

        activities = ActivityLog.objects.filter(
            subscription=scheduled_subscription,
            event_type=ActivityEventType.SUBSCRIPTION_RENEWED,
        )
        self.assertEqual(activities.count(), 1)
        self.assertEqual(activities.get().source, ActivitySource.SYSTEM)
        self.assertIsNone(activities.get().actor)

    def test_scheduled_plan_change_activation_records_system_activation(self):
        organization = self.create_organization("scheduled-activation")
        current_subscription = self.create_subscription(organization)
        scheduled_subscription = self.create_subscription(
            organization,
            status=SubscriptionStatus.SCHEDULED,
            schedule_type=SubscriptionScheduleType.PLAN_CHANGE,
            start_date=current_subscription.expiry_date,
            expiry_date=current_subscription.expiry_date + timedelta(days=30),
            is_current=False,
        )

        activate_due_scheduled_subscriptions(
            as_of_date=scheduled_subscription.start_date,
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                organization=organization,
                subscription=scheduled_subscription,
                event_type=ActivityEventType.SUBSCRIPTION_ACTIVATED,
                source=ActivitySource.SYSTEM,
                actor__isnull=True,
            ).exists()
        )

    def test_cancellation_records_user_activity(self):
        organization = self.create_organization("cancel")
        subscription = self.create_subscription(organization)

        cancel_subscription(
            organization=organization,
            actor=self.user,
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                organization=organization,
                subscription=subscription,
                event_type=ActivityEventType.SUBSCRIPTION_CANCELLED,
                source=ActivitySource.USER,
                actor=self.user,
            ).exists()
        )
