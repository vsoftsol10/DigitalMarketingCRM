from rest_framework import serializers

from .models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)
from .status import (
    SocialAccountLifecycleStatus,
)

# class SocialAccountReadSerializer(serializers.ModelSerializer):
#     """
#     Frontend-facing social account response.

#     Keeps the existing frontend field names unchanged
#     while exposing normalized database fields.
#     """

#     page_name = serializers.CharField(
#         source="account_name",
#         read_only=True,
#     )

#     connected = serializers.SerializerMethodField()

#     valid = serializers.BooleanField(
#         source="is_valid",
#         read_only=True,
#     )

#     last_sync = serializers.DateTimeField(
#         source="last_synced_at",
#         read_only=True,
#     )

#     class Meta:
#         model = SocialAccount

#         fields = (
#             "id",
#             "platform",
#             "page_name",
#             "username",
#             "profile_image",
#             "connected",
#             "valid",
#             "last_sync",
#         )

#         read_only_fields = fields

#     def get_connected(self, obj):
#         return obj.status == SocialAccountStatus.CONNECTED

class SocialAccountReadSerializer(serializers.ModelSerializer):
    """
    Frontend-facing social account response.

    Keeps existing frontend field names unchanged while also
    exposing normalized lifecycle information.
    """

    page_name = serializers.CharField(
        source="account_name",
        read_only=True,
    )

    connected = serializers.SerializerMethodField()

    valid = serializers.BooleanField(
        source="is_valid",
        read_only=True,
    )

    last_sync = serializers.DateTimeField(
        source="last_synced_at",
        read_only=True,
    )

    connection_status = serializers.CharField(
        source="status",
        read_only=True,
    )

    credential_status = serializers.SerializerMethodField()

    last_verified_at = serializers.SerializerMethodField()

    needs_reconnect = serializers.SerializerMethodField()

    class Meta:
        model = SocialAccount

        fields = (
            "id",
            "platform",
            "page_name",
            "username",
            "profile_image",

            # Existing frontend fields
            "connected",
            "valid",
            "last_sync",

            # Lifecycle fields
            "connection_status",
            "credential_status",
            "last_verified_at",
            "needs_reconnect",
        )

        read_only_fields = fields

    def get_connected(self, obj):
        return obj.status == SocialAccountStatus.CONNECTED

    def get_credential_status(self, obj):
        return SocialAccountLifecycleStatus.get_credential_status(
            obj,
        )

    def get_last_verified_at(self, obj):
        return SocialAccountLifecycleStatus.get_last_verified_at(
            obj,
        )

    def get_needs_reconnect(self, obj):
        credential_status = (
            SocialAccountLifecycleStatus.get_credential_status(
                obj,
            )
        )

        return SocialAccountLifecycleStatus.needs_reconnect(
            social_account=obj,
            credential_status=credential_status,
        )
class SocialAccountCreateSerializer(serializers.ModelSerializer):
    """
    Internal/manual social-account creation contract.

    This serializer is NOT an OAuth implementation.
    OAuth-generated account data will later be created
    through the integration/service layer.
    """

    class Meta:
        model = SocialAccount

        fields = (
            "platform",
            "platform_account_id",
            "account_name",
            "username",
            "profile_image",
        )

    def validate_platform(self, value):
        value = value.strip().lower()

        allowed_platforms = {choice.value for choice in SocialPlatform}

        if value not in allowed_platforms:
            raise serializers.ValidationError("Invalid social platform.")

        return value

    def validate_platform_account_id(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Platform account ID is required.")

        return value

    def validate_account_name(
        self,
        value,
    ):
        return value.strip()

    def validate_username(
        self,
        value,
    ):
        return value.strip()


class SocialAccountUpdateSerializer(serializers.ModelSerializer):
    """
    Update contract for an existing social account.

    Only editable display metadata is allowed.

    Platform identity, connection status, validity,
    OAuth tokens and synchronization fields are
    server/integration controlled.
    """

    class Meta:
        model = SocialAccount

        fields = (
            "account_name",
            "username",
            "profile_image",
        )

    def validate_account_name(self, value):
        return value.strip()

    def validate_username(self, value):
        return value.strip()
