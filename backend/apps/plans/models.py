from django.db import models

from apps.common.models import BaseModel


class PlanStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class Plan(BaseModel):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    code = models.SlugField(
        max_length=100,
        unique=True,
    )

    plan_type = models.CharField(
        max_length=50,
        db_index=True,
    )

    description = models.TextField(
        max_length=500,
    )

    status = models.CharField(
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.ACTIVE,
        db_index=True,
    )

    monthly_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    yearly_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    accounts_limit = models.PositiveIntegerField(
        default=0,
    )

    posts_limit = models.PositiveIntegerField(
        default=0,
    )

    videos_limit = models.PositiveIntegerField(
        default=0,
    )

    ads_limit = models.PositiveIntegerField(
        default=0,
    )

    dm_automations_limit = models.PositiveIntegerField(
        default=0,
    )

    highlights = models.TextField(
        max_length=1000,
        blank=True,
    )

    is_system = models.BooleanField(
        default=False,
        db_index=True,
    )

    is_custom = models.BooleanField(
        default=False,
        db_index=True,
    )

    class Meta:
        db_table = "plans"
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="plan_status_created_idx",
            ),
            models.Index(
                fields=["is_system"],
                name="plan_system_idx",
            ),
            models.Index(
                fields=["plan_type"],
                name="plan_type_idx",
            ),
        ]

    def __str__(self):
        return self.name
