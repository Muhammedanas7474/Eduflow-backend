from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .models import ChatMessage, ChatRoom, ChatRoomMember

# In-memory online users tracking: { tenant_id: { user_id: set(channel_names) } }
online_users = {}


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_id = self.room_name
        self.room_group_name = f"tenant_{self.user.tenant_id}_{self.room_name}"
        self.presence_group = f"presence_{self.user.tenant_id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Join presence group for online tracking
        await self.channel_layer.group_add(self.presence_group, self.channel_name)

        await self.accept()

        # Track online status
        tenant_id = self.user.tenant_id
        user_id = self.user.id
        if tenant_id not in online_users:
            online_users[tenant_id] = {}
        if user_id not in online_users[tenant_id]:
            online_users[tenant_id][user_id] = set()
        online_users[tenant_id][user_id].add(self.channel_name)

        # Broadcast that this user is now online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.presence",
                "user_id": user_id,
                "status": "online",
                "full_name": self.user.full_name,
            },
        )

        # Update read status
        await self.update_read_status()

        # Send current online users in this room to the newly connected user
        room_online = await self.get_room_online_users()
        await self.send_json(
            {
                "type": "online_users",
                "users": room_online,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            # Remove from online tracking
            tenant_id = self.user.tenant_id
            user_id = self.user.id
            if tenant_id in online_users and user_id in online_users[tenant_id]:
                online_users[tenant_id][user_id].discard(self.channel_name)
                if not online_users[tenant_id][user_id]:
                    del online_users[tenant_id][user_id]

                    # Broadcast offline status only if no more connections
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "user.presence",
                            "user_id": user_id,
                            "status": "offline",
                            "full_name": self.user.full_name,
                        },
                    )

            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            await self.channel_layer.group_discard(
                self.presence_group, self.channel_name
            )

    async def receive_json(self, content):
        msg_type = content.get("type", "chat_message")

        if msg_type == "chat_message":
            await self.handle_chat_message(content)
        elif msg_type == "typing":
            await self.handle_typing(content)
        elif msg_type == "read_receipt":
            await self.handle_read_receipt(content)

    # --- Chat Message ---

    async def handle_chat_message(self, content):
        message_content = content.get("message", "")
        if not message_content:
            return

        message = await self.save_message(message_content)
        if message:
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

    # --- Typing Indicator ---

    async def handle_typing(self, content):
        is_typing = content.get("is_typing", False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.typing",
                "user_id": self.user.id,
                "full_name": self.user.full_name,
                "is_typing": is_typing,
            },
        )

    async def user_typing(self, event):
        # Don't send typing indicator back to the sender
        if event["user_id"] == self.user.id:
            return
        await self.send_json(
            {
                "type": "typing",
                "user_id": event["user_id"],
                "full_name": event["full_name"],
                "is_typing": event["is_typing"],
            }
        )

    # --- Read Receipt ---

    async def handle_read_receipt(self, content):
        message_id = content.get("message_id")
        if message_id:
            await self.mark_message_read(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message.read",
                    "message_id": message_id,
                    "reader_id": self.user.id,
                },
            )

    async def message_read(self, event):
        if event["reader_id"] == self.user.id:
            return
        await self.send_json(
            {
                "type": "read_receipt",
                "message_id": event["message_id"],
                "reader_id": event["reader_id"],
            }
        )

    # --- Presence ---

    async def user_presence(self, event):
        await self.send_json(
            {
                "type": "presence",
                "user_id": event["user_id"],
                "status": event["status"],
                "full_name": event.get("full_name", ""),
            }
        )

    # --- DB Operations ---

    @database_sync_to_async
    def save_message(self, content):
        try:
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

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            ChatMessage.objects.filter(
                id=message_id,
                room__tenant_id=self.user.tenant_id,
            ).update(is_read=True)
        except Exception:
            pass

    @database_sync_to_async
    def get_room_online_users(self):
        """Get list of online user IDs who are members of the current room."""
        try:
            room_id = int(self.room_id)
            member_ids = list(
                ChatRoomMember.objects.filter(room_id=room_id).values_list(
                    "user_id", flat=True
                )
            )
            tenant_id = self.user.tenant_id
            tenant_online = online_users.get(tenant_id, {})
            return [uid for uid in member_ids if uid in tenant_online]
        except Exception:
            return []
