from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class EmailEventType(models.TextChoices):
    ORGANIZATION_PLAN_WELCOME = (
        "ORGANIZATION_PLAN_WELCOME",
        "Organization Plan Welcome",
    )

    PLAN_EXPIRY_REMINDER = (
        "PLAN_EXPIRY_REMINDER",
        "Plan Expiry Reminder",
    )

    PLAN_EXPIRED = (
        "PLAN_EXPIRED",
        "Plan Expired",
    )

    PLAN_RENEWED = (
        "PLAN_RENEWED",
        "Plan Renewed",
    )

    PLAN_CANCELLED = (
        "PLAN_CANCELLED",
        "Plan Cancelled",
    )

    PLAN_ACTIVATED = (
        "PLAN_ACTIVATED",
        "Plan Activated",
    )


class EmailDeliveryStatus(models.TextChoices):
    PENDING = (
        "PENDING",
        "Pending",
    )

    PROCESSING = (
        "PROCESSING",
        "Processing",
    )

    SENT = (
        "SENT",
        "Sent",
    )

    FAILED = (
        "FAILED",
        "Failed",
    )


class EmailEvent(BaseModel):
    """
    Transactional email event and delivery record.

    Stores the business event that caused an email and the
    provider delivery information required for auditing,
    retries, and idempotency.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="email_events",
    )

    subscription = models.ForeignKey(
        "organizations.OrganizationSubscription",
        on_delete=models.CASCADE,
        related_name="email_events",
        null=True,
        blank=True,
    )

    event_type = models.CharField(
        max_length=50,
        choices=EmailEventType.choices,
        db_index=True,
    )

    recipient_email = models.EmailField()

    recipient_name = models.CharField(
        max_length=255,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.PENDING,
        db_index=True,
    )

    provider_message_id = models.CharField(
        max_length=500,
        blank=True,
    )

    attempts = models.PositiveIntegerField(
        default=0,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_error = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "notification_email_events"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "event_type",
                ],
                name="email_event_org_type_idx",
            ),
            models.Index(
                fields=[
                    "subscription",
                    "event_type",
                ],
                name="email_event_sub_type_idx",
            ),
            models.Index(
                fields=[
                    "status",
                    "created_at",
                ],
                name="email_event_status_created_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "subscription",
                    "event_type",
                ],
                condition=models.Q(
                    is_deleted=False,
                ),
                name="unique_subscription_email_event",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} - " f"{self.recipient_email} - " f"{self.status}"


class UserNotificationType(models.TextChoices):
    FAILED_POST = "FAILED_POST", "Failed Post"
    SUBSCRIPTION_EXPIRED = "SUBSCRIPTION_EXPIRED", "Subscription Expired"
    SUBSCRIPTION_EXPIRING = "SUBSCRIPTION_EXPIRING", "Subscription Expiring Soon"
    POST_PUBLISHED = "POST_PUBLISHED", "Post Published"
    SUBSCRIPTION_ACTIVATED = "SUBSCRIPTION_ACTIVATED", "Subscription Activated"


class UserNotification(BaseModel):
    """Persisted, owner-scoped in-app notification state for lifecycle events."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="user_notifications",
    )
    source_activity = models.ForeignKey(
        "activities.ActivityLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_notifications",
    )
    post_platform = models.ForeignKey(
        "posts.PostPlatform",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_notifications",
    )
    subscription = models.ForeignKey(
        "organizations.OrganizationSubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_notifications",
    )
    event_type = models.CharField(
        max_length=40,
        choices=UserNotificationType.choices,
        db_index=True,
    )
    event_key = models.CharField(max_length=255)
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=500)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "user_notifications"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="user_notif_rec_read_idx",
            ),
            models.Index(
                fields=["recipient", "resolved_at", "-created_at"],
                name="user_notif_rec_res_idx",
            ),
            models.Index(
                fields=["post_platform", "event_type", "resolved_at"],
                name="user_notif_post_state_idx",
            ),
            models.Index(
                fields=["subscription", "event_type", "resolved_at"],
                name="user_notif_sub_state_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event_key"],
                condition=models.Q(event_key__gt="", is_deleted=False),
                name="unique_active_user_notification_key",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.recipient_id} - {self.created_at.isoformat()}"
