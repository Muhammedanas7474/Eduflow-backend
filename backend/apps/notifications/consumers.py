from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        """
        Receives messages from channel layer
        """
        await self.send_json(
            {
                "type": "notification",
                "message": event["message"],
                "created_at": event["created_at"],
            }
        )

    async def chat_message_global(self, event):
        """
        Receives global chat notifications
        """
        await self.send_json(
            {
                "type": "chat_notification",
                "room_id": event["room_id"],
                "sender_name": event["sender_name"],
                "message": event["message"],
                "created_at": event["created_at"],
            }
        )
