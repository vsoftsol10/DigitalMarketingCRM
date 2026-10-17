from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.db.migrations.operations.special import RunPython
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from .models import Plan
from .serializers import PlanCreateSerializer
from .services import create_plan, delete_plan


class PlanNameAndTypeReuseTests(TestCase):
    def create_plan_record(self, *, name, plan_type, is_custom=False, is_system=False):
        return Plan.objects.create(
            name=name,
            code=f"{name.lower().replace(' ', '-')}-{Plan.objects.count()}",
            plan_type=plan_type,
            description="Plan for duplicate validation tests.",
            is_custom=is_custom,
            is_system=is_system,
        )

    def serializer_for(self, *, name, plan_type="GROWTH", is_custom=False):
        data = {
            "name": name,
            "description": "Plan for duplicate validation tests.",
        }
        if not is_custom:
            data["type"] = plan_type
        return PlanCreateSerializer(data=data, context={"is_custom": is_custom})

    def create_through_serializer(self, *, name, plan_type="GROWTH", is_custom=False):
        serializer = self.serializer_for(
            name=name,
            plan_type=plan_type,
            is_custom=is_custom,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return create_plan(
            validated_data=serializer.validated_data,
            is_custom=is_custom,
        )

    def test_active_name_duplicate_is_rejected(self):
        self.create_plan_record(name="Growth Plan", plan_type="GROWTH")

        serializer = self.serializer_for(name="Growth Plan", plan_type="OTHER")

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_soft_deleted_name_can_be_reused(self):
        deleted = self.create_plan_record(name="Growth Plan", plan_type="GROWTH")
        deleted.soft_delete()

        plan = self.create_through_serializer(name="Growth Plan", plan_type="GROWTH")

        self.assertEqual(plan.name, "Growth Plan")
        self.assertFalse(plan.is_deleted)

    def test_active_regular_type_duplicate_is_rejected(self):
        self.create_plan_record(name="Existing Growth", plan_type="GROWTH")

        serializer = self.serializer_for(name="Another Growth", plan_type="growth")

        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_soft_deleted_regular_type_can_be_reused(self):
        deleted = self.create_plan_record(name="Deleted Growth", plan_type="GROWTH")
        deleted.soft_delete()

        plan = self.create_through_serializer(name="Replacement Growth", plan_type="GROWTH")

        self.assertEqual(plan.plan_type, "GROWTH")

    def test_custom_plans_can_reuse_deleted_names_and_share_custom_type(self):
        deleted = self.create_plan_record(
            name="Deleted Custom",
            plan_type="CUSTOM",
            is_custom=True,
        )
        deleted.soft_delete()

        first = self.create_through_serializer(name="Deleted Custom", is_custom=True)
        second = self.create_through_serializer(name="Another Custom", is_custom=True)

        self.assertEqual(first.plan_type, "CUSTOM")
        self.assertEqual(second.plan_type, "CUSTOM")

    def test_active_custom_name_duplicate_is_rejected(self):
        self.create_plan_record(
            name="Active Custom",
            plan_type="CUSTOM",
            is_custom=True,
        )

        serializer = self.serializer_for(name="Active Custom", is_custom=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_system_plans_remain_undeletable(self):
        system_plan = self.create_plan_record(
            name="System Basic",
            plan_type="BASIC",
            is_system=True,
        )

        with self.assertRaises(ValidationError):
            delete_plan(plan=system_plan)


class PlanNameMigrationRollbackGuardTests(TestCase):
    migration_module = import_module(
        "apps.plans.migrations.0005_active_plan_name_and_type_unique"
    )

    def create_plan_record(self, *, name, plan_type, is_custom=False):
        return Plan.objects.create(
            name=name,
            code=f"{name.lower().replace(' ', '-')}-{Plan.objects.count()}",
            plan_type=plan_type,
            description="Plan for rollback guard tests.",
            is_custom=is_custom,
        )

    def run_rollback_guard(self):
        operation = self.migration_module.Migration.operations[-1]
        self.assertIsInstance(operation, RunPython)
        self.assertIs(
            operation.reverse_code,
            self.migration_module.guard_plan_name_rollback,
        )
        operation.reverse_code(
            apps,
            SimpleNamespace(connection=connection),
        )

    def test_rollback_guard_allows_names_without_duplicates(self):
        self.create_plan_record(name="Rollback Safe Plan", plan_type="SAFE")

        self.run_rollback_guard()

    def test_rollback_guard_refuses_reused_soft_deleted_name(self):
        deleted = self.create_plan_record(
            name="Reusable Plan",
            plan_type="OLD",
        )
        deleted.soft_delete()
        self.create_plan_record(name="reusable plan", plan_type="NEW")

        with self.assertRaisesRegex(RuntimeError, "No schema changes were made"):
            self.run_rollback_guard()

    def test_type_duplicates_do_not_block_rollback(self):
        deleted = self.create_plan_record(name="Deleted Type", plan_type="SHARED")
        deleted.soft_delete()
        self.create_plan_record(name="Active Type", plan_type="SHARED")

        self.run_rollback_guard()
