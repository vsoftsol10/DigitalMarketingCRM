from rest_framework import serializers

from .models import (
    BillingCycle,
    Plan,
    PlanStatus,
)


class PlanReadSerializer(serializers.ModelSerializer):
    """
    Public read contract for plans.

    Keeps the existing frontend field names unchanged.
    """

    # type = serializers.CharField(
    #     source="plan_type",
    #     read_only=True,
    # )
    type = serializers.SerializerMethodField()

    limits = serializers.SerializerMethodField()

    class Meta:
        model = Plan

        fields = (
            "id",
            "name",
            "description",
            "type",
            "status",
            "monthly_price",
            "yearly_price",
            "limits",
            "highlights",
            "is_system",
            "is_custom",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_type(self, obj):
        return obj.plan_type.replace("_", " ").title()

    def get_limits(self, obj):
        return {
            "accounts": obj.accounts_limit,
            "posts": obj.posts_limit,
            "videos": obj.videos_limit,
            "ads": obj.ads_limit,
            "dm_automations": obj.dm_automations_limit,
        }


class PlanCreateSerializer(serializers.ModelSerializer):
    """
    Create a new plan.

    Frontend uses `type`.
    Backend stores it as `plan_type`.
    """

    type = serializers.CharField(
        source="plan_type",
        required=False,
    )

    limits = serializers.DictField(
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Plan

        fields = (
            "name",
            "description",
            "type",
            "status",
            "monthly_price",
            "yearly_price",
            "limits",
            "highlights",
        )

    def validate(self, attrs):
        is_custom = self.context.get(
            "is_custom",
            False,
        )

        if not is_custom and not attrs.get("plan_type"):
            raise serializers.ValidationError({"type": "Plan type is required."})

        if is_custom and attrs.get("plan_type"):
            raise serializers.ValidationError(
                {"type": ("Plan type must not be " "provided for a custom plan.")}
            )

        return attrs

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Plan name must contain at least 2 characters."
            )

        if Plan.objects.filter(
            name__iexact=value,
        ).exists():
            raise serializers.ValidationError("A plan with this name already exists.")

        return value

    def validate_type(self, value):
        value = value.strip().upper()

        if not value:
            raise serializers.ValidationError("Plan type is required.")

        if value == "CUSTOM":
            raise serializers.ValidationError(
                "Custom plans must be created using the Custom Plan flow."
            )

        if Plan.objects.filter(
            plan_type__iexact=value,
        ).exists():
            raise serializers.ValidationError("A plan with this type already exists.")

        return value

    def validate_description(self, value):
        return value.strip()

    def validate_status(self, value):
        value = value.strip().lower()

        allowed_values = {
            PlanStatus.ACTIVE,
            PlanStatus.INACTIVE,
        }

        if value not in allowed_values:
            raise serializers.ValidationError("Invalid plan status.")

        return value

    def validate_monthly_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Monthly price cannot be negative.")

        return value

    def validate_yearly_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Yearly price cannot be negative.")

        return value

    def validate_limits(self, value):
        allowed_fields = {
            "accounts",
            "posts",
            "videos",
            "ads",
            "dm_automations",
        }

        unknown_fields = set(value.keys()) - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                {field: "Unsupported plan limit." for field in unknown_fields}
            )

        for field in allowed_fields:
            if field not in value:
                continue

            try:
                field_value = int(value[field])
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    {field: ("Plan limit must be a valid " "non-negative integer.")}
                )

            if field_value < 0:
                raise serializers.ValidationError(
                    {field: ("Plan limit cannot be negative.")}
                )

        return value


class PlanUpdateSerializer(serializers.ModelSerializer):
    """
    Update an existing plan.

    Plan identity is protected after creation.

    Therefore:
        name       → not editable
        type       → not editable
        code       → not editable

    Editable:
        description
        status
        billing_cycle
        pricing
        limits
        highlights
    """

    limits = serializers.DictField(
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Plan

        fields = (
            "description",
            "status",
            "monthly_price",
            "yearly_price",
            "limits",
            "highlights",
        )

    def validate_description(self, value):
        return value.strip()

    def validate_status(self, value):
        value = value.strip().lower()

        allowed_values = {
            PlanStatus.ACTIVE,
            PlanStatus.INACTIVE,
        }

        if value not in allowed_values:
            raise serializers.ValidationError("Invalid plan status.")

        return value

    def validate_monthly_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Monthly price cannot be negative.")

        return value

    def validate_yearly_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Yearly price cannot be negative.")

        return value

    def validate_limits(self, value):
        allowed_fields = {
            "accounts",
            "posts",
            "videos",
            "ads",
            "dm_automations",
        }

        unknown_fields = set(value.keys()) - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                {field: "Unsupported plan limit." for field in unknown_fields}
            )

        for field in allowed_fields:
            if field not in value:
                continue

            try:
                field_value = int(value[field])
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    {field: ("Plan limit must be a valid " "non-negative integer.")}
                )

            if field_value < 0:
                raise serializers.ValidationError(
                    {field: ("Plan limit cannot be negative.")}
                )

        return value
