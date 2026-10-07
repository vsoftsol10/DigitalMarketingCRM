import uuid

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, Q
from django.utils import timezone


def backfill_stage_work(apps, schema_editor):
    SyncState = apps.get_model("insights", "InsightsSyncState")
    SyncWork = apps.get_model("insights", "InsightsSyncWork")
    terminal = {"complete", "partial", "failed"}
    active = {"queued", "syncing"}
    for state in SyncState.objects.all().iterator():
        stage_statuses = {
            "account": state.account_status,
            "content": state.content_status,
        }
        for stage, stage_status in (
            ("account", stage_statuses["account"]),
            ("content", stage_statuses["content"]),
        ):
            if state.status in terminal and stage_status in terminal:
                work_status = "terminal"
            elif state.status in active and stage_status in terminal:
                other_stage = "content" if stage == "account" else "account"
                # A terminal stage in a legitimately active sync needs no
                # recovery. If both stages are terminal while the aggregate
                # remains active, hold both rows for explicit human adoption.
                work_status = (
                    "migration_hold"
                    if stage_statuses[other_stage] in terminal
                    else "terminal"
                )
            else:
                work_status = "migration_hold"
            SyncWork.objects.create(
                sync_state_id=state.pk,
                stage=stage,
                generation=1,
                status=work_status,
                next_attempt_at=None,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )


class Migration(migrations.Migration):
    dependencies = [
        ("insights", "0003_insightssyncstate_content_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="InsightsSyncWork",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(null=True, blank=True)),
                ("stage", models.CharField(max_length=16, choices=[("account", "Account"), ("content", "Content")])),
                ("generation", models.PositiveIntegerField(default=1)),
                ("status", models.CharField(max_length=16, choices=[("pending", "Pending"), ("publishing", "Publishing"), ("dispatched", "Dispatched"), ("claimed", "Claimed"), ("terminal", "Terminal"), ("migration_hold", "Migration hold")], default="pending")),
                ("dispatch_attempt", models.PositiveIntegerField(default=0)),
                ("provider_retry_count", models.PositiveIntegerField(default=0)),
                ("next_attempt_at", models.DateTimeField(null=True, blank=True)),
                ("dispatch_expires_at", models.DateTimeField(null=True, blank=True)),
                ("celery_task_id", models.CharField(max_length=255, blank=True)),
                ("claim_token", models.UUIDField(null=True, blank=True)),
                ("claimed_at", models.DateTimeField(null=True, blank=True)),
                ("heartbeat_at", models.DateTimeField(null=True, blank=True)),
                ("lease_expires_at", models.DateTimeField(null=True, blank=True)),
                ("last_error_code", models.CharField(max_length=64, blank=True)),
                ("last_error_reason", models.CharField(max_length=255, blank=True)),
                ("sync_state", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stage_work", to="insights.insightssyncstate")),
            ],
            options={"db_table": "insights_sync_work"},
        ),
        migrations.AddConstraint(
            model_name="insightssyncwork",
            constraint=models.UniqueConstraint(fields=("sync_state", "stage"), name="ins_sync_work_state_stage_uniq"),
        ),
        migrations.AddConstraint(
            model_name="insightssyncwork",
            constraint=models.CheckConstraint(condition=Q(stage__in=("account", "content")), name="ins_sync_work_stage_valid"),
        ),
        migrations.AddConstraint(
            model_name="insightssyncwork",
            constraint=models.CheckConstraint(condition=Q(status__in=("pending", "publishing", "dispatched", "claimed", "terminal", "migration_hold")), name="ins_sync_work_status_valid"),
        ),
        migrations.AddConstraint(
            model_name="insightssyncwork",
            constraint=models.CheckConstraint(
                condition=(
                    ~Q(status="claimed")
                    | (Q(claim_token__isnull=False) & Q(claimed_at__isnull=False) & Q(heartbeat_at__isnull=False) & Q(lease_expires_at__isnull=False))
                ),
                name="ins_sync_work_claim_complete",
            ),
        ),
        migrations.AddConstraint(
            model_name="insightssyncwork",
            constraint=models.CheckConstraint(
                condition=~Q(status="claimed") | Q(lease_expires_at__gt=F("claimed_at")),
                name="ins_sync_work_lease_after_claim",
            ),
        ),
        migrations.AddIndex(
            model_name="insightssyncwork",
            index=models.Index(fields=("status", "next_attempt_at", "id"), name="ins_sync_work_due_idx"),
        ),
        migrations.AddIndex(
            model_name="insightssyncwork",
            index=models.Index(fields=("status", "dispatch_expires_at", "id"), name="ins_sync_work_disp_idx"),
        ),
        migrations.AddIndex(
            model_name="insightssyncwork",
            index=models.Index(fields=("status", "lease_expires_at", "id"), name="ins_sync_work_lease_idx"),
        ),
        migrations.RunPython(backfill_stage_work, migrations.RunPython.noop),
    ]
