from django.db import migrations, models
from django.db.models import Count, Q
from django.db.models.functions import Lower


def validate_active_organization_names(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    duplicates = (
        Organization.objects.using(schema_editor.connection.alias)
        .filter(is_deleted=False)
        .annotate(normalized_name=Lower("name"))
        .values("normalized_name")
        .annotate(name_count=Count("pk"))
        .filter(name_count__gt=1)
    )

    if duplicates.exists():
        duplicate_count = duplicates.count()
        raise RuntimeError(
            "Cannot add active organization name uniqueness: "
            f"{duplicate_count} case-insensitive duplicate name group(s) "
            "exist among non-deleted organizations. Resolve these conflicts "
            "manually before retrying the migration. No records were changed."
        )


def guard_organization_name_rollback(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    duplicates = (
        Organization.objects.using(schema_editor.connection.alias)
        .annotate(normalized_name=Lower("name"))
        .values("normalized_name")
        .annotate(name_count=Count("pk"))
        .filter(name_count__gt=1)
    )

    if duplicates.exists():
        duplicate_count = duplicates.count()
        raise RuntimeError(
            "Cannot roll back active Organization name uniqueness: "
            f"{duplicate_count} case-insensitive duplicate name group(s) "
            "exist across all organizations, including soft-deleted rows. "
            "Resolve the duplicate names manually before retrying rollback. "
            "No schema changes were made."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0016_organizationsubscription_schedule_type"),
    ]

    operations = [
        migrations.RunPython(
            validate_active_organization_names,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="organization",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AddConstraint(
            model_name="organization",
            constraint=models.UniqueConstraint(
                Lower("name"),
                condition=Q(is_deleted=False),
                name="org_active_name_lower_uniq",
            ),
        ),
        # Django reverses operations in reverse order, so this check runs
        # before removing the partial index or restoring unconditional
        # uniqueness on Organization.name.
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=guard_organization_name_rollback,
        ),
    ]
