from rest_framework import serializers


class DashboardStatisticsSerializer(serializers.Serializer):
    total_organizations = serializers.IntegerField()
    connected_social_accounts = serializers.IntegerField()
    scheduled_posts_today = serializers.IntegerField()
    published_posts_today = serializers.IntegerField()


class DashboardScheduleItemSerializer(serializers.Serializer):
    target_id = serializers.UUIDField()
    post_id = serializers.UUIDField()
    organization_id = serializers.CharField()
    organization_name = serializers.CharField()
    platform = serializers.CharField()
    social_account = serializers.CharField(allow_blank=True)
    content_type = serializers.CharField(allow_blank=True)
    title = serializers.CharField()
    scheduled_at = serializers.DateTimeField()
    timezone = serializers.CharField()
    status = serializers.CharField()


class DashboardNotificationSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    organization_id = serializers.CharField()
    organization_name = serializers.CharField()
    plan_name = serializers.CharField(required=False)
    expiry_date = serializers.DateField(required=False)
    post_id = serializers.UUIDField(required=False)
    target_id = serializers.UUIDField(required=False)
    platform = serializers.CharField(required=False)
    social_account = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    post_title = serializers.CharField(required=False, allow_blank=True)
    post_preview = serializers.CharField(required=False, allow_blank=True)
    failure_reason = serializers.CharField(required=False, allow_blank=True)
    days_remaining = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField()


class DashboardRecentActivitySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    event_type = serializers.CharField()
    occurred_at = serializers.DateTimeField()
    organization_id = serializers.CharField()
    organization_name = serializers.CharField()
    actor_name = serializers.CharField(allow_blank=True)
    actor_email = serializers.EmailField(allow_blank=True)
    metadata = serializers.DictField()
    post_title = serializers.CharField(required=False, allow_blank=True)
    post_preview = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False, allow_blank=True)
    social_account = serializers.CharField(required=False, allow_blank=True)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    published_at = serializers.DateTimeField(required=False, allow_null=True)
    plan_name = serializers.CharField(required=False, allow_blank=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)


class DashboardSerializer(serializers.Serializer):
    statistics = DashboardStatisticsSerializer()
    today_schedule = DashboardScheduleItemSerializer(many=True)
    notifications = DashboardNotificationSerializer(many=True)
    recent_activities = DashboardRecentActivitySerializer(many=True)
