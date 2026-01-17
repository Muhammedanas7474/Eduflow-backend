from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.enrollments.models import Enrollment
from apps.enrollments.serializers import EnrollmentCreateSerializer
from apps.common.permissions import IsAdmin
from apps.common.responses import success_response


class EnrollmentViewSet(ModelViewSet):
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        tenant = user.tenant

        qs = Enrollment.objects.filter(tenant=tenant)

        # STUDENT → only own enrollments
        if user.role == "STUDENT":
            return qs.filter(student=user)

        # INSTRUCTOR → courses created by instructor
        if user.role == "INSTRUCTOR":
            return qs.filter(course__created_by=user)

        # ADMIN → all enrollments in tenant
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return EnrollmentCreateSerializer
        return EnrollmentCreateSerializer  # read handled manually

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
