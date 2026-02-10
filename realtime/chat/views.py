from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CallSession, ChatMessage, ChatRoom, ChatRoomMember
from .serializers import (
    CallSessionSerializer,
    ChatMessageSerializer,
    ChatRoomSerializer,
)


class RoomListView(generics.ListAPIView):
    """List chat rooms for the authenticated user. Filter by ?type=COURSE or ?type=DM"""

    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ChatRoom.objects.none()

        user_id = self.request.user.id
        tenant_id = self.request.user.tenant_id

        qs = ChatRoom.objects.filter(members__user_id=user_id, tenant_id=tenant_id)

        # Optional type filter
        room_type = self.request.query_params.get("type")
        if room_type in ("COURSE", "DM"):
            qs = qs.filter(type=room_type)

        return qs.order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["user_id"] = self.request.user.id
        return context


class MessageHistoryView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        user_id = self.request.user.id

        if not ChatRoomMember.objects.filter(room_id=room_id, user_id=user_id).exists():
            return ChatMessage.objects.none()

        return ChatMessage.objects.filter(room_id=room_id).order_by("created_at")


class CreateDMView(APIView):
    """
    Create or retrieve a DM room between the authenticated user and a target user.
    POST body: { "target_user_id": <int> }
    """

    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        target_user_id = request.data.get("target_user_id")
        if not target_user_id:
            return Response(
                {"error": "target_user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user_id = int(target_user_id)
        user_id = request.user.id
        tenant_id = request.user.tenant_id

        if target_user_id == user_id:
            return Response(
                {"error": "Cannot create DM with yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room, created = ChatRoom.get_or_create_dm(tenant_id, user_id, target_user_id)

        serializer = ChatRoomSerializer(room, context={"user_id": user_id})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CallHistoryView(generics.ListAPIView):
    """Get call history for a specific DM room."""

    serializer_class = CallSessionSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        user_id = self.request.user.id

        # Ensure user is a member of this room
        if not ChatRoomMember.objects.filter(room_id=room_id, user_id=user_id).exists():
            return CallSession.objects.none()

        return CallSession.objects.filter(room_id=room_id).order_by("-started_at")


class EnrollmentWebhookView(APIView):
    """
    Internal API called by Core Backend to add user to a course room.
    Also adds the course instructor if provided.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        course_id = request.data.get("course_id")
        user_id = request.data.get("user_id")
        tenant_id = request.data.get("tenant_id")
        course_name = request.data.get("course_name")
        instructor_id = request.data.get("instructor_id")

        if not all([course_id, user_id, tenant_id]):
            return Response(status=400)

        room = ChatRoom.objects.filter(course_id=course_id, tenant_id=tenant_id).first()

        if not room:
            room = ChatRoom.objects.create(
                course_id=course_id,
                tenant_id=tenant_id,
                name=course_name or f"Course {course_id}",
                type="COURSE",
            )

        ChatRoomMember.objects.get_or_create(room=room, user_id=user_id)

        if instructor_id:
            ChatRoomMember.objects.get_or_create(room=room, user_id=instructor_id)

        return Response({"status": "success", "room_id": room.id}, status=200)
