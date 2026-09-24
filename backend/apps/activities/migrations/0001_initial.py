from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organizations", "0016_organizationsubscription_schedule_type"),
        ("posts", "0006_poststatus_unresolved"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("event_type", models.CharField(choices=[("ORGANIZATION_CREATED", "Organization Created"), ("SUBSCRIPTION_ACTIVATED", "Subscription Activated"), ("POST_CREATED", "Post Created"), ("POST_SCHEDULED", "Post Scheduled"), ("POST_PUBLISHED", "Post Published"), ("POST_FAILED", "Post Failed"), ("SUBSCRIPTION_RENEWED", "Subscription Renewed"), ("SUBSCRIPTION_CANCELLED", "Subscription Cancelled")], db_index=True, max_length=50)),
                ("occurred_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("source", models.CharField(choices=[("USER", "User"), ("SYSTEM", "System")], db_index=True, default="SYSTEM", max_length=20)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("idempotency_key", models.CharField(blank=True, default="", max_length=255)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="activity_logs", to="organizations.organization")),
                ("post", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to="posts.post")),
                ("post_platform", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to="posts.postplatform")),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to="organizations.organizationsubscription")),
            ],
            options={
                "db_table": "activity_logs",
                "ordering": ["-occurred_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["organization", "-occurred_at", "-id"], name="activity_org_occurred_idx"),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["organization", "event_type", "-occurred_at"], name="activity_org_event_idx"),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["post_platform", "event_type"], name="activity_target_event_idx"),
        ),
        migrations.AddConstraint(
            model_name="activitylog",
            constraint=models.UniqueConstraint(condition=models.Q(("idempotency_key__gt", ""), ("is_deleted", False)), fields=("idempotency_key",), name="unique_active_activity_idempotency_key"),
        ),
    ]
