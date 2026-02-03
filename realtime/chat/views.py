from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatRoom, ChatRoomMember
from .serializers import ChatMessageSerializer, ChatRoomSerializer

# We need a custom permission or authentication because 'request.user' is not a Django User model here
# The realtime service uses JWTAuthMiddleware, but validation for HTTP requests might need specific setup.
# For now, we assume standardized JWT Auth is applied to HTTP requests in settings.


class RoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer

    permission_classes = [AllowAny]

    def get_queryset(self):
        print(f"DEBUG: User: {self.request.user}, Auth: {self.request.auth}")
        print(f"DEBUG: IsAuthenticated: {self.request.user.is_authenticated}")
        # Filter rooms where the user is a member
        # User ID comes from request.user (if using SimpleJWT) or Token
        # In this isolated service, we might need to parse the token manually if not configured.
        # Assuming standard DRF JWT Auth is working.
        if not self.request.user.is_authenticated:
            return ChatRoom.objects.none()

        user_id = self.request.user.id
        tenant_id = self.request.user.tenant_id

        return ChatRoom.objects.filter(
            members__user_id=user_id, tenant_id=tenant_id
        ).order_by(
            "-created_at"
        )  # Should ideally sort by last_message time

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_id"] = self.request.user.id
        return context


class MessageHistoryView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        # Ensure user is member
        user_id = self.request.user.id

        if not ChatRoomMember.objects.filter(room_id=room_id, user_id=user_id).exists():
            return ChatMessage.objects.none()

        return ChatMessage.objects.filter(room_id=room_id).order_by("created_at")


class EnrollmentWebhookView(APIView):
    """
    Internal API called by Core Backend to add user to a course room.
    Also adds the course instructor if provided.
    """

    permission_classes = [AllowAny]  # Should be protected by internal secret/IP

    def post(self, request):
        # Validate internal secret!
        # if request.headers.get('X-Internal-Secret') != settings.INTERNAL_SECRET:
        #    return Response(status=403)

        course_id = request.data.get("course_id")
        user_id = request.data.get("user_id")
        tenant_id = request.data.get("tenant_id")
        course_name = request.data.get("course_name")
        instructor_id = request.data.get("instructor_id")

        if not all([course_id, user_id, tenant_id]):
            return Response(status=400)

        # 1. Get or Create Room for Course (handle potential duplicates)
        room = ChatRoom.objects.filter(course_id=course_id, tenant_id=tenant_id).first()

        if not room:
            room = ChatRoom.objects.create(
                course_id=course_id,
                tenant_id=tenant_id,
                name=course_name or f"Course {course_id}",
                type="COURSE",
            )

        # 2. Add Student to Room
        ChatRoomMember.objects.get_or_create(room=room, user_id=user_id)

        # 3. Add Instructor to Room (if provided)
        if instructor_id:
            ChatRoomMember.objects.get_or_create(room=room, user_id=instructor_id)

        return Response({"status": "success", "room_id": room.id}, status=200)
