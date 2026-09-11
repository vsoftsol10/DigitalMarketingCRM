from django.urls import path

from .views import (
    InstagramOAuthCallbackAPIView,
    InstagramOAuthStartAPIView,
)


urlpatterns = [
    path(
        "oauth/start/",
        InstagramOAuthStartAPIView.as_view(),
        name="instagram-oauth-start",
    ),
    path(
        "oauth/callback/",
        InstagramOAuthCallbackAPIView.as_view(),
        name="instagram-oauth-callback",
    ),
]