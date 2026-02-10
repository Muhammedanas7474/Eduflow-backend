from django.db import models
from django.utils import timezone


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

    def get_member_ids(self):
        """Return list of user IDs in this room."""
        return list(self.members.values_list("user_id", flat=True))

    def get_other_member_id(self, user_id):
        """For DM rooms, return the other participant's user ID."""
        if self.type != "DM":
            return None
        member = self.members.exclude(user_id=user_id).first()
        return member.user_id if member else None

    @classmethod
    def get_or_create_dm(cls, tenant_id, user_id_1, user_id_2):
        """
        Find existing DM room between two users, or create a new one.
        Returns (room, created) tuple.
        """
        # Look for existing DM rooms where both users are members
        existing = (
            cls.objects.filter(
                type="DM",
                tenant_id=tenant_id,
                members__user_id=user_id_1,
            )
            .filter(members__user_id=user_id_2)
            .first()
        )

        if existing:
            return existing, False

        # Create new DM room
        room = cls.objects.create(
            tenant_id=tenant_id,
            name=f"DM_{min(user_id_1, user_id_2)}_{max(user_id_1, user_id_2)}",
            type="DM",
        )
        ChatRoomMember.objects.create(room=room, user_id=user_id_1)
        ChatRoomMember.objects.create(room=room, user_id=user_id_2)

        return room, True


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
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender_id} in {self.room.name}"


class CallSession(models.Model):
    STATUS_CHOICES = (
        ("RINGING", "Ringing"),
        ("ACTIVE", "Active"),
        ("ENDED", "Ended"),
        ("MISSED", "Missed"),
        ("REJECTED", "Rejected"),
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="calls")
    caller_id = models.IntegerField(db_index=True)
    callee_id = models.IntegerField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="RINGING")
    started_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Call {self.caller_id} → {self.callee_id} ({self.status})"

    @property
    def duration(self):
        """Return call duration in seconds, or None if not answered."""
        if self.answered_at and self.ended_at:
            return int((self.ended_at - self.answered_at).total_seconds())
        return None

    def end_call(self):
        self.status = "ENDED"
        self.ended_at = timezone.now()
        self.save()

    def reject_call(self):
        self.status = "REJECTED"
        self.ended_at = timezone.now()
        self.save()

    def mark_missed(self):
        self.status = "MISSED"
        self.ended_at = timezone.now()
        self.save()

    def answer_call(self):
        self.status = "ACTIVE"
        self.answered_at = timezone.now()
        self.save()
