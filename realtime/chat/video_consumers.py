from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import CallSession, ChatMessage, ChatRoom, ChatRoomMember


class VideoCallConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for WebRTC video call signaling.
    Handles SDP offer/answer exchange, ICE candidates, and call lifecycle.
    """

    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.call_group = f"call_{self.user.tenant_id}_{self.room_id}"

        # Verify user is a member of this DM room
        is_member = await self.check_membership()
        if not is_member:
            await self.close()
            return

        # Join call signaling group
        await self.channel_layer.group_add(self.call_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "call_group"):
            # Notify the other user that this user disconnected
            await self.channel_layer.group_send(
                self.call_group,
                {
                    "type": "call.ended",
                    "user_id": self.user.id,
                    "reason": "disconnected",
                },
            )
            await self.channel_layer.group_discard(self.call_group, self.channel_name)

    async def receive_json(self, content):
        msg_type = content.get("type")

        if msg_type == "call_offer":
            await self.handle_call_offer(content)
        elif msg_type == "call_answer":
            await self.handle_call_answer(content)
        elif msg_type == "ice_candidate":
            await self.handle_ice_candidate(content)
        elif msg_type == "call_end":
            await self.handle_call_end(content)
        elif msg_type == "call_reject":
            await self.handle_call_reject(content)

    # --- Call Offer ---

    async def handle_call_offer(self, content):
        """Caller sends SDP offer to start a call."""
        callee_id = content.get("callee_id")
        sdp = content.get("sdp")

        # Create call session in DB
        call = await self.create_call_session(callee_id)

        await self.channel_layer.group_send(
            self.call_group,
            {
                "type": "call.offer",
                "caller_id": self.user.id,
                "caller_name": self.user.full_name,
                "callee_id": callee_id,
                "sdp": sdp,
                "call_id": call.id if call else None,
            },
        )

    async def call_offer(self, event):
        # Only send to the callee, not back to the caller
        if event["callee_id"] == self.user.id:
            await self.send_json(
                {
                    "type": "incoming_call",
                    "caller_id": event["caller_id"],
                    "caller_name": event["caller_name"],
                    "sdp": event["sdp"],
                    "call_id": event["call_id"],
                }
            )

    # --- Call Answer ---

    @database_sync_to_async
    def create_system_message(self, content):
        try:
            room = ChatRoom.objects.get(
                id=int(self.room_id), tenant_id=self.user.tenant_id
            )
            return ChatMessage.objects.create(
                room=room,
                sender_id=self.user.id,
                content=content,
                is_system_message=True,
            )
        except Exception as e:
            print(f"Error creating system message: {e}")
            return None

    # --- Call Lifecycle with System Messages ---

    async def handle_call_answer(self, content):
        """Callee sends SDP answer to accept the call."""
        call_id = content.get("call_id")
        sdp = content.get("sdp")

        # Update call session
        await self.answer_call_session(call_id)

        # Notify signaling group
        await self.channel_layer.group_send(
            self.call_group,
            {
                "type": "call.answer",
                "answerer_id": self.user.id,
                "sdp": sdp,
                "call_id": call_id,
            },
        )

        # Create system message
        message = await self.create_system_message("📞 Video call started")
        if message:
            # Broadcast to chat group (ChatConsumer)
            chat_group = f"tenant_{self.user.tenant_id}_{self.room_id}"
            await self.channel_layer.group_send(
                chat_group,
                {
                    "type": "chat.message",
                    "id": message.id,
                    "message": message.content,
                    "user_id": self.user.id,
                    "full_name": "System",
                    "created_at": str(message.created_at),
                    "is_system_message": True,
                },
            )

    async def handle_call_end(self, content):
        """End an active call."""
        call_id = content.get("call_id")
        duration = await self.end_call_session(call_id)

        await self.channel_layer.group_send(
            self.call_group,
            {
                "type": "call.ended",
                "user_id": self.user.id,
                "reason": "ended",
                "call_id": call_id,
            },
        )

        # System message for call end
        duration_str = f" ({duration}s)" if duration else ""
        content = f"📞 Video call ended{duration_str}"
        message = await self.create_system_message(content)
        if message:
            chat_group = f"tenant_{self.user.tenant_id}_{self.room_id}"
            await self.channel_layer.group_send(
                chat_group,
                {
                    "type": "chat.message",
                    "id": message.id,
                    "message": message.content,
                    "user_id": self.user.id,
                    "full_name": "System",
                    "created_at": str(message.created_at),
                    "is_system_message": True,
                },
            )

    async def handle_call_reject(self, content):
        """Reject an incoming call."""
        call_id = content.get("call_id")
        await self.reject_call_session(call_id)

        await self.channel_layer.group_send(
            self.call_group,
            {
                "type": "call.rejected",
                "user_id": self.user.id,
                "call_id": call_id,
            },
        )

        # System message
        message = await self.create_system_message("📞 Video call declined")
        if message:
            chat_group = f"tenant_{self.user.tenant_id}_{self.room_id}"
            await self.channel_layer.group_send(
                chat_group,
                {
                    "type": "chat.message",
                    "id": message.id,
                    "message": message.content,
                    "user_id": self.user.id,
                    "full_name": "System",
                    "created_at": str(message.created_at),
                    "is_system_message": True,
                },
            )

    # --- DB Operations ---

    @database_sync_to_async
    def check_membership(self):
        return ChatRoomMember.objects.filter(
            room_id=int(self.room_id), user_id=self.user.id
        ).exists()

    @database_sync_to_async
    def create_call_session(self, callee_id):
        try:
            room = ChatRoom.objects.get(
                id=int(self.room_id),
                type="DM",
                tenant_id=self.user.tenant_id,
            )
            return CallSession.objects.create(
                room=room,
                caller_id=self.user.id,
                callee_id=callee_id,
                status="RINGING",
            )
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def answer_call_session(self, call_id):
        try:
            call = CallSession.objects.get(id=call_id)
            call.answer_call()
        except CallSession.DoesNotExist:
            pass

    @database_sync_to_async
    def end_call_session(self, call_id):
        try:
            if call_id:
                call = CallSession.objects.get(id=call_id)
                call.end_call()
                return call.duration
        except CallSession.DoesNotExist:
            pass
        return None

    @database_sync_to_async
    def reject_call_session(self, call_id):
        try:
            if call_id:
                call = CallSession.objects.get(id=call_id)
                call.reject_call()
        except CallSession.DoesNotExist:
            pass
