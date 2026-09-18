from rest_framework import serializers

from apps.plans.models import Plan

from .models import (
    BillingCycle,
    Organization,
    SubscriptionStatus,
)

from django.db.models import Q
from django.utils import timezone

# ============================================================
# ORGANIZATION RESPONSE SERIALIZER
# ============================================================


class NullableDateField(serializers.DateField):
    def to_internal_value(self, data):
        if data == "":
            return None

        return super().to_internal_value(data)


from rest_framework import serializers

from .models import Organization


class OrganizationReadSerializer(serializers.ModelSerializer):
    """
    Frontend-facing read serializer.

    Relationship data is flattened here so the existing frontend
    can continue using its current response structure.

    The serializer prefers prefetched relationship data supplied by
    the organization selectors to avoid N+1 database queries.
    """

    organization_status = serializers.CharField(
        source="status",
        read_only=True,
    )

    location = serializers.SerializerMethodField()

    contact_name = serializers.SerializerMethodField()
    contact_email = serializers.SerializerMethodField()
    contact_phone = serializers.SerializerMethodField()

    # ========================================================
    # CURRENT SUBSCRIPTION
    # ========================================================

    subscription_plan = serializers.SerializerMethodField()
    billing_cycle = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    subscription_start = serializers.SerializerMethodField()
    subscription_expiry = serializers.SerializerMethodField()

    # ========================================================
    # LAST SUBSCRIPTION
    # ========================================================

    last_subscription_status = serializers.SerializerMethodField()
    last_subscription_plan = serializers.SerializerMethodField()
    last_subscription_billing_cycle = serializers.SerializerMethodField()
    last_subscription_start = serializers.SerializerMethodField()
    last_subscription_expiry = serializers.SerializerMethodField()

    # ========================================================
    # UPCOMING SUBSCRIPTION
    # ========================================================

    upcoming_plan = serializers.SerializerMethodField()
    upcoming_billing_cycle = serializers.SerializerMethodField()
    upcoming_start = serializers.SerializerMethodField()
    upcoming_expiry = serializers.SerializerMethodField()

    # ========================================================
    # SOCIAL ACCOUNTS
    # ========================================================

    social_accounts = serializers.SerializerMethodField()

    class Meta:
        model = Organization

        fields = (
            "id",
            "organization_id",
            "name",
            "slug",
            "logo",
            "description",
            "industry",
            "website",
            "location",
            "logo_color",
            "organization_status",
            "contact_name",
            "contact_email",
            "contact_phone",
            # Current subscription
            "subscription_plan",
            "billing_cycle",
            "subscription_status",
            "subscription_start",
            "subscription_expiry",
            # Last subscription
            "last_subscription_status",
            "last_subscription_plan",
            "last_subscription_billing_cycle",
            "last_subscription_start",
            "last_subscription_expiry",
            # Upcoming subscription
            "upcoming_plan",
            "upcoming_billing_cycle",
            "upcoming_start",
            "upcoming_expiry",
            "social_accounts",
            "created_at",
            "updated_at",
        )

    # ========================================================
    # LOCATION
    # ========================================================

    def get_location(self, obj):
        parts = [
            obj.city,
            obj.state,
            obj.country,
        ]

        return ", ".join(part.strip() for part in parts if part and part.strip())

    # ========================================================
    # PRIMARY CONTACT
    # ========================================================

    def _get_primary_contact(self, obj):
        """
        Return the primary organization contact.

        Prefetched contacts are preferred to avoid additional
        database queries during serialization.
        """

        prefetched_contacts = getattr(
            obj,
            "prefetched_contacts",
            None,
        )

        if prefetched_contacts is not None:
            return prefetched_contacts[0] if prefetched_contacts else None

        return (
            obj.contacts.filter(
                is_deleted=False,
                is_primary=True,
            ).first()
            or obj.contacts.filter(
                is_deleted=False,
            ).first()
        )

    def get_contact_name(self, obj):
        contact = self._get_primary_contact(obj)

        return contact.name if contact else ""

    def get_contact_email(self, obj):
        contact = self._get_primary_contact(obj)

        return contact.email if contact else ""

    def get_contact_phone(self, obj):
        contact = self._get_primary_contact(obj)

        return contact.phone if contact else ""

    # ========================================================
    # CURRENT SUBSCRIPTION
    # ========================================================

    def _get_subscription(self, obj):
        """
        Return the organization's current subscription.

        Prefetched current subscriptions are preferred to avoid
        additional database queries.

        Only the subscription marked as current is considered.
        """

        prefetched_subscriptions = getattr(
            obj,
            "prefetched_current_subscriptions",
            None,
        )

        if prefetched_subscriptions is not None:
            return prefetched_subscriptions[0] if prefetched_subscriptions else None

        return (
            obj.subscriptions.filter(
                is_deleted=False,
                is_current=True,
            )
            .select_related("plan")
            .first()
        )

    def get_subscription_plan(self, obj):
        subscription = self._get_subscription(obj)

        if not subscription:
            return None

        return subscription.plan.name

    def get_billing_cycle(self, obj):
        subscription = self._get_subscription(obj)

        if not subscription:
            return None

        return subscription.billing_cycle

    def get_subscription_status(self, obj):
        subscription = self._get_subscription(obj)

        if not subscription:
            return None

        return subscription.status

    def get_subscription_start(self, obj):
        subscription = self._get_subscription(obj)

        if not subscription:
            return None

        return subscription.start_date

    def get_subscription_expiry(self, obj):
        subscription = self._get_subscription(obj)

        if not subscription:
            return None

        return subscription.expiry_date

    # ========================================================
    # LAST SUBSCRIPTION
    # ========================================================

    def _get_last_subscription(self, obj):
        """
        Return the most recent relevant historical subscription.

        Expired subscriptions are considered only when their
        expiry date has already passed.

        Cancelled subscriptions remain eligible regardless of
        expiry date.

        Prefetched data is preferred to avoid additional queries.
        """

        prefetched_subscriptions = getattr(
            obj,
            "prefetched_last_subscriptions",
            None,
        )

        if prefetched_subscriptions is not None:
            return prefetched_subscriptions[0] if prefetched_subscriptions else None

        return (
            obj.subscriptions.filter(
                is_deleted=False,
                is_current=False,
            )
            .filter(
                Q(
                    status=SubscriptionStatus.EXPIRED,
                    expiry_date__lt=timezone.localdate(),
                )
                | Q(
                    status=SubscriptionStatus.CANCELLED,
                )
            )
            .select_related("plan")
            .order_by(
                "-expiry_date",
                "-created_at",
            )
            .first()
        )

    def get_last_subscription_status(self, obj):
        subscription = self._get_last_subscription(obj)

        if not subscription:
            return None

        return subscription.status

    def get_last_subscription_plan(self, obj):
        subscription = self._get_last_subscription(obj)

        if not subscription:
            return None

        return subscription.plan.name

    def get_last_subscription_billing_cycle(self, obj):
        subscription = self._get_last_subscription(obj)

        if not subscription:
            return None

        return subscription.billing_cycle

    def get_last_subscription_start(self, obj):
        subscription = self._get_last_subscription(obj)

        if not subscription:
            return None

        return subscription.start_date

    def get_last_subscription_expiry(self, obj):
        subscription = self._get_last_subscription(obj)

        if not subscription:
            return None

        return subscription.expiry_date

    # ========================================================
    # UPCOMING SUBSCRIPTION
    # ========================================================

    def _get_upcoming_subscription(self, obj):
        """
        Return the earliest scheduled subscription.

        Prefetched upcoming subscriptions are preferred to avoid
        additional database queries.
        """

        prefetched_subscriptions = getattr(
            obj,
            "prefetched_upcoming_subscriptions",
            None,
        )

        if prefetched_subscriptions is not None:
            return prefetched_subscriptions[0] if prefetched_subscriptions else None

        return (
            obj.subscriptions.filter(
                is_deleted=False,
                status="scheduled",
                is_current=False,
            )
            .select_related("plan")
            .order_by(
                "start_date",
                "created_at",
            )
            .first()
        )

    def get_upcoming_plan(self, obj):
        subscription = self._get_upcoming_subscription(obj)

        if not subscription:
            return None

        return subscription.plan.name

    def get_upcoming_billing_cycle(self, obj):
        subscription = self._get_upcoming_subscription(obj)

        if not subscription:
            return None

        return subscription.billing_cycle

    def get_upcoming_start(self, obj):
        subscription = self._get_upcoming_subscription(obj)

        if not subscription:
            return None

        return subscription.start_date

    def get_upcoming_expiry(self, obj):
        subscription = self._get_upcoming_subscription(obj)

        if not subscription:
            return None

        return subscription.expiry_date

    # ========================================================
    # SOCIAL ACCOUNTS
    # ========================================================

    def get_social_accounts(self, obj):
        """
        Return non-deleted social accounts.

        Uses prefetched data when available.
        """

        prefetched_accounts = getattr(
            obj,
            "prefetched_social_accounts",
            None,
        )

        if prefetched_accounts is not None:
            accounts = prefetched_accounts
        else:
            accounts = obj.social_accounts.filter(
                is_deleted=False,
            ).order_by(
                "platform",
                "account_name",
            )

        return [
            {
                "id": str(account.id),
                "platform": account.platform,
                "page_name": account.account_name,
                "username": account.username,
                "connected": (account.status == "connected"),
                "valid": account.is_valid,
                "last_sync": account.last_synced_at,
            }
            for account in accounts
        ]


