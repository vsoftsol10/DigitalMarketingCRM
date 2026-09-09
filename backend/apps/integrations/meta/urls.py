from django.urls import path

from .views import (
    MetaOAuthCallbackAPIView,
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
]
    