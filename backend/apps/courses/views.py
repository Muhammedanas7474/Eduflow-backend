from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Course, Lesson
from .permissions import IsAdminOrInstructor
from .serializers import CourseListSerializer, CourseSerializer, LessonSerializer


class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_active", "is_approved"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.select_related("tenant", "created_by").filter(
            tenant=user.tenant
        )

        if user.role == "ADMIN":
            # Admin sees all courses
            return queryset
        elif user.role == "INSTRUCTOR":
            # Instructor sees only their own courses
            return queryset.filter(created_by=user)
        else:
            # Students see only approved and active courses
            return queryset.filter(is_approved=True, is_active=True)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrInstructor()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseSerializer

    @swagger_auto_schema(
        method="post",
        responses={
            200: "Course approved successfully.",
            403: "Only admins can approve courses.",
        },
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Admin-only endpoint to approve a course"""
        if request.user.role != "ADMIN":
            return Response(
                {"detail": "Only admins can approve courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        course = self.get_object()
        course.is_approved = True
        course.save()
        return Response(
            {
                "detail": "Course approved successfully.",
                "is_approved": True,
                "id": course.id,
            }
        )

    @swagger_auto_schema(
        method="post",
        responses={200: "Course rejected.", 403: "Only admins can reject courses."},
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Admin-only endpoint to reject/unapprove a course"""
        if request.user.role != "ADMIN":
            return Response(
                {"detail": "Only admins can reject courses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        course = self.get_object()
        course.is_approved = False
        course.save()
        return Response(
            {"detail": "Course rejected.", "is_approved": False, "id": course.id}
        )


class LessonViewSet(ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        course_id = self.request.query_params.get("course")
        queryset = Lesson.objects.select_related("course", "created_by").filter(
            tenant=self.request.user.tenant, is_active=True
        )
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, created_by=self.request.user)
