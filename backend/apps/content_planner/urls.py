from django.urls import path

from .views import (
    ContentPlannerDetailAPIView,
    ContentPlannerListCreateAPIView,
)

urlpatterns = [
    path(
        "",
        ContentPlannerListCreateAPIView.as_view(),
        name="content-planner-list-create",
    ),
    path(
        "<uuid:idea_id>/",
        ContentPlannerDetailAPIView.as_view(),
        name="content-planner-detail",
    ),
]