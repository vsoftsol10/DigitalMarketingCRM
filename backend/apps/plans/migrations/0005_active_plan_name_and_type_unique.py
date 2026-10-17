from django.db import migrations, models
from django.db.models import Count, Q
from django.db.models.functions import Lower


def validate_active_plan_names_and_types(apps, schema_editor):
    Plan = apps.get_model("plans", "Plan")
    database = schema_editor.connection.alias

    duplicate_names = (
        Plan.objects.using(database)
        .filter(is_deleted=False)
        .annotate(normalized_name=Lower("name"))
        .values("normalized_name")
        .annotate(value_count=Count("pk"))
        .filter(value_count__gt=1)
    )
    duplicate_regular_types = (
        Plan.objects.using(database)
        .filter(is_deleted=False, is_custom=False)
        .annotate(normalized_type=Lower("plan_type"))
        .values("normalized_type")
        .annotate(value_count=Count("pk"))
        .filter(value_count__gt=1)
    )

    name_group_count = duplicate_names.count()
    type_group_count = duplicate_regular_types.count()
    if name_group_count or type_group_count:
        raise RuntimeError(
            "Cannot add active Plan name/type uniqueness: "
            f"{name_group_count} case-insensitive duplicate name group(s) "
            "and "
            f"{type_group_count} duplicate regular type group(s) exist "
            "among non-deleted plans. Resolve these conflicts manually "
            "before retrying the migration. No records were changed."
        )


def guard_plan_name_rollback(apps, schema_editor):
    Plan = apps.get_model("plans", "Plan")
    duplicate_names = (
        Plan.objects.using(schema_editor.connection.alias)
        .annotate(normalized_name=Lower("name"))
        .values("normalized_name")
        .annotate(value_count=Count("pk"))
        .filter(value_count__gt=1)
    )

    if duplicate_names.exists():
        duplicate_count = duplicate_names.count()
        raise RuntimeError(
            "Cannot roll back active Plan name uniqueness: "
            f"{duplicate_count} case-insensitive duplicate name group(s) "
            "exist across all plans, including soft-deleted rows. Resolve "
            "the duplicate names manually before retrying rollback. "
            "No schema changes were made."
        )

    # Reversing this migration removes the partial type index. The earlier
    # Plan schema had no type uniqueness rule, so type duplicates need not
    # block rollback.


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0008_populate_subscription_plan_reference"),
        ("plans", "0004_remove_plan_billing_cycle"),
    ]

    operations = [
        migrations.RunPython(
            validate_active_plan_names_and_types,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="plan",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name="plan",
            constraint=models.UniqueConstraint(
                Lower("name"),
                condition=Q(is_deleted=False),
                name="plan_active_name_lower_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="plan",
            constraint=models.UniqueConstraint(
                Lower("plan_type"),
                condition=Q(is_deleted=False, is_custom=False),
                name="plan_active_type_lower_uniq",
            ),
        ),
        # Reverse this guard before the name index is removed and the old
        # unconditional name uniqueness is restored.
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=guard_plan_name_rollback,
        ),
    ]
