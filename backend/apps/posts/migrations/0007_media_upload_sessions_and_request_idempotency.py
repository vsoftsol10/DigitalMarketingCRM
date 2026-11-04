import uuid

from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0006_poststatus_unresolved"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organizations", "0017_active_organization_name_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="request_idempotency_key",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=128,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="post",
            constraint=models.UniqueConstraint(
                condition=Q(request_idempotency_key__isnull=False),
                fields=("organization", "request_idempotency_key"),
                name="unique_post_request_idempotency",
            ),
        ),
        migrations.CreateModel(
            name="MediaUploadSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("original_filename", models.CharField(max_length=255)),
                ("content_type", models.CharField(max_length=100)),
                (
                    "media_type",
                    models.CharField(
                        choices=[("IMAGE", "Image"), ("VIDEO", "Video")],
                        max_length=10,
                    ),
                ),
                ("expected_size", models.PositiveBigIntegerField()),
                ("bytes_uploaded", models.PositiveBigIntegerField(default=0)),
                ("cloudinary_public_id", models.CharField(max_length=512)),
                ("cloudinary_asset_id", models.CharField(blank=True, max_length=255)),
                (
                    "cloudinary_secure_url",
                    models.URLField(blank=True, max_length=2048),
                ),
                (
                    "cloudinary_resource_type",
                    models.CharField(default="image", max_length=20),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("CREATED", "Created"),
                            ("UPLOADING", "Uploading"),
                            ("PROCESSING", "Processing"),
                            ("READY", "Ready"),
                            ("FAILED", "Failed"),
                            ("EXPIRED", "Expired"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="CREATED",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("finalized_at", models.DateTimeField(blank=True, null=True)),
                (
                    "attached_post",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="media_upload_sessions",
                        to="posts.post",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="media_upload_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media_upload_sessions",
                        to="organizations.organization",
                    ),
                ),
            ],
            options={
                "db_table": "media_upload_sessions",
            },
        ),
        migrations.AddIndex(
            model_name="mediauploadsession",
            index=models.Index(
                fields=["organization", "status"],
                name="media_upload_org_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="mediauploadsession",
            index=models.Index(
                fields=["expires_at", "status"],
                name="media_upload_expiry_idx",
            ),
        ),
    ]
