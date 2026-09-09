from django.urls import path

from .views import AICaptionGenerateAPIView


urlpatterns = [
    path(
        "captions/generate/",
        AICaptionGenerateAPIView.as_view(),
        name="ai-caption-generate",
    ),
]