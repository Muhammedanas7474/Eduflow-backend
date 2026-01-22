from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Course,Lesson
from .serializers import CourseSerializer, CourseListSerializer,LessonSerializer
from .permissions import IsAdminOrInstructor
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]


    def get_queryset(self):
        return Course.objects.filter(
            tenant=self.request.user.tenant
        )


    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrInstructor()]
        return super().get_permissions()
    

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            created_by=self.request.user
        )
    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseSerializer



class LessonViewSet(ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        course_id = self.request.query_params.get("course")
        queryset = Lesson.objects.filter(
            tenant=self.request.user.tenant,
            is_active=True
        )
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            created_by=self.request.user
        )

