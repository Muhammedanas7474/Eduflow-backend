from rest_framework import serializers

from .models import ChatMessage, ChatRoom, ChatRoomMember


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
        ]

    def get_sender_name(self, obj):
        # We need to get user name from backend service
        # For now, return a placeholder - ideally this would call the backend API
        return f"User {obj.sender_id}"


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "type",
            "course_id",
            "last_message",
            "unread_count",
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
            # If never read, all messages are unread? Or specific limit?
            # For MVP, count all.
            return obj.messages.count()

        return obj.messages.filter(created_at__gt=member.last_read_at).count()
