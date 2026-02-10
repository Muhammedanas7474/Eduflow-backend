from rest_framework import serializers

from .models import CallSession, ChatMessage, ChatRoom, ChatRoomMember


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sender_id",
            "sender_name",
            "content",
            "file_url",
            "file_type",
            "timestamp",
            "is_system_message",
            "is_read",
        ]

    def get_sender_name(self, obj):
        return f"User {obj.sender_id}"


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "type",
            "course_id",
            "last_message",
            "unread_count",
            "other_user",
            "created_at",
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by("-created_at").first()
        if last_msg:
            return ChatMessageSerializer(last_msg).data
        return None

    def get_unread_count(self, obj):
        user_id = self.context.get("user_id")
        if not user_id:
            return 0

        member = ChatRoomMember.objects.filter(room=obj, user_id=user_id).first()
        if not member or not member.last_read_at:
            return obj.messages.count()

        return obj.messages.filter(created_at__gt=member.last_read_at).count()

    def get_other_user(self, obj):
        """For DM rooms, return the other user's ID."""
        if obj.type != "DM":
            return None
        user_id = self.context.get("user_id")
        if not user_id:
            return None
        other_id = obj.get_other_member_id(user_id)
        return {"user_id": other_id} if other_id else None


class CallSessionSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()

    class Meta:
        model = CallSession
        fields = [
            "id",
            "room",
            "caller_id",
            "callee_id",
            "status",
            "started_at",
            "answered_at",
            "ended_at",
            "duration",
        ]
        read_only_fields = [
            "id",
            "started_at",
            "answered_at",
            "ended_at",
            "duration",
        ]
