from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from apps.accounts.models import User

# ============================================================
# USER SERIALIZER
# ============================================================


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "profile_image",
        )


# ============================================================
# PROFILE UPDATE SERIALIZER
# ============================================================


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "phone",
            "profile_image",
        )

    def validate_first_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("First name is required.")

        return value

    def validate_last_name(self, value):
        return value.strip()

    def validate_phone(self, value):
        return value.strip()

    def validate_profile_image(self, value):
        if value is None:
            return value

        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only JPEG, PNG, and WebP images are allowed."
            )

        max_size = 5 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "Profile image must be smaller than 5 MB."
            )

        return value


# ============================================================
# CHANGE PASSWORD
# ============================================================


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        user = self.context["request"].user

        # ------------------------------------------
        # CURRENT PASSWORD
        # ------------------------------------------

        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": ("Current password is incorrect.")}
            )

        # ------------------------------------------
        # CONFIRM PASSWORD
        # ------------------------------------------

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": ("Passwords do not match.")}
            )

        # ------------------------------------------
        # PREVENT SAME PASSWORD
        # ------------------------------------------

        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": (
                        "New password must be different " "from the current password."
                    )
                }
            )

        # ------------------------------------------
        # DJANGO PASSWORD VALIDATORS
        # ------------------------------------------

        validate_password(
            attrs["new_password"],
            user,
        )

        return attrs


# ============================================================
# LOGIN
# ============================================================


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
