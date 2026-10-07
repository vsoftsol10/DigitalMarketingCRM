from django.urls import path

from .views import (
    InsightsAccountDataAPIView,
    InsightsAccountSnapshotAPIView,
    InsightsAccountSnapshotContentAPIView,
    InsightsAccountSyncAPIView,
    InsightsOrganizationAccountListAPIView,
    InsightsOrganizationListAPIView,
)


urlpatterns = [
    path(
        "organizations/",
        InsightsOrganizationListAPIView.as_view(),
        name="insights-organization-list",
    ),
    path(
        "organizations/<str:organization_id>/accounts/",
        InsightsOrganizationAccountListAPIView.as_view(),
        name="insights-organization-account-list",
    ),
    path(
        "organizations/<str:organization_id>/accounts/<uuid:social_account_id>/snapshot/",
        InsightsAccountSnapshotAPIView.as_view(),
        name="insights-account-snapshot",
    ),
    path(
        "organizations/<str:organization_id>/accounts/<uuid:social_account_id>/snapshot/content/",
        InsightsAccountSnapshotContentAPIView.as_view(),
        name="insights-account-snapshot-content",
    ),
    path(
        "organizations/<str:organization_id>/accounts/<uuid:social_account_id>/sync/",
        InsightsAccountSyncAPIView.as_view(),
        name="insights-account-sync",
    ),
    path(
        "organizations/<str:organization_id>/accounts/<uuid:social_account_id>/",
        InsightsAccountDataAPIView.as_view(),
        name="insights-account-data",
    ),
]
