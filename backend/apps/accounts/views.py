import hashlib
import hmac

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import (
    JSONParser,
    FormParser,
    MultiPartParser,
)
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

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
from apps.common.throttles import RedisRateThrottle


def _login_subject_digest(subject):
    return hmac.new(
        str(settings.SECRET_KEY).encode("utf-8"),
        subject.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _login_source_ip(request):
    """Use the socket peer until the deployment explicitly trusts a proxy."""
    return str(request.META.get("REMOTE_ADDR") or "")


class LoginAccountRateThrottle(RedisRateThrottle):
    """Limit login attempts by source IP and normalized email identifier."""

    scope = "login"

    def _configured_limits(self):
        limits = super()._configured_limits()
        if len(limits) < 2:
            raise ImproperlyConfigured(
                "The login scope requires account-minute and IP-hour limits."
            )
        return [limits[0]]

    def _subject_digest(self, request):
        identifier = request.data.get("email", "")
        normalized_identifier = (
            identifier.strip().casefold()
            if isinstance(identifier, str)
            else ""
        )
        subject = f"login:ip:{_login_source_ip(request)}:account:{normalized_identifier}"
        return _login_subject_digest(subject)


class LoginIPRateThrottle(RedisRateThrottle):
    """Limit all login attempts from one DRF-trusted source IP."""

    scope = "login"

    def _configured_limits(self):
        limits = super()._configured_limits()
        if len(limits) < 2:
            raise ImproperlyConfigured(
                "The login scope requires account-minute and IP-hour limits."
            )
        return [limits[1]]

    def _subject_digest(self, request):
        return _login_subject_digest(f"login:ip:{_login_source_ip(request)}")


def _refresh_token_fingerprint(token):
    token_value = token if isinstance(token, str) else ""
    return hmac.new(
        str(settings.SECRET_KEY).encode("utf-8"),
        token_value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class RefreshTokenRateThrottle(RedisRateThrottle):
    """Limit refresh attempts by source IP and a keyed token fingerprint."""

    scope = "token_refresh"

    def _configured_limits(self):
        limits = super()._configured_limits()
        if len(limits) < 2:
            raise ImproperlyConfigured(
                "The token_refresh scope requires token-minute and IP-hour limits."
            )
        return [limits[0]]

    def _subject_digest(self, request):
        refresh_token = request.data.get("refresh", "")
        fingerprint = _refresh_token_fingerprint(refresh_token)
        subject = (
            f"token_refresh:ip:{_login_source_ip(request)}:token:{fingerprint}"
        )
        return _login_subject_digest(subject)


class RefreshIPRateThrottle(RedisRateThrottle):
    """Limit all refresh attempts from one source IP."""

    scope = "token_refresh"

    def _configured_limits(self):
        limits = super()._configured_limits()
        if len(limits) < 2:
            raise ImproperlyConfigured(
                "The token_refresh scope requires token-minute and IP-hour limits."
            )
        return [limits[1]]

    def _subject_digest(self, request):
        return _login_subject_digest(
            f"token_refresh:ip:{_login_source_ip(request)}"
        )


class RateLimitedTokenRefreshView(TokenRefreshView):
    """SimpleJWT refresh endpoint with endpoint-scoped Redis limits."""

    throttle_classes = [RefreshTokenRateThrottle, RefreshIPRateThrottle]


# ============================================================
# LOGIN
# ============================================================


class LoginAPIView(APIView):
    """
    Authenticate user and issue JWT access/refresh tokens.
    """

    permission_classes = [AllowAny]
    throttle_classes = [LoginAccountRateThrottle, LoginIPRateThrottle]

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
