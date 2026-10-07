from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.insights.models import (
    InsightsSyncState,
    InsightsSyncStatus,
    InsightsSyncWork,
    InsightsSyncWorkStage,
    InsightsSyncWorkStatus,
)
from apps.insights.sync_service import ACTIVE_SYNC_STATUSES, dispatch_stage_work


class Command(BaseCommand):
    help = "List or explicitly adopt Insights stage work held during recovery rollout."

    def add_arguments(self, parser):
        parser.add_argument("--work-id")
        parser.add_argument("--reason")

    def handle(self, *args, **options):
        work_id = options.get("work_id")
        reason = (options.get("reason") or "").strip()
        if not work_id:
            self._list_held()
            return
        if not reason:
            raise CommandError("--reason is required when adopting work.")
        if len(reason) > 255:
            raise CommandError("--reason must be 255 characters or fewer.")

        ref = InsightsSyncWork.objects.filter(id=work_id).values("sync_state_id").first()
        if ref is None:
            raise CommandError("Insights work row was not found.")
        with transaction.atomic():
            state = InsightsSyncState.objects.select_for_update().filter(
                id=ref["sync_state_id"], is_deleted=False,
            ).first()
            if state is None:
                raise CommandError("Parent SyncState was not found.")
            work = InsightsSyncWork.objects.select_for_update().filter(
                id=work_id, sync_state=state,
            ).first()
            if work is None or work.status != InsightsSyncWorkStatus.MIGRATION_HOLD:
                raise CommandError("Work is not in migration_hold.")
            if state.status not in ACTIVE_SYNC_STATUSES:
                raise CommandError("Terminal or inactive SyncStates cannot be adopted.")
            stage_status = (
                state.account_status
                if work.stage == InsightsSyncWorkStage.ACCOUNT
                else state.content_status
            )
            if stage_status not in ACTIVE_SYNC_STATUSES:
                raise CommandError("Terminal stages cannot be adopted.")
            work.generation += 1
            work.status = InsightsSyncWorkStatus.PENDING
            work.dispatch_attempt = 0
            work.provider_retry_count = 0
            work.next_attempt_at = timezone.now()
            work.dispatch_expires_at = None
            work.celery_task_id = ""
            work.claim_token = None
            work.claimed_at = None
            work.heartbeat_at = None
            work.lease_expires_at = None
            work.last_error_code = "migration_hold_adopted"
            work.last_error_reason = reason
            work.save()
            adopted_id = str(work.id)

        self.stdout.write(f"Adopted work {adopted_id}; reason: {reason}")
        dispatch_stage_work(adopted_id)

    def _list_held(self):
        held = InsightsSyncWork.objects.select_related("sync_state").filter(
            status=InsightsSyncWorkStatus.MIGRATION_HOLD,
        ).order_by("created_at", "id")
        for work in held:
            state = work.sync_state
            stage_status = (
                state.account_status
                if work.stage == InsightsSyncWorkStage.ACCOUNT
                else state.content_status
            )
            self.stdout.write(
                f"work_id={work.id} sync_state_id={state.id} stage={work.stage} "
                f"sync_status={state.status} stage_status={stage_status} created_at={work.created_at.isoformat()}"
            )
