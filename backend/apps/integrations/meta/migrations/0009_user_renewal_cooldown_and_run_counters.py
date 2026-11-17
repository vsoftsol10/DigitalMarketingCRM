from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("meta_integration", "0008_metaaccountcredential_provider_expiry_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="metaaccountcredential",
            name="last_user_token_renewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metatokenmaintenancerun",
            name="user_renewed",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="metatokenmaintenancerun",
            name="user_skipped",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="metatokenmaintenancerun",
            name="user_locked",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="metatokenmaintenancerun",
            name="user_stale",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="metatokenmaintenancerun",
            name="user_retry",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
