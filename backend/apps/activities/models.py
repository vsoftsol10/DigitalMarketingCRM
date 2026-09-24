from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel


class ActivityEventType(models.TextChoices):
    ORGANIZATION_CREATED = "ORGANIZATION_CREATED", "Organization Created"
    SUBSCRIPTION_ACTIVATED = "SUBSCRIPTION_ACTIVATED", "Subscription Activated"
    POST_CREATED = "POST_CREATED", "Post Created"
    POST_SCHEDULED = "POST_SCHEDULED", "Post Scheduled"
    POST_PUBLISHED = "POST_PUBLISHED", "Post Published"
    POST_FAILED = "POST_FAILED", "Post Failed"
    SUBSCRIPTION_RENEWED = "SUBSCRIPTION_RENEWED", "Subscription Renewed"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED", "Subscription Cancelled"


class ActivitySource(models.TextChoices):
    USER = "USER", "User"
    SYSTEM = "SYSTEM", "System"


class ActivityLog(BaseModel):
    """An append-only, organization-scoped business activity record."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="activity_logs",
    )

    event_type = models.CharField(
        max_length=50,
        choices=ActivityEventType.choices,
        db_index=True,
    )

    occurred_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    source = models.CharField(
        max_length=20,
        choices=ActivitySource.choices,
        default=ActivitySource.SYSTEM,
        db_index=True,
    )

    subscription = models.ForeignKey(
        "organizations.OrganizationSubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    post_platform = models.ForeignKey(
        "posts.PostPlatform",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    idempotency_key = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    class Meta:
        db_table = "activity_logs"
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(
                fields=["organization", "-occurred_at", "-id"],
                name="activity_org_occurred_idx",
            ),
            models.Index(
                fields=["organization", "event_type", "-occurred_at"],
                name="activity_org_event_idx",
            ),
            models.Index(
                fields=["post_platform", "event_type"],
                name="activity_target_event_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=models.Q(idempotency_key__gt="", is_deleted=False),
                name="unique_active_activity_idempotency_key",
            ),
        ]

    def __str__(self):
        return f"{self.organization_id} - {self.event_type} - {self.occurred_at.isoformat()}"
