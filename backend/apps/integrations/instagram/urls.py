from django.urls import path

from .views import (
    InstagramOAuthCallbackAPIView,
    InstagramOAuthStartAPIView,
)
from .invitation_views import (
    InvitationInstagramConfirmAPIView,
    InvitationInstagramDeclineAPIView,
    InvitationInstagramOAuthCallbackAPIView,
    InvitationInstagramOAuthStartAPIView,
    InvitationInstagramPreviewAPIView,
)


urlpatterns = [
    path(
        "invitation/oauth/start/",
        InvitationInstagramOAuthStartAPIView.as_view(),
        name="instagram-invitation-oauth-start",
    ),
    path(
        "invitation/oauth/callback/",
        InvitationInstagramOAuthCallbackAPIView.as_view(),
        name="instagram-invitation-oauth-callback",
    ),
    path(
        "invitation/oauth/preview/",
        InvitationInstagramPreviewAPIView.as_view(),
        name="instagram-invitation-oauth-preview",
    ),
    path(
        "invitation/oauth/confirm/",
        InvitationInstagramConfirmAPIView.as_view(),
        name="instagram-invitation-oauth-confirm",
    ),
    path(
        "invitation/oauth/decline/",
        InvitationInstagramDeclineAPIView.as_view(),
        name="instagram-invitation-oauth-decline",
    ),
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
