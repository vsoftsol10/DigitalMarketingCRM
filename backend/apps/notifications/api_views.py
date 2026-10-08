from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.responses import success_response

from .models import UserNotification
from .selectors import get_user_notification_unread_count, get_user_notifications
from .serializers import UserNotificationSerializer


class UserNotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = get_user_notifications(user=request.user)
        return success_response(
            data={
                "notifications": UserNotificationSerializer(notifications, many=True).data,
                "unread_count": get_user_notification_unread_count(user=request.user),
            },
            message="Notifications fetched successfully.",
        )


class UserNotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = UserNotification.objects.filter(
            id=notification_id,
            recipient=request.user,
            organization__created_by=request.user,
            organization__is_deleted=False,
            is_deleted=False,
            resolved_at__isnull=True,
        ).first()
        if not notification:
            return Response({"detail": "Notification not found."}, status=404)

        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])

        return success_response(
            data={
                "notification": UserNotificationSerializer(notification).data,
                "unread_count": get_user_notification_unread_count(user=request.user),
            },
            message="Notification marked as read.",
        )
