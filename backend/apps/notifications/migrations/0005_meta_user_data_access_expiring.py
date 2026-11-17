from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0004_alter_usernotification_event_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usernotification",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("FAILED_POST", "Failed Post"),
                    (
                        "META_USER_DATA_ACCESS_EXPIRING",
                        "Meta User Data Access Expiring",
                    ),
                    (
                        "SOCIAL_ACCOUNT_RECONNECT_REQUIRED",
                        "Social Account Reconnect Required",
                    ),
                    ("SUBSCRIPTION_EXPIRED", "Subscription Expired"),
                    ("SUBSCRIPTION_EXPIRING", "Subscription Expiring Soon"),
                    ("POST_PUBLISHED", "Post Published"),
                    ("SUBSCRIPTION_ACTIVATED", "Subscription Activated"),
                ],
                db_index=True,
                max_length=40,
            ),
        ),
    ]
