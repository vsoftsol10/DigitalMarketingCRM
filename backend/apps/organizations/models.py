from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class OrganizationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class SubscriptionPlan(models.TextChoices):
    BASIC = "BASIC", "Basic"
    ADVANCE = "ADVANCE", "Advance"
    CUSTOM = "CUSTOM", "Custom"


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SCHEDULED = "scheduled", "Scheduled"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class Organization(BaseModel):
    """
    Core organization/client entity.

    Frontend-facing fields such as organization_status and location
    are exposed through serializers later without forcing the frontend
    to follow the database naming.
    """

    organization_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
    )

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        editable=False,
    )

    logo = models.ImageField(
        upload_to="organizations/logos/",
        null=True,
        blank=True,
    )

    logo_color = models.CharField(
        max_length=20,
        default="#3563F6",
    )

    description = models.TextField(
        blank=True,
    )

    industry = models.CharField(
        max_length=100,
    )

    website = models.URLField(
        blank=True,
    )

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    address = models.TextField(
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        blank=True,
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
    )

    timezone = models.CharField(
        max_length=100,
        default="Asia/Kolkata",
    )

    # ---------------------------------------------------------
    # Organization status
    # ---------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
        db_index=True,
    )

    # ---------------------------------------------------------
    # Ownership / audit context
    # ---------------------------------------------------------

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_organizations",
    )

    class Meta:
        db_table = "organizations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="org_status_created_idx",
            ),
            models.Index(
                fields=["industry"],
                name="org_industry_idx",
            ),
        ]

    def __str__(self):
        return f"{self.organization_id} - {self.name}"


class OrganizationContact(BaseModel):
    """
    Contact persons belonging to an organization.

    Multiple contacts are supported, while one can be marked as
    the primary contact used by the current frontend.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    name = models.CharField(
        max_length=255,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    role = models.CharField(
        max_length=100,
        blank=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "organization_contacts"
        ordering = ["-is_primary", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization"],
                condition=models.Q(is_primary=True),
                name="unique_primary_contact_per_org",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "is_primary"],
                name="org_contact_primary_idx",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class OrganizationSubscription(BaseModel):
    """
    Subscription period belonging to an organization.

    An organization can have multiple subscription records
    over its lifetime. Only one subscription can be current.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

    plan = models.ForeignKey(
        "plans.Plan",
        on_delete=models.PROTECT,
        related_name="organization_subscriptions",
    )

    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
        db_index=True,
    )

    start_date = models.DateField()

    expiry_date = models.DateField()

    is_current = models.BooleanField(
        default=True,
        db_index=True,
    )

    class Meta:
        db_table = "organization_subscriptions"

        indexes = [
            models.Index(
                fields=["status"],
                name="org_sub_status_idx",
            ),
            models.Index(
                fields=["expiry_date"],
                name="org_sub_expiry_idx",
            ),
            models.Index(
                fields=["organization", "is_current"],
                name="org_sub_current_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["organization"],
                condition=models.Q(is_current=True),
                name="unique_current_subscription_per_org",
            ),
        ]
