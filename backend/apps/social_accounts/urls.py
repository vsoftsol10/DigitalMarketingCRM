# from django.urls import path

# from .views import (
#     OrganizationSocialAccountDetailAPIView,
#     OrganizationSocialAccountListCreateAPIView,
# )

# urlpatterns = [
#     path(
#         "organizations/<str:organization_id>/social-accounts/",
#         OrganizationSocialAccountListCreateAPIView.as_view(),
#         name="organization-social-account-list-create",
#     ),
#     path(
#         "organizations/<str:organization_id>/social-accounts/<uuid:social_account_id>/",
#         OrganizationSocialAccountDetailAPIView.as_view(),
#         name="organization-social-account-detail",
#     ),
# ]

from django.urls import path

from .views import (
    OrganizationSocialAccountDetailAPIView,
    OrganizationSocialAccountDisconnectAPIView,
    OrganizationSocialAccountListCreateAPIView,
)
from .invitation_views import (
    OrganizationEmailInvitationCreateAPIView,
    OrganizationInvitationEmailResendAPIView,
    OrganizationInvitationEmailRetryAPIView,
    OrganizationInvitationEmailSendAPIView,
    OrganizationInvitationListAPIView,
    OrganizationInvitationRevokeAPIView,
    OrganizationShareInvitationCreateAPIView,
    PublicInvitationClaimAPIView,
    PublicInvitationAcceptanceCancelAPIView,
    PublicInvitationAcceptanceCompleteAPIView,
    PublicInvitationOAuthAttemptCreateAPIView,
    PublicInvitationPlatformResumeAPIView,
    PublicInvitationValidateAPIView,
)

urlpatterns = [
    path(
        "organizations/<str:organization_id>/social-accounts/",
        OrganizationSocialAccountListCreateAPIView.as_view(),
        name="organization-social-account-list-create",
    ),
    path(
        "organizations/<str:organization_id>/social-accounts/<uuid:social_account_id>/",
        OrganizationSocialAccountDetailAPIView.as_view(),
        name="organization-social-account-detail",
    ),
    path(
        "organizations/<str:organization_id>/social-accounts/<uuid:social_account_id>/disconnect/",
        OrganizationSocialAccountDisconnectAPIView.as_view(),
        name="organization-social-account-disconnect",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/",
        OrganizationInvitationListAPIView.as_view(),
        name="organization-social-account-invitation-list",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/email/",
        OrganizationEmailInvitationCreateAPIView.as_view(),
        name="organization-social-account-invitation-email-create",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/<uuid:invitation_id>/email/send/",
        OrganizationInvitationEmailSendAPIView.as_view(),
        name="organization-social-account-invitation-email-send",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/<uuid:invitation_id>/email/retry/",
        OrganizationInvitationEmailRetryAPIView.as_view(),
        name="organization-social-account-invitation-email-retry",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/<uuid:invitation_id>/email/resend/",
        OrganizationInvitationEmailResendAPIView.as_view(),
        name="organization-social-account-invitation-email-resend",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/share-link/",
        OrganizationShareInvitationCreateAPIView.as_view(),
        name="organization-social-account-invitation-share-create",
    ),
    path(
        "organizations/<str:organization_id>/social-account-invitations/<uuid:invitation_id>/revoke/",
        OrganizationInvitationRevokeAPIView.as_view(),
        name="organization-social-account-invitation-revoke",
    ),
    path(
        "social-account-invitations/validate/",
        PublicInvitationValidateAPIView.as_view(),
        name="social-account-invitation-validate",
    ),
    path(
        "social-account-invitations/claim/",
        PublicInvitationClaimAPIView.as_view(),
        name="social-account-invitation-claim",
    ),
    path(
        "social-account-invitations/cancel/",
        PublicInvitationAcceptanceCancelAPIView.as_view(),
        name="social-account-invitation-cancel",
    ),
    path(
        "social-account-invitations/complete/",
        PublicInvitationAcceptanceCompleteAPIView.as_view(),
        name="social-account-invitation-complete",
    ),
    path(
        "social-account-invitations/oauth/attempt/",
        PublicInvitationOAuthAttemptCreateAPIView.as_view(),
        name="social-account-invitation-oauth-attempt",
    ),
    path(
        "social-account-invitations/resume/",
        PublicInvitationPlatformResumeAPIView.as_view(),
        name="social-account-invitation-platform-resume",
    ),
]
