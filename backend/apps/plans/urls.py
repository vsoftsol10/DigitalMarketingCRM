from django.urls import path

from .views import (
    PlanListCreateAPIView,
    PlanDetailAPIView,
)


urlpatterns = [
    path(
        "",
        PlanListCreateAPIView.as_view(),
        name="plan-list-create",
    ),
    path(
        "<uuid:plan_id>/",
        PlanDetailAPIView.as_view(),
        name="plan-detail",
    ),
]