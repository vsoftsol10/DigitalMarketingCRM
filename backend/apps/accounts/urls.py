# from django.urls import path

# from rest_framework_simplejwt.views import (
#     TokenRefreshView,
# )

# from apps.accounts.views import (
#     LoginAPIView,
#     LogoutAPIView,
#     MeAPIView,
# )

# urlpatterns = [
#     path("login/", LoginAPIView.as_view(), name="login"),
#     path("refresh/", TokenRefreshView.as_view(), name="refresh"),
#     path("logout/", LogoutAPIView.as_view(), name="logout"),
#     path("me/", MeAPIView.as_view(), name="me"),
# ]


from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from apps.accounts.views import (
    ChangePasswordAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
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
        TokenRefreshView.as_view(),
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
