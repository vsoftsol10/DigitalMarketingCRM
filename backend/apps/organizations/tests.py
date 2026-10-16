from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
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


class RequiredSubscriptionPlanMigrationTests(TransactionTestCase):
    migrate_from = [
        ("organizations", "0007_organizationsubscription_plan_reference"),
    ]
    migrate_to = [
        ("organizations", "0008_populate_subscription_plan_reference"),
    ]

    def setUp(self):
        super().setUp()
        MigrationExecutor(connection).migrate(self.migrate_from)
        self.apps = MigrationExecutor(connection).loader.project_state(
            self.migrate_from,
        ).apps
        Plan = self.apps.get_model("plans", "Plan")
        Plan.objects.filter(
            code__in=["basic", "advanced", "legacy-custom"],
        ).delete()

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def migrate_forward(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def test_migration_seeds_missing_plans_without_overwriting_existing(self):
        Plan = self.apps.get_model("plans", "Plan")
        existing_basic = Plan.objects.create(
            name="Basic",
            code="basic",
            plan_type="BASIC",
            description="Existing approved Basic configuration.",
            status="inactive",
            monthly_price=1234,
            is_system=False,
        )

        self.migrate_forward()

        Plan = self.apps.get_model("plans", "Plan")
        existing_basic.refresh_from_db()
        advanced = Plan.objects.get(code="advanced")
        self.assertEqual(
            existing_basic.description,
            "Existing approved Basic configuration.",
        )
        self.assertEqual(existing_basic.status, "inactive")
        self.assertEqual(existing_basic.monthly_price, 1234)
        self.assertFalse(existing_basic.is_system)
        self.assertEqual(advanced.plan_type, "ADVANCED")
        self.assertFalse(Plan.objects.filter(code="legacy-custom").exists())

    def test_migration_preserves_existing_advanced_plan_configuration(self):
        Plan = self.apps.get_model("plans", "Plan")
        existing_advanced = Plan.objects.create(
            name="Advanced",
            code="advanced",
            plan_type="ADVANCED",
            description="Approved Advanced configuration.",
            status="inactive",
            monthly_price=61234,
            yearly_price=612345,
            accounts_limit=42,
            posts_limit=1234,
            videos_limit=567,
            ads_limit=89,
            dm_automations_limit=101,
            highlights="Custom Advanced highlights",
            is_system=False,
            is_custom=True,
        )

        self.migrate_forward()

        Plan = self.apps.get_model("plans", "Plan")
        existing_advanced.refresh_from_db()
        self.assertEqual(Plan.objects.filter(code="advanced").count(), 1)
        self.assertEqual(existing_advanced.name, "Advanced")
        self.assertEqual(existing_advanced.code, "advanced")
        self.assertEqual(existing_advanced.plan_type, "ADVANCED")
        self.assertEqual(
            existing_advanced.description,
            "Approved Advanced configuration.",
        )
        self.assertEqual(existing_advanced.status, "inactive")
        self.assertEqual(existing_advanced.monthly_price, 61234)
        self.assertEqual(existing_advanced.yearly_price, 612345)
        self.assertEqual(existing_advanced.accounts_limit, 42)
        self.assertEqual(existing_advanced.posts_limit, 1234)
        self.assertEqual(existing_advanced.videos_limit, 567)
        self.assertEqual(existing_advanced.ads_limit, 89)
        self.assertEqual(existing_advanced.dm_automations_limit, 101)
        self.assertEqual(
            existing_advanced.highlights,
            "Custom Advanced highlights",
        )
        self.assertFalse(existing_advanced.is_system)
        self.assertTrue(existing_advanced.is_custom)

    def test_migration_fails_safely_on_required_plan_name_conflict(self):
        Plan = self.apps.get_model("plans", "Plan")
        conflicting_plan = Plan.objects.create(
            name="Basic",
            code="approved-basic-alias",
            plan_type="BASIC",
            description="Existing plan with a conflicting name.",
        )

        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "required subscription Plan with code 'basic'.*"
                "already exists under another code",
            ):
                self.migrate_forward()

            Plan = self.apps.get_model("plans", "Plan")
            self.assertEqual(Plan.objects.filter(name="Basic").count(), 1)
            self.assertTrue(
                Plan.objects.filter(pk=conflicting_plan.pk).exists(),
            )
            self.assertFalse(Plan.objects.filter(code="basic").exists())
            self.assertFalse(Plan.objects.filter(code="advanced").exists())
        finally:
            # Let tearDown migrate the test database back to its latest state.
            conflicting_plan.delete()

    def test_custom_subscriptions_receive_a_legacy_custom_plan_reference(self):
        Organization = self.apps.get_model("organizations", "Organization")
        OrganizationSubscription = self.apps.get_model(
            "organizations",
            "OrganizationSubscription",
        )
        organization = Organization.objects.create(
            organization_id="ORG-MIGRATION-CUSTOM",
            name="Migration Custom Organization",
            slug="migration-custom-organization",
            industry="Retail",
        )
        subscription = OrganizationSubscription.objects.create(
            organization=organization,
            plan="CUSTOM",
            status="active",
        )

        self.migrate_forward()

        OrganizationSubscription = self.apps.get_model(
            "organizations",
            "OrganizationSubscription",
        )
        Plan = self.apps.get_model("plans", "Plan")
        subscription = OrganizationSubscription.objects.get(pk=subscription.pk)
        legacy_custom = Plan.objects.get(code="legacy-custom")
        self.assertEqual(subscription.plan_reference_id, legacy_custom.pk)
        self.assertTrue(legacy_custom.is_custom)
        self.assertEqual(legacy_custom.plan_type, "CUSTOM")

    def test_existing_legacy_custom_plan_configuration_is_preserved(self):
        Plan = self.apps.get_model("plans", "Plan")
        existing_legacy_custom = Plan.objects.create(
            name="Approved Legacy Custom",
            code="legacy-custom",
            plan_type="CUSTOM",
            description="Existing legacy configuration.",
            monthly_price=7654,
            is_custom=True,
        )

        Organization = self.apps.get_model("organizations", "Organization")
        OrganizationSubscription = self.apps.get_model(
            "organizations",
            "OrganizationSubscription",
        )
        organization = Organization.objects.create(
            organization_id="ORG-MIGRATION-CUSTOM-EXISTING",
            name="Migration Existing Custom Organization",
            slug="migration-existing-custom-organization",
            industry="Retail",
        )
        subscription = OrganizationSubscription.objects.create(
            organization=organization,
            plan="CUSTOM",
            status="active",
        )

        self.migrate_forward()

        OrganizationSubscription = self.apps.get_model(
            "organizations",
            "OrganizationSubscription",
        )
        Plan = self.apps.get_model("plans", "Plan")
        existing_legacy_custom.refresh_from_db()
        subscription = OrganizationSubscription.objects.get(pk=subscription.pk)
        self.assertEqual(Plan.objects.filter(code="legacy-custom").count(), 1)
        self.assertEqual(
            existing_legacy_custom.description,
            "Existing legacy configuration.",
        )
        self.assertEqual(existing_legacy_custom.monthly_price, 7654)
        self.assertEqual(subscription.plan_reference_id, existing_legacy_custom.pk)
