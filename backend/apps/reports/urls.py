from django.urls import path

from .views import InsightsReportPngAPIView, InsightsReportPreviewAPIView


urlpatterns = [
    path("insights/preview/", InsightsReportPreviewAPIView.as_view(), name="insights-report-preview"),
    path("insights/png/", InsightsReportPngAPIView.as_view(), name="insights-report-png"),
]
