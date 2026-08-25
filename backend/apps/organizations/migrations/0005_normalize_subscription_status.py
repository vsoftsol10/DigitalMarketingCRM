from django.db import migrations


def normalize_subscription_status(apps, schema_editor):
    OrganizationSubscription = apps.get_model(
        "organizations",
        "OrganizationSubscription",
    )

    OrganizationSubscription.objects.filter(
        status="trial"
    ).update(
        status="active"
    )

    OrganizationSubscription.objects.filter(
        status="paused"
    ).update(
        status="active"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0004_alter_organizationsubscription_status"),
    ]

    operations = [
        migrations.RunPython(
            normalize_subscription_status,
            migrations.RunPython.noop,
        ),
    ]