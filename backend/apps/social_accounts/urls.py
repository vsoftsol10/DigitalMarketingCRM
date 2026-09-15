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
]
