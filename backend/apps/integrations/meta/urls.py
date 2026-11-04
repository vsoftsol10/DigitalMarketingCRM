from django.urls import path

from .views import (
    MetaOAuthCallbackAPIView,
    MetaOAuthSelectionAPIView,
    MetaOAuthSelectionConfirmAPIView,
    MetaOAuthSelectionFinishAPIView,
    MetaOAuthStartAPIView,
)
from .invitation_views import (
    InvitationFacebookOAuthCallbackAPIView,
    InvitationFacebookOAuthStartAPIView,
    InvitationFacebookPageAddAPIView,
    InvitationFacebookPageSelectionAPIView,
)

urlpatterns = [
    path(
        "invitation/oauth/start/",
        InvitationFacebookOAuthStartAPIView.as_view(),
        name="meta-invitation-oauth-start",
    ),
    path(
        "invitation/oauth/callback/",
        InvitationFacebookOAuthCallbackAPIView.as_view(),
        name="meta-invitation-oauth-callback",
    ),
    path(
        "invitation/oauth/selection/",
        InvitationFacebookPageSelectionAPIView.as_view(),
        name="meta-invitation-oauth-selection",
    ),
    path(
        "invitation/oauth/selection/add/",
        InvitationFacebookPageAddAPIView.as_view(),
        name="meta-invitation-oauth-selection-add",
    ),
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
    path(
        "oauth/selection/finish/",
        MetaOAuthSelectionFinishAPIView.as_view(),
        name="meta-oauth-selection-finish",
    ),
]
