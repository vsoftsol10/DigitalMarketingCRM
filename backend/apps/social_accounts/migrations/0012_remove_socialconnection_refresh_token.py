from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("social_accounts", "0011_socialaccountinvitation_pending_delivery_token_encrypted"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="socialconnection",
            name="refresh_token",
        ),
    ]
