from rest_framework import serializers

from apps.plans.models import Plan

from .models import (
    BillingCycle,
    OrganizationSubscription,
)


class SubscriptionRenewSerializer(serializers.Serializer):
    billing_cycle = serializers.ChoiceField(
        choices=BillingCycle.choices,
        required=False,
    )


class SubscriptionChangePlanSerializer(
    serializers.Serializer,
):
    plan = serializers.PrimaryKeyRelatedField(
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


class SubscriptionStartSerializer(
    serializers.Serializer,
):
    plan = serializers.PrimaryKeyRelatedField(
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


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True,
    )

    plan_code = serializers.CharField(
        source="plan.code",
        read_only=True,
    )

    class Meta:
        model = OrganizationSubscription

        fields = (
            "id",
            "plan_name",
            "plan_code",
            "billing_cycle",
            "status",
            "start_date",
            "expiry_date",
            "is_current",
            "created_at",
            "updated_at",
        )
