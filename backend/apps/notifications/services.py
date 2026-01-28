from apps.notifications.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def create_notification(*, tenant, user, type, message):
    notification = Notification.objects.create(
        tenant=tenant, user=user, type=type, message=message
    )

    # Send via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "notify",
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
        },
    )

    return notification
