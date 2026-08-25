from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0012_remove_subscription_org_unique",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="organizationsubscription",
                    name="plan",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organization_subscriptions",
                        to="plans.plan",
                    ),
                ),
                migrations.AlterField(
                    model_name="organizationsubscription",
                    name="start_date",
                    field=models.DateField(),
                ),
                migrations.AlterField(
                    model_name="organizationsubscription",
                    name="expiry_date",
                    field=models.DateField(),
                ),
                migrations.AlterField(
                    model_name="organizationsubscription",
                    name="status",
                    field=models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("scheduled", "Scheduled"),
                            ("expired", "Expired"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=20,
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
