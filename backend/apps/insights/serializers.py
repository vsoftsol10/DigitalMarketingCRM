from rest_framework import serializers
from django.utils import timezone

from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialPlatform


class InsightsOrganizationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="organization_id", read_only=True)

    class Meta:
        model = Organization
        fields = ("id", "name")
        read_only_fields = fields


class InsightsAccountSerializer(serializers.ModelSerializer):
    organization_id = serializers.CharField(
        source="organization.organization_id",
        read_only=True,
    )
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = SocialAccount
        fields = (
            "id",
            "organization_id",
            "platform",
            "platform_account_id",
            "account_name",
            "username",
            "display_name",
            "profile_image",
        )
        read_only_fields = fields

    def get_display_name(self, obj):
        return obj.username or obj.account_name or obj.platform_account_id


class InsightsSnapshotMediaSerializer(serializers.Serializer):
    provider_media_id = serializers.CharField()
    media_type = serializers.CharField(allow_blank=True)
    caption = serializers.CharField(allow_blank=True)
    permalink = serializers.CharField(allow_blank=True)
    published_at = serializers.DateTimeField(allow_null=True)
    metrics = serializers.JSONField()
    fetched_at = serializers.DateTimeField(allow_null=True)


class MetricValueSerializer(serializers.Serializer):
    value = serializers.JSONField(allow_null=True)
    label = serializers.CharField()
    unit = serializers.CharField(allow_blank=True)
    date = serializers.DateField(required=False, allow_null=True)
    measurement = serializers.CharField(required=False, allow_blank=True)
    aggregation = serializers.CharField(required=False, allow_blank=True)
    availability = serializers.ChoiceField(
        choices=(
            "available",
            "unavailable",
            "permission_required",
            "provider_error",
            "not_supported",
        ),
    )
    source = serializers.CharField()
    provider_metric = serializers.CharField(required=False, allow_blank=True)
    period = serializers.CharField(allow_null=True, allow_blank=True)
    reason = serializers.CharField(allow_blank=True)


class DateRangeSerializer(serializers.Serializer):
    since = serializers.DateField(allow_null=True)
    until = serializers.DateField(allow_null=True)


class InsightsFiltersSerializer(serializers.Serializer):
    organization_id = serializers.CharField()
    date_range = DateRangeSerializer()


class InsightsDateRangeQuerySerializer(serializers.Serializer):
    since = serializers.DateField(required=False)
    until = serializers.DateField(required=False)
    cursor = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        if ("since" in attrs) != ("until" in attrs):
            raise serializers.ValidationError(
                "Both since and until must be provided together."
            )
        if attrs.get("since") and attrs["since"] > attrs["until"]:
            raise serializers.ValidationError("since must be on or before until.")
        return attrs


class InsightsSnapshotQuerySerializer(serializers.Serializer):
    """Required filters shared by persisted snapshot read endpoints."""

    since = serializers.DateField(required=True)
    until = serializers.DateField(required=True)
    platform = serializers.ChoiceField(
        choices=(SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK),
        required=True,
    )

    def validate(self, attrs):
        since = attrs["since"]
        until = attrs["until"]
        if since > until:
            raise serializers.ValidationError({"since": "since must be on or before until."})
        if until > timezone.localdate():
            raise serializers.ValidationError({"until": "until cannot be in the future."})
        if (until - since).days > 89:
            raise serializers.ValidationError({"date_range": "Insights date ranges cannot exceed 90 days."})
        return attrs


class InsightsSyncRequestSerializer(serializers.Serializer):
    """Validated filters for explicitly requesting a persisted sync."""

    since = serializers.DateField(required=True)
    until = serializers.DateField(required=True)
    platform = serializers.ChoiceField(
        choices=(SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK),
        required=True,
    )
    force_refresh = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        since = attrs["since"]
        until = attrs["until"]
        if since > until:
            raise serializers.ValidationError({"since": "since must be on or before until."})
        if until > timezone.localdate():
            raise serializers.ValidationError({"until": "until cannot be in the future."})
        if (until - since).days > 89:
            raise serializers.ValidationError({"date_range": "Insights date ranges cannot exceed 90 days."})
        return attrs


class FollowerGrowthPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = MetricValueSerializer()


class FollowerGrowthSerializer(serializers.Serializer):
    availability = serializers.ChoiceField(
        choices=("available", "unavailable", "permission_required", "provider_error", "not_supported"),
    )
    reason = serializers.CharField(allow_blank=True)
    current_value = MetricValueSerializer()
    change = MetricValueSerializer()
    points = FollowerGrowthPointSerializer(many=True)


class AccountPerformanceSerializer(serializers.Serializer):
    availability = serializers.ChoiceField(
        choices=("available", "unavailable", "permission_required", "provider_error", "not_supported"),
    )
    reason = serializers.CharField(allow_blank=True)
    metrics = serializers.DictField(child=MetricValueSerializer())


class ContentPerformanceItemSerializer(serializers.Serializer):
    content_id = serializers.CharField()
    media_type = serializers.CharField(allow_blank=True)
    caption = serializers.CharField(allow_blank=True)
    permalink = serializers.URLField(allow_blank=True)
    published_at = serializers.DateTimeField(allow_null=True)
    field_availability = serializers.DictField(
        child=serializers.ChoiceField(
            choices=("available", "unavailable", "permission_required", "provider_error", "not_supported"),
        ),
    )
    metrics = serializers.DictField(child=MetricValueSerializer())


class ContentPerformanceSerializer(serializers.Serializer):
    availability = serializers.ChoiceField(
        choices=("available", "unavailable", "permission_required", "provider_error", "not_supported"),
    )
    reason = serializers.CharField(allow_blank=True)
    results = ContentPerformanceItemSerializer(many=True)
    next = serializers.CharField(allow_null=True, allow_blank=True)


class InsightsResponseSerializer(serializers.Serializer):
    """Stable, account-scoped envelope for subsequent metric implementations."""

    schema_version = serializers.CharField()
    filters = InsightsFiltersSerializer()
    account = InsightsAccountSerializer()
    provider_metadata = serializers.DictField(
        child=serializers.JSONField(allow_null=True),
    )
    metrics = serializers.DictField(child=MetricValueSerializer())
    follower_growth = FollowerGrowthSerializer()
    account_performance = AccountPerformanceSerializer()
    content_performance = ContentPerformanceSerializer()
