import django.db.models.deletion
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0008_populate_subscription_plan_reference",
        ),
        (
            "plans",
            "0004_remove_plan_billing_cycle",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE organization_subscriptions
                        RENAME COLUMN plan_reference_id TO plan_id;
                    """,
                    reverse_sql="""
                        ALTER TABLE organization_subscriptions
                        RENAME COLUMN plan_id TO plan_reference_id;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE organization_subscriptions
                        DROP COLUMN plan;
                    """,
                    reverse_sql="""
                        ALTER TABLE organization_subscriptions
                        ADD COLUMN plan VARCHAR(20);
                    """,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="organizationsubscription",
                    name="plan_reference",
                ),
                migrations.AlterField(
                    model_name="organizationsubscription",
                    name="plan",
                    field=django.db.models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organization_subscriptions",
                        to="plans.plan",
                    ),
                ),
            ],
        ),
    ]