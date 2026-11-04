from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0007_media_upload_sessions_and_request_idempotency"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediauploadsession",
            name="cloudinary_version",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
