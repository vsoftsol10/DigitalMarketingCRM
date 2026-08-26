from django.urls import path

from .views import MetaOAuthStartAPIView

urlpatterns = [
    path("oauth/start/", MetaOAuthStartAPIView.as_view(), name="meta-oauth-start"),
]
