from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0014_alter_organizationsubscription_organization_and_more",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="organizationsubscription",
                    name="organization",
                    field=models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="subscriptions",
                        to="organizations.organization",
                    ),
                ),
            ],
        ),
    ]