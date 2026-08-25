from rest_framework import serializers

from apps.organizations.models import Organization

from .models import ContentIdea

from .constants import CONTENT_TYPES_BY_PLATFORM


class ContentIdeaReadSerializer(serializers.ModelSerializer):
    """
    Frontend-facing serializer for reading content ideas.

    Keeps the response shape compatible with the current
    Content Planner frontend.
    """

    organization_id = serializers.UUIDField(
        source="organization.id",
        read_only=True,
    )

    organization = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    type = serializers.CharField(
        source="content_type",
        read_only=True,
    )

    goal = serializers.CharField(
        source="campaign_goal",
        read_only=True,
    )

    class Meta:
        model = ContentIdea

        fields = (
            "id",
            "organization_id",
            "organization",
            "title",
            "description",
            "platform",
            "type",
            "goal",
            "target_publish_date",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "organization_id",
            "organization",
            "type",
            "goal",
            "created_at",
            "updated_at",
        )


class ContentIdeaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a content idea.
    """

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(
            is_deleted=False,
        ),
        required=True,
    )

    class Meta:
        model = ContentIdea

        fields = (
            "organization",
            "title",
            "description",
            "platform",
            "content_type",
            "campaign_goal",
            "target_publish_date",
        )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Title is required.")

        return value

    def validate_description(self, value):
        return value.strip()

    def validate(self, attrs):
        platform = attrs.get("platform")
        content_type = attrs.get("content_type")

        allowed_types = CONTENT_TYPES_BY_PLATFORM.get(
            platform,
            set(),
        )

        if content_type not in allowed_types:
            raise serializers.ValidationError(
                {
                    "content_type": (
                        "Selected content type is not supported "
                        "by the selected platform."
                    )
                }
            )

        return attrs


class ContentIdeaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for partially updating a content idea.
    """

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(
            is_deleted=False,
        ),
        required=False,
    )

    class Meta:
        model = ContentIdea

        fields = (
            "organization",
            "title",
            "description",
            "platform",
            "content_type",
            "campaign_goal",
            "target_publish_date",
        )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Title is required.")

        return value

    def validate_description(self, value):
        return value.strip()

    def validate(self, attrs):
        platform = attrs.get(
            "platform",
            self.instance.platform,
        )

        content_type = attrs.get(
            "content_type",
            self.instance.content_type,
        )

        allowed_types = CONTENT_TYPES_BY_PLATFORM.get(
            platform,
            set(),
        )

        if content_type not in allowed_types:
            raise serializers.ValidationError(
                {
                    "content_type": (
                        "Selected content type is not supported "
                        "by the selected platform."
                    )
                }
            )

        return attrs
