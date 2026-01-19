from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.enrollments.models import Enrollment,LessonProgress
from apps.enrollments.serializers import EnrollmentCreateSerializer,LessonProgressCreateSerializer
from apps.common.permissions import IsAdmin
from apps.common.responses import success_response


class EnrollmentViewSet(ModelViewSet):
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        tenant = user.tenant

        qs = Enrollment.objects.filter(tenant=tenant)

        if user.role == "STUDENT":
            return qs.filter(student=user)

        if user.role == "INSTRUCTOR":
            return qs.filter(course__created_by=user)

        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return EnrollmentCreateSerializer
        return EnrollmentCreateSerializer  

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            success_response(
                data=serializer.data,
                message="Enrollments fetched successfully"
            )
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()

        return Response(
            success_response(
                data={
                    "id": enrollment.id,
                    "student": enrollment.student.id,
                    "course": enrollment.course.id
                },
                message="Student enrolled successfully"
            )
        )
    





class LessonProgressViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LessonProgressCreateSerializer
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user
        tenant = user.tenant

        qs = LessonProgress.objects.filter(tenant=tenant)

        if user.role == "STUDENT":
            return qs.filter(student=user)

        if user.role == "INSTRUCTOR":
            return qs.filter(lesson__course__created_by=user)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        progress = serializer.save()

        return Response(
            success_response(
                data={
                    "lesson": progress.lesson.id,
                    "completed": progress.is_completed,
                    "completed_at": progress.completed_at,
                },
                message="Lesson marked as completed"
            )
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            success_response(
                data=serializer.data,
                message="Lesson progress fetched successfully"
            )
        )

