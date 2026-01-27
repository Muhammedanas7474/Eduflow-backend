from apps.notifications.views import (
    MarkAllNotificationsReadAPIView,
    MarkNotificationReadAPIView,
    NotificationListAPIView,
    UnreadNotificationCountAPIView,
)
from django.urls import path

urlpatterns = [
    path("", NotificationListAPIView.as_view()),
    path("unread-count/", UnreadNotificationCountAPIView.as_view()),
    path("<int:notification_id>/read/", MarkNotificationReadAPIView.as_view()),
    path("read-all/", MarkAllNotificationsReadAPIView.as_view()),
]
