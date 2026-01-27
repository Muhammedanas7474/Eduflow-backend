from apps.common.responses import success_response
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            tenant=request.user.tenant, user=request.user
        )

        serializer = NotificationSerializer(notifications, many=True)

        return Response(
            success_response(data=serializer.data, message="Notifications fetched")
        )


class MarkNotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = Notification.objects.filter(
            id=notification_id, tenant=request.user.tenant, user=request.user
        ).first()

        if notification:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        return Response(success_response(message="Notification marked as read"))


class MarkAllNotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(
            tenant=request.user.tenant, user=request.user, is_read=False
        ).update(is_read=True)

        return Response(success_response(message="All notifications marked as read"))


class UnreadNotificationCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            tenant=request.user.tenant, user=request.user, is_read=False
        ).count()

        return Response(success_response(data={"unread_count": count}))
