from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_accounts", "0010_socialaccountinvitation_pending_token_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="socialaccountinvitation",
            name="pending_delivery_token_encrypted",
            field=models.TextField(blank=True, default=""),
        ),
    ]
