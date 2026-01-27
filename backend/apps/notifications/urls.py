from django.urls import path
from apps.notifications.views import (
    NotificationListAPIView,
    MarkNotificationReadAPIView,
    MarkAllNotificationsReadAPIView,
    UnreadNotificationCountAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view()),
    path("unread-count/", UnreadNotificationCountAPIView.as_view()),
    path("<int:notification_id>/read/", MarkNotificationReadAPIView.as_view()),
    path("read-all/", MarkAllNotificationsReadAPIView.as_view()),
]
