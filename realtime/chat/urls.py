from django.urls import path

from .views import EnrollmentWebhookView, MessageHistoryView, RoomListView

urlpatterns = [
    path("rooms/", RoomListView.as_view(), name="room-list"),
    path(
        "rooms/<int:room_id>/messages/",
        MessageHistoryView.as_view(),
        name="room-messages",
    ),
    path(
        "webhook/enrollment/",
        EnrollmentWebhookView.as_view(),
        name="enrollment-webhook",
    ),
]
