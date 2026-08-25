from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0005_normalize_subscription_status",
        ),
        (
            "plans",
            "0001_initial",
        ),
    ]

    operations = []