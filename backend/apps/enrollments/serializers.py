from rest_framework import serializers
from apps.enrollments.models import Enrollment
from apps.accounts.models import User
from apps.courses.models import Course
from apps.common.exceptions import AppException
from rest_framework import status


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["student", "course"]

    def validate(self, attrs):
        request = self.context["request"]
        admin_user = request.user
        tenant = admin_user.tenant

        student: User = attrs.get("student")
        course: Course = attrs.get("course")

        # 1️⃣ Tenant check
        if student.tenant_id != tenant.id:
            raise AppException(
                "Student does not belong to your tenant",
                status.HTTP_400_BAD_REQUEST
            )

        if course.tenant_id != tenant.id:
            raise AppException(
                "Course does not belong to your tenant",
                status.HTTP_400_BAD_REQUEST
            )

        # 2️⃣ Only STUDENT can be enrolled
        if student.role != "STUDENT":
            raise AppException(
                "Only students can be enrolled in courses",
                status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Duplicate enrollment check
        if Enrollment.objects.filter(
            tenant=tenant,
            student=student,
            course=course
        ).exists():
            raise AppException(
                "Student is already enrolled in this course",
                status.HTTP_400_BAD_REQUEST
            )

        # 4️⃣ Attach tenant automatically
        attrs["tenant"] = tenant

        return attrs
