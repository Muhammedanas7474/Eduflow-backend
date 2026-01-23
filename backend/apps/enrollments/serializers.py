from rest_framework import serializers
from apps.enrollments.models import Enrollment,LessonProgress,EnrollmentRequest
from apps.accounts.models import User
from apps.courses.models import Course
from apps.common.exceptions import AppException
from rest_framework import status
from apps.courses.models import Lesson


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

        
        if student.role != "STUDENT":
            raise AppException(
                "Only students can be enrolled in courses",
                status.HTTP_400_BAD_REQUEST
            )

        
        if Enrollment.objects.filter(
            tenant=tenant,
            student=student,
            course=course
        ).exists():
            raise AppException(
                "Student is already enrolled in this course",
                status.HTTP_400_BAD_REQUEST
            )

        attrs["tenant"] = tenant

        return attrs


class LessonProgressListSerializer(serializers.ModelSerializer):
    """Serializer for listing lesson progress with completion status"""
    class Meta:
        model = LessonProgress
        fields = ["id", "lesson", "is_completed", "completed_at"]


class LessonProgressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ["lesson"]

    def validate(self, attrs):
        request = self.context["request"]
        user: User = request.user
        tenant = user.tenant
        lesson: Lesson = attrs.get("lesson")

       
        if user.role != "STUDENT":
            raise AppException(
                "Only students can mark lesson progress",
                status.HTTP_403_FORBIDDEN
            )

     
        if lesson.tenant_id != tenant.id:
            raise AppException(
                "Lesson does not belong to your tenant",
                status.HTTP_400_BAD_REQUEST
            )

        if not Enrollment.objects.filter(
            tenant=tenant,
            student=user,
            course=lesson.course
        ).exists():
            raise AppException(
                "You are not enrolled in this course",
                status.HTTP_403_FORBIDDEN
            )

        if LessonProgress.objects.filter(
            tenant=tenant,
            student=user,
            lesson=lesson
        ).exists():
            raise AppException(
                "Lesson progress already exists",
                status.HTTP_400_BAD_REQUEST
            )

        
        attrs["tenant"] = tenant
        attrs["student"] = user

        return attrs
    

class EnrollmentRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing enrollment requests with full details"""
    student = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    
    class Meta:
        model = EnrollmentRequest
        fields = ["id", "student", "student_name", "course", "course_title", "status", "requested_at"]
    
    def get_student(self, obj):
        return obj.student.id if obj.student else None
    
    def get_student_name(self, obj):
        return obj.student.full_name if obj.student else "Unknown"
    
    def get_course_title(self, obj):
        return obj.course.title if obj.course else "Unknown"


class EnrollmentRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentRequest
        fields = ["course"]

    def validate(self, attrs):
        request = self.context["request"]
        student: User = request.user
        tenant = student.tenant
        course: Course = attrs.get("course")

        
        if student.role != "STUDENT":
            raise AppException(
                "Only students can request enrollment",
                status.HTTP_403_FORBIDDEN
            )

       
        if course.tenant_id != tenant.id:
            raise AppException(
                "Course does not belong to your tenant",
                status.HTTP_400_BAD_REQUEST
            )

        
        if Enrollment.objects.filter(
            tenant=tenant,
            student=student,
            course=course
        ).exists():
            raise AppException(
                "You are already enrolled in this course",
                status.HTTP_400_BAD_REQUEST
            )

        
        if EnrollmentRequest.objects.filter(
            tenant=tenant,
            student=student,
            course=course
        ).exists():
            raise AppException(
                "Enrollment request already submitted",
                status.HTTP_400_BAD_REQUEST
            )

        attrs["tenant"] = tenant
        attrs["student"] = student

        return attrs