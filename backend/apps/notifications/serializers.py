from rest_framework import serializers


class UserNotificationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.CharField(source="event_type")
    title = serializers.CharField()
    message = serializers.CharField()
    organization_id = serializers.CharField(source="organization.organization_id")
    organization_name = serializers.CharField(source="organization.name")
    post_id = serializers.UUIDField(source="post_platform.post_id", allow_null=True)
    target_id = serializers.UUIDField(source="post_platform_id", allow_null=True)
    subscription_id = serializers.UUIDField(allow_null=True)
    plan_name = serializers.SerializerMethodField()
    expiry_date = serializers.DateField(source="subscription.expiry_date", allow_null=True)
    platform = serializers.CharField(source="post_platform.platform", allow_null=True)
    post_title = serializers.SerializerMethodField()
    read_at = serializers.DateTimeField(allow_null=True)
    is_read = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_plan_name(self, notification):
        subscription = notification.subscription
        plan = subscription.plan if subscription else None
        return plan.name if plan and not plan.is_deleted else ""

    def get_post_title(self, notification):
        target = notification.post_platform
        if not target or not target.post_id:
            return ""
        caption = " ".join((target.post.caption or "").split())
        return caption[:120]

    def get_is_read(self, notification):
        return notification.read_at is not None
