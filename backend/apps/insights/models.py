from django.db import models
from django.db.models import F, Q

from apps.common.models import BaseModel
from apps.social_accounts.models import SocialAccount


class InsightsAccountSnapshot(BaseModel):
    """Persisted account metrics for one selected date range."""

    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="insights_account_snapshots",
    )
    since = models.DateField()
    until = models.DateField()
    api_version = models.CharField(max_length=16)
    metrics = models.JSONField(default=dict)
    follower_growth = models.JSONField(default=dict)
    profile_metadata = models.JSONField(default=dict)
    fetched_at = models.DateTimeField()
    sync_state = models.ForeignKey(
        "InsightsSyncState",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_snapshots",
    )

    class Meta:
        db_table = "insights_account_snapshots"
        constraints = [
            models.UniqueConstraint(
                fields=("social_account", "since", "until", "api_version"),
                condition=Q(is_deleted=False, sync_state__isnull=True),
                name="ins_acct_snap_legacy_uniq",
            ),
            models.UniqueConstraint(
                fields=("sync_state", "api_version"),
                condition=Q(is_deleted=False, sync_state__isnull=False),
                name="ins_acct_snap_version_uniq",
            ),
            models.CheckConstraint(
                condition=Q(since__lte=F("until")),
                name="ins_acct_snap_valid_range",
            ),
        ]
        indexes = [
            models.Index(
                fields=("social_account", "since", "until"),
                name="ins_acct_snap_range_idx",
            ),
            models.Index(
                fields=("fetched_at",),
                name="ins_acct_snap_fetched_idx",
            ),
        ]


