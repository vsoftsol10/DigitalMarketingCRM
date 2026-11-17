from django.urls import path

from apps.accounts.views import (
    ChangePasswordAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    RateLimitedTokenRefreshView,
)

urlpatterns = [
    # Authentication
    path(
        "login/",
        LoginAPIView.as_view(),
        name="login",
    ),
    path(
        "refresh/",
        RateLimitedTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),
    # Current user
    path(
        "me/",
        MeAPIView.as_view(),
        name="me",
    ),
    # Password
    path(
        "change-password/",
        ChangePasswordAPIView.as_view(),
        name="change-password",
    ),
]
