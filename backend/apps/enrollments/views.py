from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.enrollments.models import Enrollment,LessonProgress,EnrollmentRequest
from apps.enrollments.serializers import EnrollmentCreateSerializer,LessonProgressCreateSerializer,LessonProgressListSerializer,EnrollmentRequestCreateSerializer,EnrollmentRequestListSerializer
from apps.common.permissions import IsAdmin,IsInstructor
from apps.common.responses import success_response
from apps.common.exceptions import AppException
from apps.courses.models import Course
from rest_framework import status
from django.utils import timezone
from apps.courses.models import Lesson
from django.db import transaction
from apps.enrollments.tasks import enrollment_approved_task


class EnrollmentViewSet(ModelViewSet):
    http_method_names = ["get", "post"]
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
        user = request.user
        tenant = user.tenant

        # Enhanced response with progress data
        enrollments_data = []
        for enrollment in queryset:
            course = enrollment.course
            total_lessons = Lesson.objects.filter(course=course, is_active=True).count()
            completed_lessons = 0
            
            if user.role == "STUDENT":
                completed_lessons = LessonProgress.objects.filter(
                    tenant=tenant,
                    student=user,
                    lesson__course=course,
                    is_completed=True
                ).count()
            
            progress_percentage = round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0)
            
            enrollments_data.append({
                "id": enrollment.id,
                "course": enrollment.course.id,
                "course_title": course.title,
                "course_description": course.description,
                "enrolled_at": enrollment.enrolled_at,
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "progress_percentage": progress_percentage,
            })

        return Response(
            success_response(
                data=enrollments_data,
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

    def get_serializer_class(self):
        if self.action == "list":
            return LessonProgressListSerializer
        return LessonProgressCreateSerializer

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




class InstructorCourseEnrollmentsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, course_id):
        instructor = request.user
        tenant = instructor.tenant

        # 1️⃣ Validate course ownership
        try:
            course = Course.objects.get(
                id=course_id,
                tenant=tenant,
                created_by=instructor
            )
        except Course.DoesNotExist:
            raise AppException(
                "Course not found or access denied",
                status.HTTP_404_NOT_FOUND
            )

        # 2️⃣ Fetch enrollments
        enrollments = Enrollment.objects.filter(
            tenant=tenant,
            course=course
        ).select_related("student")

        data = [
            {
                "student_id": e.student.id,
                "student_name": e.student.full_name,
                "student_phone": e.student.phone_number,
                "enrolled_at": e.enrolled_at,
            }
            for e in enrollments
        ]

        return Response(
            success_response(
                data=data,
                message="Enrolled students fetched successfully"
            )
        )
    

class EnrollmentRequestViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentRequestCreateSerializer
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user
        tenant = user.tenant

        if user.role == "STUDENT":
            return EnrollmentRequest.objects.filter(
                tenant=tenant,
                student=user
            )

        return EnrollmentRequest.objects.filter(tenant=tenant)

    def get_serializer_class(self):
        if self.action == "list":
            return EnrollmentRequestListSerializer
        return EnrollmentRequestCreateSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            success_response(
                data=serializer.data,
                message="Enrollment requests fetched successfully"
            )
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        req = serializer.save()

        return Response(
            success_response(
                data={
                    "id": req.id,
                    "course": req.course.id,
                    "status": req.status
                },
                message="Enrollment request submitted"
            )
        )


class AdminEnrollmentRequestReviewAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, request_id):
        action = request.data.get("action")
        admin = request.user
        tenant = admin.tenant

        if action not in ["approve", "reject"]:
            raise AppException(
                "Invalid action. Use approve or reject",
                status.HTTP_400_BAD_REQUEST
            )

        try:
            enroll_req = EnrollmentRequest.objects.get(
                id=request_id,
                tenant=tenant
            )
        except EnrollmentRequest.DoesNotExist:
            raise AppException(
                "Enrollment request not found",
                status.HTTP_404_NOT_FOUND
            )

        if enroll_req.status != "PENDING":
            raise AppException(
                "Enrollment request already reviewed",
                status.HTTP_400_BAD_REQUEST
            )

        enroll_req.reviewed_by = admin
        enroll_req.reviewed_at = timezone.now()

        if action == "approve":
            with transaction.atomic():
                enrollment = Enrollment.objects.create(
                    tenant=tenant,
                    student=enroll_req.student,
                    course=enroll_req.course
                )
                enroll_req.status = "APPROVED"
                enroll_req.save()

                transaction.on_commit(
                    lambda: enrollment_approved_task.delay(
                        tenant_id=tenant.id,
                        enrollment_id=enrollment.id
                    )
                )
        else:
            enroll_req.status = "REJECTED"
            enroll_req.save()

        return Response(
            success_response(
                data={
                    "request_id": enroll_req.id,
                    "status": enroll_req.status
                },
                message=f"Enrollment request {enroll_req.status.lower()}"
            )
        )


