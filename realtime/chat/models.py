from django.db import models


class ChatRoom(models.Model):
    ROOM_TYPES = (
        ("COURSE", "Course Group"),
        ("DM", "Direct Message"),
    )

    tenant_id = models.IntegerField(db_index=True)
    course_id = models.IntegerField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=ROOM_TYPES, default="COURSE")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class ChatRoomMember(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="members")
    user_id = models.IntegerField(db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("room", "user_id")

    def __str__(self):
        return f"User {self.user_id} in {self.room.name}"


class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender_id = models.IntegerField(db_index=True)
    content = models.TextField(blank=True)
    file_url = models.URLField(max_length=500, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_system_message = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender_id} in {self.room.name}"
