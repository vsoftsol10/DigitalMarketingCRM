from django.urls import path

from .views import (
    CalendarEventDetailAPIView,
    CalendarEventsAPIView,
    CalendarFiltersAPIView,
    OrganizationPostDetailAPIView,
    OrganizationPostListCreateAPIView,
    OrganizationPostMediaCreateAPIView,
    OrganizationPostPublishNowAPIView,
    OrganizationPostScheduleAPIView,
    OrganizationPostTargetDetailAPIView,
    OrganizationPostTargetPublishNowAPIView,
    OrganizationPostTargetScheduleAPIView,
    OrganizationPostTargetRetryAPIView,
)

urlpatterns = [
    path("calendar/events/", CalendarEventsAPIView.as_view(), name="calendar-events"),
    path(
        "calendar/events/<uuid:target_id>/",
        CalendarEventDetailAPIView.as_view(),
        name="calendar-event-detail",
    ),
    path("calendar/filters/", CalendarFiltersAPIView.as_view(), name="calendar-filters"),
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
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/schedule/",
        OrganizationPostScheduleAPIView.as_view(),
        name="organization-post-schedule",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/publish-now/",
        OrganizationPostPublishNowAPIView.as_view(),
        name="organization-post-publish-now",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/targets/<uuid:target_id>/retry/",
        OrganizationPostTargetRetryAPIView.as_view(),
        name="organization-post-target-retry",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/targets/<uuid:target_id>/publish-now/",
        OrganizationPostTargetPublishNowAPIView.as_view(),
        name="organization-post-target-publish-now",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/targets/<uuid:target_id>/schedule/",
        OrganizationPostTargetScheduleAPIView.as_view(),
        name="organization-post-target-schedule",
    ),
    path(
        "organizations/<str:organization_id>/<uuid:post_id>/targets/<uuid:target_id>/",
        OrganizationPostTargetDetailAPIView.as_view(),
        name="organization-post-target-detail",
    ),
]
