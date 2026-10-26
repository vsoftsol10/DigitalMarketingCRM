from django.urls import path

from .api_views import (
    UserNotificationClearAPIView,
    UserNotificationListAPIView,
    UserNotificationReadAPIView,
)


urlpatterns = [
    path("", UserNotificationListAPIView.as_view(), name="user-notification-list"),
    path("clear/", UserNotificationClearAPIView.as_view(), name="user-notification-clear"),
    path("<uuid:notification_id>/read/", UserNotificationReadAPIView.as_view(), name="user-notification-read"),
]