class InstructorEnrollmentRequestReviewAPIView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request, request_id):
        action = request.data.get("action")
        instructor = request.user
        tenant = instructor.tenant

        if action not in ["approve", "reject"]:
            raise AppException(
                "Invalid action. Use approve or reject",
                status.HTTP_400_BAD_REQUEST
            )

        try:
            enroll_req = EnrollmentRequest.objects.get(
                id=request_id,
                tenant=tenant
            )
        except EnrollmentRequest.DoesNotExist:
            raise AppException(
                "Enrollment request not found",
                status.HTTP_404_NOT_FOUND
            )

        if enroll_req.course.created_by != instructor:
            raise AppException(
                "You can only review requests for your own courses",
                status.HTTP_403_FORBIDDEN
            )

        if enroll_req.status != "PENDING":
            raise AppException(
                "Enrollment request already reviewed",
                status.HTTP_400_BAD_REQUEST
            )

        enroll_req.reviewed_by = instructor
        enroll_req.reviewed_at = timezone.now()

        if action == "approve":
            with transaction.atomic():
                enrollment = Enrollment.objects.create(
                    tenant=tenant,
                    student=enroll_req.student,
                    course=enroll_req.course
                )
                enroll_req.status = "APPROVED"
                enroll_req.save()

                transaction.on_commit(
                    lambda: enrollment_approved_task.delay(
                        tenant_id=tenant.id,
                        enrollment_id=enrollment.id
                    )
                )
        else:
            enroll_req.status = "REJECTED"
            enroll_req.save()

        return Response(
            success_response(
                data={
                    "request_id": enroll_req.id,
                    "status": enroll_req.status
                },
                message=f"Enrollment request {enroll_req.status.lower()}"
            )
        )

class InstructorCourseProgressAPIView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, course_id):
        instructor = request.user
        tenant = instructor.tenant

        try:
            course = Course.objects.get(
                id=course_id,
                tenant=tenant,
                created_by=instructor
            )
        except Course.DoesNotExist:
            raise AppException(
                "Course not found or access denied",
                status.HTTP_404_NOT_FOUND
            )

        total_students = Enrollment.objects.filter(
            tenant=tenant,
            course=course
        ).count()

        lessons = Lesson.objects.filter(
            tenant=tenant,
            course=course
        )

        lesson_stats = []
        for lesson in lessons:
            completed_count = LessonProgress.objects.filter(
                tenant=tenant,
                lesson=lesson,
                is_completed=True
            ).count()

            lesson_stats.append({
                "lesson_id": lesson.id,
                "lesson_title": lesson.title,
                "completed_students": completed_count,
                "total_students": total_students
            })

        return Response(
            success_response(
                data={
                    "course_id": course.id,
                    "course_title": course.title,
                    "total_students": total_students,
                    "lessons": lesson_stats
                },
                message="Course progress fetched successfully"
            )
        )