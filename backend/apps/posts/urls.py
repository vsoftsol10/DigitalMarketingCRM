from django.urls import path

from .views import (
    OrganizationPostDetailAPIView,
    OrganizationPostListCreateAPIView,
    OrganizationPostMediaCreateAPIView,
)

urlpatterns = [
    path(
        "organizations/<str:organization_id>/",
        OrganizationPostListCreateAPIView.as_view(),
        name="organization-post-list-create",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/",
        OrganizationPostDetailAPIView.as_view(),
        name="organization-post-detail",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/media/",
        OrganizationPostMediaCreateAPIView.as_view(),
        name="organization-post-media-create",
    ),
]