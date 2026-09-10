# from django.urls import path

# from .views import (
#     MetaOAuthCallbackAPIView,
#     MetaOAuthStartAPIView,
# )

# urlpatterns = [
#     path(
#         "oauth/start/",
#         MetaOAuthStartAPIView.as_view(),
#         name="meta-oauth-start",
#     ),
#     path(
#         "oauth/callback/",
#         MetaOAuthCallbackAPIView.as_view(),
#         name="meta-oauth-callback",
#     ),
# ]

from django.urls import path

from .views import (
    MetaOAuthCallbackAPIView,
    MetaOAuthSelectionAPIView,
    MetaOAuthSelectionConfirmAPIView,
    MetaOAuthStartAPIView,
)

urlpatterns = [
    path(
        "oauth/start/",
        MetaOAuthStartAPIView.as_view(),
        name="meta-oauth-start",
    ),
    path(
        "oauth/callback/",
        MetaOAuthCallbackAPIView.as_view(),
        name="meta-oauth-callback",
    ),
    path(
        "oauth/selection/",
        MetaOAuthSelectionAPIView.as_view(),
        name="meta-oauth-selection",
    ),
    path(
        "oauth/selection/confirm/",
        MetaOAuthSelectionConfirmAPIView.as_view(),
        name="meta-oauth-selection-confirm",
    ),
]
