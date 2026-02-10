from django.urls import path

from .views import (
    CallHistoryView,
    CreateDMView,
    EnrollmentWebhookView,
    MessageHistoryView,
    RoomListView,
)

urlpatterns = [
    path("rooms/", RoomListView.as_view(), name="room-list"),
    path(
        "rooms/<int:room_id>/messages/",
        MessageHistoryView.as_view(),
        name="room-messages",
    ),
    path(
        "rooms/<int:room_id>/calls/",
        CallHistoryView.as_view(),
        name="call-history",
    ),
    path("rooms/dm/create/", CreateDMView.as_view(), name="create-dm"),
    path(
        "webhook/enrollment/",
        EnrollmentWebhookView.as_view(),
        name="enrollment-webhook",
    ),
]
