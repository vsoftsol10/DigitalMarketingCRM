from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import (
    JSONParser,
    FormParser,
    MultiPartParser,
)
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)

from apps.accounts.services import (
    change_user_password,
    login_user,
)

from apps.common.utils import api_response


# ============================================================
# LOGIN
# ============================================================


class LoginAPIView(APIView):
    """
    Authenticate user and issue JWT access/refresh tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = login_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        refresh = RefreshToken.for_user(user)

        return api_response(
            message="Login successful.",
            data={
                "access": str(
                    refresh.access_token
                ),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
        )


# ============================================================
# CURRENT USER / PROFILE
# ============================================================


class MeAPIView(APIView):
    """
    Fetch and update the currently authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get(self, request):
        serializer = UserSerializer(
            request.user
        )

        return api_response(
            message="User fetched successfully.",
            data=serializer.data,
        )

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        return api_response(
            message="Profile updated successfully.",
            data=UserSerializer(user).data,
        )


# ============================================================
# CHANGE PASSWORD
# ============================================================


class ChangePasswordAPIView(APIView):
    """
    Change password for the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        change_user_password(
            user=request.user,
            new_password=serializer.validated_data[
                "new_password"
            ],
        )

        return api_response(
            message="Password changed successfully.",
            data=None,
        )


# ============================================================
# LOGOUT
# ============================================================


class LogoutAPIView(APIView):
    """
    Blacklist the current user's refresh token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get(
            "refresh"
        )

        if refresh:
            token = RefreshToken(refresh)
            token.blacklist()

        return api_response(
            message="Logged out successfully.",
            data=None,
        )