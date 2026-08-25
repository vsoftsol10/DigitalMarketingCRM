from django.urls import path

from .views import (
    OrganizationListCreateAPIView,
    OrganizationDetailAPIView,
    OrganizationSubscriptionRenewAPIView,
    OrganizationSubscriptionChangePlanAPIView,
    OrganizationSubscriptionCancelAPIView,
    OrganizationSubscriptionStartAPIView,
    OrganizationSubscriptionHistoryAPIView,
)

from apps.social_accounts.views import (
    OrganizationSocialAccountListCreateAPIView,
    OrganizationSocialAccountDetailAPIView,
)

urlpatterns = [
    # ========================================================
    # ORGANIZATIONS
    # ========================================================
    path(
        "",
        OrganizationListCreateAPIView.as_view(),
        name="organization-list-create",
    ),
    # ========================================================
    # SOCIAL ACCOUNTS
    # ========================================================
    path(
        "<str:organization_id>/social-accounts/",
        OrganizationSocialAccountListCreateAPIView.as_view(),
        name="organization-social-account-list-create",
    ),
    path(
        "<str:organization_id>/social-accounts/<uuid:social_account_id>/",
        OrganizationSocialAccountDetailAPIView.as_view(),
        name="organization-social-account-detail",
    ),
    # ========================================================
    # ORGANIZATION DETAIL
    # ========================================================
    path(
        "<str:organization_id>/",
        OrganizationDetailAPIView.as_view(),
        name="organization-detail",
    ),
    path(
        "<str:organization_id>/subscription/renew/",
        OrganizationSubscriptionRenewAPIView.as_view(),
        name="organization-subscription-renew",
    ),
    path(
        "<str:organization_id>/subscription/change-plan/",
        OrganizationSubscriptionChangePlanAPIView.as_view(),
        name="organization-subscription-change-plan",
    ),
    path(
        "<str:organization_id>/subscription/cancel/",
        OrganizationSubscriptionCancelAPIView.as_view(),
        name="organization-subscription-cancel",
    ),
    path(
        "<str:organization_id>/subscription/start/",
        OrganizationSubscriptionStartAPIView.as_view(),
        name="organization-subscription-start",
    ),
    path(
        "<str:organization_id>/subscription/history/",
        OrganizationSubscriptionHistoryAPIView.as_view(),
        name="organization-subscription-history",
    ),
]
