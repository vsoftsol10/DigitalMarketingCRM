from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0013_sync_subscription_migration_state",
        ),
        (
            "plans",
            "0004_remove_plan_billing_cycle",
        ),
    ]

    operations = [
        migrations.AddIndex(
            model_name="organizationsubscription",
            index=models.Index(
                fields=[
                    "organization",
                    "is_current",
                ],
                name="org_sub_current_idx",
            ),
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddConstraint(
                    model_name="organizationsubscription",
                    constraint=models.UniqueConstraint(
                        condition=models.Q(
                            is_current=True,
                        ),
                        fields=("organization",),
                        name="unique_current_subscription_per_org",
                    ),
                ),
            ],
        ),
    ]