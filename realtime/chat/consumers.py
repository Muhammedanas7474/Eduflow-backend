from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .models import ChatMessage, ChatRoom, ChatRoomMember


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        # Use room_name as Room ID for DB lookup
        # If room_name is not numeric, we might need a slug lookup
        self.room_id = self.room_name
        self.room_group_name = f"tenant_{self.user.tenant_id}_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Update Read Status
        await self.update_read_status()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive_json(self, content):
        message_content = content.get("message", "")

        if not message_content:
            return

        # Save to DB
        message = await self.save_message(message_content)

        if message:
            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "id": message.id,
                    "message": message.content,
                    "user_id": self.user.id,
                    "full_name": self.user.full_name,
                    "created_at": str(message.created_at),
                },
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send_json(
            {
                "type": "chat_message",
                "id": event["id"],
                "message": event["message"],
                "user_id": event["user_id"],
                "sender_name": event.get("full_name", ""),
                "timestamp": event.get("created_at", ""),
            }
        )

    @database_sync_to_async
    def save_message(self, content):
        try:
            # Safe lookup
            room = ChatRoom.objects.get(
                id=int(self.room_id), tenant_id=self.user.tenant_id
            )

            return ChatMessage.objects.create(
                room=room, sender_id=self.user.id, content=content
            )
        except (ValueError, ChatRoom.DoesNotExist):
            return None

    @database_sync_to_async
    def update_read_status(self):
        try:
            room_id = int(self.room_id)
            room = ChatRoom.objects.get(id=room_id, tenant_id=self.user.tenant_id)
            ChatRoomMember.objects.update_or_create(
                room=room,
                user_id=self.user.id,
                defaults={"last_read_at": timezone.now()},
            )
        except Exception:
            pass
