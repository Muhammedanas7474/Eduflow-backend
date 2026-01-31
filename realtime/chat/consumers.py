import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat rooms with tenant isolation.

    Room groups are namespaced by tenant_id to ensure users from
    different tenants cannot see each other's messages.

    Group naming: chat_tenant_{tenant_id}_{room_name}
    """

    async def connect(self):
        user = self.scope.get("user")

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            # Close without accepting - this results in code 1006 in browser
            await self.close(code=4001)
            return

        # Store user info from JWT claims
        self.user_id = user.id
        self.tenant_id = user.tenant_id
        self.user_name = user.full_name or f"User_{user.id}"
        self.role = user.role

        # Get room from URL
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]

        # 🔐 TENANT ISOLATION: Room groups are namespaced by tenant_id
        # Users from tenant 1 in room "general" -> chat_tenant_1_general
        # Users from tenant 2 in room "general" -> chat_tenant_2_general
        # They will NOT see each other's messages!
        self.room_group_name = f"chat_tenant_{self.tenant_id}_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Send welcome message with user and tenant info
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connected",
                    "room": self.room_name,
                    "tenant_id": self.tenant_id,
                    "user_id": self.user_id,
                    "user_name": self.user_name,
                    "role": self.role,
                    "message": f"Welcome {self.user_name}! You are in tenant {self.tenant_id}, room '{self.room_name}'.",
                }
            )
        )

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        # Parse incoming message
        try:
            data = json.loads(text_data)
            message = data.get("message", text_data)
        except json.JSONDecodeError:
            message = text_data

        # Broadcast message to room group with user info
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user_id": self.user_id,
                "user_name": self.user_name,
                "tenant_id": self.tenant_id,
            },
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": event["message"],
                    "user_id": event["user_id"],
                    "user_name": event["user_name"],
                    "tenant_id": event["tenant_id"],
                }
            )
        )
