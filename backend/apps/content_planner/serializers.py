from rest_framework import serializers

from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialAccountStatus

from .models import ContentIdea


class SelectedSocialAccountSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = SocialAccount
        fields = ("id", "platform", "display_name")

    def get_display_name(self, obj):
        return obj.account_name or obj.username or obj.platform_account_id


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

    organization_code = serializers.CharField(
        source="organization.organization_id",
        read_only=True,
    )

    organization = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    content_type = serializers.CharField(read_only=True)

    type = serializers.CharField(
        source="content_type",
        read_only=True,
    )

    selected_social_accounts = SelectedSocialAccountSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ContentIdea

        fields = (
            "id",
            "organization_id",
            "organization_code",
            "organization",
            "caption",
            "description",
            "content_type",
            "type",
            "target_publish_date",
            "target_publish_time",
            "selected_social_accounts",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "organization_id",
            "organization_code",
            "organization",
            "content_type",
            "type",
            "selected_social_accounts",
            "created_at",
            "updated_at",
        )


class ContentIdeaWriteSerializerMixin(serializers.Serializer):
    social_account_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        write_only=True,
    )

    def validate_organization(self, organization):
        request = self.context["request"]
        if organization.created_by_id != request.user.id:
            raise serializers.ValidationError("The selected organization is not available.")
        return organization

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        organization = attrs.get("organization", instance.organization if instance else None)
        account_ids = attrs.get("social_account_ids")
        target_time = attrs.get(
            "target_publish_time",
            instance.target_publish_time if instance else None,
        )
        content_type = attrs.get(
            "content_type",
            instance.content_type if instance else None,
        )

        if content_type not in {"POST", "REEL", "STORY"}:
            raise serializers.ValidationError(
                {"content_type": "Only POST, REEL, and STORY are supported."}
            )
        if target_time is None:
            raise serializers.ValidationError(
                {"target_publish_time": "Target publish time is required."}
            )

        if account_ids is None:
            account_ids = list(instance.selected_social_accounts.values_list("id", flat=True)) if instance else []
        if not account_ids:
            raise serializers.ValidationError(
                {"social_account_ids": "Select at least one publish account."}
            )
        if len(account_ids) != len(set(account_ids)):
            raise serializers.ValidationError(
                {"social_account_ids": "Duplicate social accounts are not allowed."}
            )

        accounts = SocialAccount.objects.filter(
            id__in=account_ids,
            organization=organization,
            is_deleted=False,
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        if accounts.count() != len(account_ids):
            raise serializers.ValidationError(
                {"social_account_ids": "Each account must belong to this organization and be connected and valid."}
            )

        attrs["selected_social_accounts"] = list(accounts)
        attrs.pop("social_account_ids", None)
        return attrs


class ContentIdeaCreateSerializer(ContentIdeaWriteSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for creating a content idea.
    """

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(
            is_deleted=False,
        ),
        required=True,
    )

    target_publish_time = serializers.TimeField(required=True)

    class Meta:
        model = ContentIdea

        fields = (
            "organization",
            "caption",
            "description",
            "content_type",
            "target_publish_date",
            "target_publish_time",
            "social_account_ids",
        )

    def validate_caption(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Caption is required.")

        return value

    def validate_description(self, value):
        return value.strip()
class ContentIdeaUpdateSerializer(ContentIdeaWriteSerializerMixin, serializers.ModelSerializer):
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
            "caption",
            "description",
            "content_type",
            "target_publish_date",
            "target_publish_time",
            "social_account_ids",
        )

    def validate_caption(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Caption is required.")

        return value

    def validate_description(self, value):
        return value.strip()