class OrganizationOptionSerializer(serializers.ModelSerializer):
    """Small organization representation used by selection controls."""

    class Meta:
        model = Organization
        fields = (
            "organization_id",
            "name",
        )
        read_only_fields = fields


# ============================================================
# ORGANIZATION CREATE SERIALIZER
# ============================================================


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """
    Creates an organization together with its primary contact
    and initial subscription.

    Subscription rules:
        - Plan must be selected from active plans only.
        - Billing cycle must be monthly or yearly.
        - Subscription status is always ACTIVE on creation.
        - Start/expiry dates are calculated by the service layer.
        - Client cannot submit subscription status or dates.
    """

    organization_status = serializers.CharField(
        source="status",
        required=False,
        default="ACTIVE",
    )

    location = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    contact_name = serializers.CharField(
        required=True,
        allow_blank=False,
    )

    contact_email = serializers.EmailField(
        required=True,
        allow_blank=False,
    )

    contact_phone = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    subscription_plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(
            status="active",
            is_deleted=False,
        ),
        required=True,
    )

    billing_cycle = serializers.ChoiceField(
        choices=BillingCycle.choices,
        required=True,
    )

    social_accounts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        read_only=True,
    )

    class Meta:
        model = Organization

        fields = (
            "name",
            "description",
            "industry",
            "website",
            "location",
            "logo_color",
            "organization_status",
            "contact_name",
            "contact_email",
            "contact_phone",
            "subscription_plan",
            "billing_cycle",
            "social_accounts",
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Organization name must contain at least 3 characters."
            )

        if Organization.objects.filter(
            name__iexact=value,
            is_deleted=False,
        ).exists():
            raise serializers.ValidationError("Organization name already exists.")

        return value

    def validate_industry(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Industry is required.")

        return value

    def validate_website(self, value):
        return value.strip()

    def validate_location(self, value):
        return value.strip()

    def validate_contact_name(self, value):
        return value.strip()

    def validate_contact_email(self, value):
        return value.strip().lower()

    def validate_contact_phone(self, value):
        return value.strip()

    def validate_organization_status(self, value):
        value = value.strip().upper()

        allowed_values = {
            "ACTIVE",
            "INACTIVE",
        }

        if value not in allowed_values:
            raise serializers.ValidationError("Invalid organization status.")

        return value


# ============================================================
# ORGANIZATION UPDATE SERIALIZER
# ============================================================


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """
    Accepts partial updates from the current frontend.

    The service layer handles the related contact and
    subscription updates atomically.
    """

    organization_status = serializers.CharField(
        source="status",
        required=False,
    )

    location = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    contact_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    contact_email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    contact_phone = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    # subscription_plan = serializers.CharField(
    #     required=False,
    # )
    subscription_plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(
            status="active",
            is_deleted=False,
        ),
        required=False,
    )

    billing_cycle = serializers.CharField(
        required=False,
    )

    subscription_status = serializers.CharField(
        required=False,
    )

    social_accounts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        read_only=True,
    )

    class Meta:
        model = Organization

        fields = (
            "name",
            "description",
            "industry",
            "website",
            "location",
            "logo_color",
            "organization_status",
            "contact_name",
            "contact_email",
            "contact_phone",
            "subscription_plan",
            "billing_cycle",
            "subscription_status",
            "social_accounts",
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Organization name must contain at least 3 characters."
            )

        queryset = Organization.objects.filter(
            name__iexact=value,
            is_deleted=False,
        ).exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Organization name already exists.")

        return value

    def validate_industry(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Industry is required.")

        return value

    def validate_website(self, value):
        return value.strip()

    def validate_location(self, value):
        return value.strip()

    def validate_contact_name(self, value):
        return value.strip()

    def validate_contact_email(self, value):
        return value.strip().lower()

    def validate_contact_phone(self, value):
        return value.strip()

    def validate_organization_status(self, value):
        value = value.strip().upper()

        allowed_values = {
            "ACTIVE",
            "INACTIVE",
        }

        if value not in allowed_values:
            raise serializers.ValidationError("Invalid organization status.")

        return value

    def validate_billing_cycle(self, value):
        value = value.strip().lower()

        allowed_values = {
            "monthly",
            "yearly",
        }

        if value not in allowed_values:
            raise serializers.ValidationError("Invalid billing cycle.")

        return value

    def validate_subscription_status(self, value):
        value = value.strip().lower()

        allowed_values = {
            "trial",
            "active",
            "paused",
            "expired",
            "cancelled",
        }

        if value not in allowed_values:
            raise serializers.ValidationError("Invalid subscription status.")

        return value
