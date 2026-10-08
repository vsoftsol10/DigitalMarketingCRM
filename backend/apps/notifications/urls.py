from django.urls import path

from .api_views import UserNotificationListAPIView, UserNotificationReadAPIView


urlpatterns = [
    path("", UserNotificationListAPIView.as_view(), name="user-notification-list"),
    path("<uuid:notification_id>/read/", UserNotificationReadAPIView.as_view(), name="user-notification-read"),
]
