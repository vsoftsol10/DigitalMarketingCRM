from django.db import migrations, models


def mark_current_subscriptions(apps, schema_editor):
    OrganizationSubscription = apps.get_model(
        "organizations",
        "OrganizationSubscription",
    )

    # Expired subscriptions are historical.
    OrganizationSubscription.objects.filter(
        status="expired",
    ).update(
        is_current=False,
    )

    # Active and cancelled subscriptions are initially
    # considered current during this migration.
    OrganizationSubscription.objects.filter(
        status__in=["active", "cancelled"],
    ).update(
        is_current=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0009_remove_organizationsubscription_plan_reference_and_more",
        ),
        (
            "plans",
            "0004_remove_plan_billing_cycle",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationsubscription",
            name="is_current",
            field=models.BooleanField(
                default=True,
                db_index=True,
            ),
        ),

        migrations.RunPython(
            mark_current_subscriptions,
            migrations.RunPython.noop,
        ),

        migrations.RunSQL(
            sql="""
                ALTER TABLE organization_subscriptions
                ALTER COLUMN plan_id SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE organization_subscriptions
                ALTER COLUMN plan_id DROP NOT NULL;
            """,
        ),

        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX unique_current_subscription_per_org
                ON organization_subscriptions (organization_id)
                WHERE is_current = TRUE;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS unique_current_subscription_per_org;
            """,
        ),
    ]