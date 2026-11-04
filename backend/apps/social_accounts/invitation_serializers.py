from rest_framework import serializers

from .models import (
    SocialAccountInvitationMode,
    SocialAccountInvitationOAuthPlatform,
    SocialPlatform,
)


SUPPORTED_INVITATION_PLATFORMS = {
    SocialPlatform.FACEBOOK,
    SocialPlatform.INSTAGRAM,
}


class InvitationCreateSerializer(serializers.Serializer):
    platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(SUPPORTED_INVITATION_PLATFORMS)),
        allow_empty=False,
    )

    def validate_platforms(self, platforms):
        return sorted(set(platforms))


class EmailInvitationCreateSerializer(InvitationCreateSerializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().casefold()


class ShareInvitationCreateSerializer(InvitationCreateSerializer):
    usage_limit = serializers.IntegerField(min_value=1, max_value=100, default=10)


class InvitationTokenSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, max_length=200, trim_whitespace=True)


class InvitationClaimSerializer(InvitationTokenSerializer):
    platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(SUPPORTED_INVITATION_PLATFORMS)),
        allow_empty=False,
        required=False,
    )

    def validate_platforms(self, platforms):
        return sorted(set(platforms))


class InvitationAcceptanceCancelSerializer(serializers.Serializer):
    acceptance_token = serializers.CharField(
        min_length=32,
        max_length=200,
        trim_whitespace=True,
    )


class InvitationAcceptanceCompleteSerializer(serializers.Serializer):
    acceptance_token = serializers.CharField(
        min_length=32,
        max_length=200,
        trim_whitespace=True,
        required=False,
    )
    resumption_token = serializers.CharField(
        min_length=32,
        max_length=4096,
        trim_whitespace=True,
        required=False,
    )

    def validate(self, attrs):
        if bool(attrs.get("acceptance_token")) == bool(attrs.get("resumption_token")):
            raise serializers.ValidationError("Provide one invitation session credential.")
        return attrs


class InvitationOAuthAttemptCreateSerializer(serializers.Serializer):
    acceptance_token = serializers.CharField(
        min_length=32,
        max_length=200,
        trim_whitespace=True,
    )
    platform = serializers.ChoiceField(
        choices=SocialAccountInvitationOAuthPlatform.choices,
    )


class InvitationPlatformResumptionSerializer(serializers.Serializer):
    resumption_token = serializers.CharField(
        min_length=32,
        max_length=4096,
        trim_whitespace=True,
    )
    platform = serializers.ChoiceField(
        choices=SocialAccountInvitationOAuthPlatform.choices,
    )