class InsightsMediaSnapshot(BaseModel):
    """Latest persisted native media metadata and returned metrics."""

    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="insights_media_snapshots",
    )
    provider_media_id = models.CharField(max_length=255)
    media_type = models.CharField(max_length=32, blank=True)
    caption = models.TextField(blank=True)
    permalink = models.URLField(max_length=2048, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    api_version = models.CharField(max_length=16)
    metrics = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "insights_media_snapshots"
        constraints = [
            models.UniqueConstraint(
                fields=("social_account", "provider_media_id"),
                condition=Q(is_deleted=False),
                name="ins_media_snap_unique_live",
            ),
        ]
        indexes = [
            models.Index(
                fields=("social_account", "published_at", "provider_media_id"),
                name="ins_media_snap_pub_idx",
            ),
            models.Index(
                fields=("social_account", "fetched_at"),
                name="ins_media_snap_fetched_idx",
            ),
        ]


class InsightsContentSnapshotItem(BaseModel):
    """Immutable content metrics captured by one Insights sync attempt."""

    sync_state = models.ForeignKey(
        "InsightsSyncState",
        on_delete=models.CASCADE,
        related_name="content_snapshot_items",
    )
    provider_media_id = models.CharField(max_length=255)
    media_type = models.CharField(max_length=32, blank=True)
    caption = models.TextField(blank=True)
    permalink = models.URLField(max_length=2048, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    api_version = models.CharField(max_length=16)
    metrics = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "insights_content_snapshot_items"
        constraints = [
            models.UniqueConstraint(
                fields=("sync_state", "provider_media_id"),
                condition=Q(is_deleted=False),
                name="ins_content_state_media_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("sync_state", "published_at", "provider_media_id"),
                name="ins_content_state_pub_idx",
            ),
        ]


class InsightsSyncStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SYNCING = "syncing", "Syncing"
    COMPLETE = "complete", "Complete"
    PARTIAL = "partial", "Partial"
    FAILED = "failed", "Failed"


class InsightsSyncWorkStage(models.TextChoices):
    ACCOUNT = "account", "Account"
    CONTENT = "content", "Content"


class InsightsSyncWorkStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PUBLISHING = "publishing", "Publishing"
    DISPATCHED = "dispatched", "Dispatched"
    CLAIMED = "claimed", "Claimed"
    TERMINAL = "terminal", "Terminal"
    MIGRATION_HOLD = "migration_hold", "Migration hold"


class InsightsSyncState(BaseModel):
    """Durable progress and checkpoint for one account/date-range sync."""

    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="insights_sync_states",
    )
    since = models.DateField()
    until = models.DateField()
    api_version = models.CharField(max_length=16)
    status = models.CharField(
        max_length=16,
        choices=InsightsSyncStatus.choices,
        default=InsightsSyncStatus.QUEUED,
        db_index=True,
    )
    account_status = models.CharField(
        max_length=16,
        choices=InsightsSyncStatus.choices,
        default=InsightsSyncStatus.QUEUED,
        db_index=True,
    )
    content_status = models.CharField(
        max_length=16,
        choices=InsightsSyncStatus.choices,
        default=InsightsSyncStatus.QUEUED,
        db_index=True,
    )
    provider_cursor = models.TextField(blank=True)
    checkpoint = models.JSONField(default=dict)
    items_discovered = models.PositiveIntegerField(default=0)
    items_processed = models.PositiveIntegerField(default=0)
    items_total = models.PositiveIntegerField(null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    account_started_at = models.DateTimeField(null=True, blank=True)
    account_completed_at = models.DateTimeField(null=True, blank=True)
    content_completed_at = models.DateTimeField(null=True, blank=True)
    account_error_code = models.CharField(max_length=64, blank=True)
    account_error_reason = models.CharField(max_length=255, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    error_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "insights_sync_states"
        constraints = [
            models.UniqueConstraint(
                fields=("social_account", "since", "until"),
                condition=Q(
                    is_deleted=False,
                    status__in=(
                        InsightsSyncStatus.QUEUED,
                        InsightsSyncStatus.SYNCING,
                    ),
                ),
                name="ins_sync_unique_active",
            ),
            models.CheckConstraint(
                condition=Q(since__lte=F("until")),
                name="ins_sync_valid_range",
            ),
            models.CheckConstraint(
                condition=Q(items_processed__lte=F("items_discovered")),
                name="ins_sync_processed_le_discovered",
            ),
            models.CheckConstraint(
                condition=(Q(items_total__isnull=True) | Q(items_processed__lte=F("items_total"))),
                name="ins_sync_processed_le_total",
            ),
        ]
        indexes = [
            models.Index(
                fields=("status", "requested_at"),
                name="ins_sync_status_req_idx",
            ),
            models.Index(
                fields=("social_account", "since", "until"),
                name="ins_sync_account_range_idx",
            ),
        ]


class InsightsSnapshotSlot(BaseModel):
    """Stable account-and-duration slot with independently published stages."""

    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="insights_snapshot_slots",
    )
    duration_days = models.PositiveSmallIntegerField()
    published_account_sync_state = models.ForeignKey(
        InsightsSyncState,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_account_snapshot_slots",
    )
    published_content_sync_state = models.ForeignKey(
        InsightsSyncState,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_content_snapshot_slots",
    )
    active_sync_state = models.ForeignKey(
        InsightsSyncState,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_snapshot_slots",
    )

    class Meta:
        db_table = "insights_snapshot_slots"
        constraints = [
            models.UniqueConstraint(
                fields=("social_account", "duration_days"),
                condition=Q(is_deleted=False),
                name="ins_snap_slot_account_days_uniq",
            ),
            models.CheckConstraint(
                condition=Q(duration_days__in=(7, 28, 30)),
                name="ins_snap_slot_days_valid",
            ),
        ]


class InsightsSyncWork(BaseModel):
    """Durable dispatch intent and fenced lease for one sync stage."""

    sync_state = models.ForeignKey(
        InsightsSyncState,
        on_delete=models.CASCADE,
        related_name="stage_work",
    )
    stage = models.CharField(max_length=16, choices=InsightsSyncWorkStage.choices)
    generation = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=InsightsSyncWorkStatus.choices,
        default=InsightsSyncWorkStatus.PENDING,
    )
    dispatch_attempt = models.PositiveIntegerField(default=0)
    provider_retry_count = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    dispatch_expires_at = models.DateTimeField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    claim_token = models.UUIDField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True)
    last_error_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "insights_sync_work"
        constraints = [
            models.UniqueConstraint(
                fields=("sync_state", "stage"),
                name="ins_sync_work_state_stage_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(stage__in=InsightsSyncWorkStage.values),
                name="ins_sync_work_stage_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=InsightsSyncWorkStatus.values),
                name="ins_sync_work_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(status=InsightsSyncWorkStatus.CLAIMED)
                    | (
                        models.Q(claim_token__isnull=False)
                        & models.Q(claimed_at__isnull=False)
                        & models.Q(heartbeat_at__isnull=False)
                        & models.Q(lease_expires_at__isnull=False)
                    )
                ),
                name="ins_sync_work_claim_complete",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(status=InsightsSyncWorkStatus.CLAIMED)
                    | models.Q(lease_expires_at__gt=models.F("claimed_at"))
                ),
                name="ins_sync_work_lease_after_claim",
            ),
        ]
        indexes = [
            models.Index(
                fields=("status", "next_attempt_at", "id"),
                name="ins_sync_work_due_idx",
            ),
            models.Index(
                fields=("status", "dispatch_expires_at", "id"),
                name="ins_sync_work_disp_idx",
            ),
            models.Index(
                fields=("status", "lease_expires_at", "id"),
                name="ins_sync_work_lease_idx",
            ),
        ]
