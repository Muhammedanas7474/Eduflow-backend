from datetime import timedelta

from apps.accounts.models import User
from apps.accounts.serializers import (
    AdminCreateUserSerializer,
    AdminUpdateUserStatusSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    VerifyOTPSerializer,
)
from apps.common.exceptions import AppException
from apps.common.permissions import IsAdmin, IsInstructor, IsStudent
from apps.common.responses import error_response, success_response
from apps.courses.models import Course
from apps.enrollments.models import Enrollment, EnrollmentRequest
from apps.tenants.models import Tenant
from django.conf import settings
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .utils import delete_otp, get_otp, send_otp


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(
                "OTP verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                        "role": openapi.Schema(type=openapi.TYPE_STRING),
                        "access_expiry": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        try:
            serializer = VerifyOTPSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone = serializer.validated_data["phone_number"]
            otp_input = serializer.validated_data["otp"]
            purpose = serializer.validated_data["purpose"]

            user = User.objects.filter(phone_number=phone).first()
            if not user:
                raise AppException("User not found")

            stored_otp = get_otp(
                tenant_id=user.tenant_id,
                phone=phone,
                purpose=purpose,
            )

            if not stored_otp:
                raise AppException("OTP expired or not found")

            if str(stored_otp) != str(otp_input):
                raise AppException("Invalid OTP")

            delete_otp(
                tenant_id=user.tenant_id,
                phone=phone,
                purpose=purpose,
            )

            user.is_phone_verified = True
            user.is_active = True
            user.save(update_fields=["is_phone_verified", "is_active"])

            # 🔐 Generate JWT
            refresh = RefreshToken.for_user(user)

            # ✅ Custom claims (required for realtime service)
            refresh["tenant_id"] = user.tenant_id
            refresh["role"] = user.role
            refresh["user_id"] = user.id

            access_token = str(refresh.access_token)

            response = Response(
                {
                    "success": True,
                    "message": "OTP verified successfully",
                    "data": {
                        "access": access_token,  # ✅ FIXED
                        "refresh": str(refresh),
                        "role": user.role,
                        "access_expiry": str(
                            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds
                        ),
                        "user": {
                            "id": user.id,
                            "full_name": user.full_name,
                            "email": user.email,
                            "phone_number": user.phone_number,
                            "role": user.role,
                            "is_active": user.is_active,
                            "is_phone_verified": user.is_phone_verified,
                            "tenant": user.tenant.name if user.tenant else None,
                        },
                    },
                },
                status=status.HTTP_200_OK,
            )

            # ✅ Cookies (unchanged)
            response.set_cookie(
                key=settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token"),
                value=access_token,
                expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
                secure=not settings.DEBUG,
                httponly=True,
                samesite="Lax",
            )
            response.set_cookie(
                key=settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token"),
                value=str(refresh),
                expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                secure=not settings.DEBUG,
                httponly=True,
                samesite="Lax",
            )

            print("ACCESS TOKEN (WS):", access_token)
            return response

        except AppException as e:
            return Response(
                {"success": False, "message": e.message, "data": None},
                status=e.status_code,
            )


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        print(f"DEBUG: Refresh Request Cookies: {request.COOKIES}")
        print(f"DEBUG: Refresh Request Data: {request.data}")

        refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
        )

        if refresh_token:
            request.data["refresh"] = refresh_token

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        token = serializer.validated_data

        response = Response(
            success_response(
                message="Token refreshed successfully",
                data={
                    "access_expiry": str(
                        settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds
                    )
                },
            ),
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key=settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token"),
            value=token["access"],
            expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
            secure=not settings.DEBUG,
            httponly=True,
            samesite="Lax",
        )

        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response(
            success_response(message="Logged out successfully"),
            status=status.HTTP_200_OK,
        )
        response.delete_cookie(settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token"))
        response.delete_cookie(
            settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
        )
        return response


class WebSocketTokenView(APIView):
    """
    Returns a fresh access token for WebSocket authentication.

    Since WebSockets cannot access HTTP-only cookies, the frontend needs
    to call this endpoint to get a token to pass via query string.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Generate a fresh access token with custom claims
        refresh = RefreshToken.for_user(user)
        refresh["tenant_id"] = user.tenant_id
        refresh["role"] = user.role
        refresh["full_name"] = user.full_name or ""

        return Response(
            success_response(
                message="WebSocket token generated",
                data={
                    "token": str(refresh.access_token),
                    "expires_in": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds,
                },
            ),
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: "Registration successful. OTP sent.",
            409: "User already exists",
        },
    )
    def post(self, request):

        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if User.objects.filter(
                phone_number=serializer.validated_data["phone_number"]
            ).exists():
                raise AppException(
                    "User already exists", status_code=409, code="USER_EXISTS"
                )

            tenant = Tenant.objects.get(id=serializer.validated_data["tenant_id"])

            user = User.objects.create_user(
                phone_number=serializer.validated_data["phone_number"],
                password=serializer.validated_data["password"],
                tenant=tenant,
            )

            user.full_name = serializer.validated_data["full_name"]
            user.email = serializer.validated_data["email"]
            user.role = "STUDENT"
            user.is_active = False
            user.is_phone_verified = False
            user.save()

            send_otp(
                tenant_id=user.tenant_id,
                phone=user.phone_number,
                purpose="REGISTER",
            )

            return Response(
                success_response(message="Registration successful. OTP sent."),
                status=201,
            )

        except AppException as e:
            return Response(error_response(e.message, e.code), status=e.status_code)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: "OTP sent for login",
            401: "Invalid credentials",
            403: "Account disabled",
            404: "User not found",
        },
    )
    def post(self, request):

        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone = serializer.validated_data["phone_number"]
            phone = serializer.validated_data["phone_number"]
            password = serializer.validated_data["password"]
            tenant_id = int(serializer.validated_data["tenant_id"])

            user = User.objects.filter(phone_number=phone, tenant_id=tenant_id).first()

            if not user:
                raise AppException("User not found", status_code=404)

            if not user.check_password(password):
                raise AppException(
                    "Invalid phone number or password",
                    status_code=401,
                    code="INVALID_CREDENTIALS",
                )

            if not user.is_active:
                raise AppException("Account disabled", status_code=403)

            send_otp(
                tenant_id=tenant_id,
                phone=phone,
                purpose="LOGIN",
            )

            return Response(success_response(message="OTP sent for login"), status=200)

        except AppException as e:
            return Response(error_response(e.message, e.code), status=e.status_code)


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @swagger_auto_schema(responses={200: "Admin dashboard stats"})
    def get(self, request):

        tenant = request.user.tenant
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Statistics
        total_users = User.objects.filter(tenant=tenant).count()
        total_students = User.objects.filter(tenant=tenant, role="STUDENT").count()
        total_instructors = User.objects.filter(
            tenant=tenant, role="INSTRUCTOR"
        ).count()
        total_courses = Course.objects.filter(tenant=tenant).count()
        active_courses = Course.objects.filter(tenant=tenant, is_active=True).count()
        pending_approvals = EnrollmentRequest.objects.filter(
            tenant=tenant, status="PENDING"
        ).count()
        total_enrollments = Enrollment.objects.filter(tenant=tenant).count()
        enrollments_this_week = Enrollment.objects.filter(
            tenant=tenant, enrolled_at__gte=week_ago
        ).count()

        return Response(
            success_response(
                message="Admin Dashboard",
                data={
                    "role": request.user.role,
                    "stats": {
                        "total_users": total_users,
                        "total_students": total_students,
                        "total_instructors": total_instructors,
                        "total_courses": total_courses,
                        "active_courses": active_courses,
                        "pending_approvals": pending_approvals,
                        "total_enrollments": total_enrollments,
                        "enrollments_this_week": enrollments_this_week,
                    },
                },
            )
        )


class InstructorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    @swagger_auto_schema(responses={200: "Instructor dashboard stats"})
    def get(self, request):
        from apps.courses.models import Course, Lesson
        from apps.enrollments.models import (
            Enrollment,
            EnrollmentRequest,
            LessonProgress,
        )

        instructor = request.user
        tenant = instructor.tenant

        # Get instructor's courses
        my_courses = Course.objects.filter(tenant=tenant, created_by=instructor)

        # Statistics
        total_courses = my_courses.count()
        active_courses = my_courses.filter(is_active=True).count()
        total_lessons = Lesson.objects.filter(
            tenant=tenant, course__in=my_courses
        ).count()
        total_students = (
            Enrollment.objects.filter(tenant=tenant, course__in=my_courses)
            .values("student")
            .distinct()
            .count()
        )
        pending_enrollments = EnrollmentRequest.objects.filter(
            tenant=tenant, course__in=my_courses, status="PENDING"
        ).count()

        # Calculate average completion rate
        total_progress = 0
        total_possible = 0
        for course in my_courses:
            lessons_count = Lesson.objects.filter(course=course, is_active=True).count()
            if lessons_count > 0:
                enrollments = Enrollment.objects.filter(course=course)
                for enrollment in enrollments:
                    completed = LessonProgress.objects.filter(
                        student=enrollment.student,
                        lesson__course=course,
                        is_completed=True,
                    ).count()
                    total_progress += completed
                    total_possible += lessons_count

        avg_completion = round(
            (total_progress / total_possible * 100) if total_possible > 0 else 0, 1
        )

        return Response(
            success_response(
                message="Instructor Dashboard",
                data={
                    "role": request.user.role,
                    "stats": {
                        "total_courses": total_courses,
                        "active_courses": active_courses,
                        "total_lessons": total_lessons,
                        "total_students": total_students,
                        "pending_enrollments": pending_enrollments,
                        "avg_completion_rate": avg_completion,
                    },
                },
            )
        )


class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    @swagger_auto_schema(responses={200: "Student dashboard stats"})
    def get(self, request):
        from apps.courses.models import Lesson
        from apps.enrollments.models import (
            Enrollment,
            EnrollmentRequest,
            LessonProgress,
        )

        student = request.user
        tenant = student.tenant

        # Get student's enrollments
        my_enrollments = Enrollment.objects.filter(tenant=tenant, student=student)

        # Statistics
        courses_enrolled = my_enrollments.count()
        pending_requests = EnrollmentRequest.objects.filter(
            tenant=tenant, student=student, status="PENDING"
        ).count()

        # Calculate progress
        total_lessons = 0
        completed_lessons = 0
        courses_in_progress = 0
        courses_completed = 0

        for enrollment in my_enrollments:
            course_lessons = Lesson.objects.filter(
                course=enrollment.course, is_active=True
            ).count()
            completed = LessonProgress.objects.filter(
                tenant=tenant,
                student=student,
                lesson__course=enrollment.course,
                is_completed=True,
            ).count()

            total_lessons += course_lessons
            completed_lessons += completed

            if course_lessons > 0:
                if completed == course_lessons:
                    courses_completed += 1
                elif completed > 0:
                    courses_in_progress += 1

        overall_progress = round(
            (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0, 1
        )

        return Response(
            success_response(
                message="Student Dashboard",
                data={
                    "role": request.user.role,
                    "stats": {
                        "courses_enrolled": courses_enrolled,
                        "courses_in_progress": courses_in_progress,
                        "courses_completed": courses_completed,
                        "pending_requests": pending_requests,
                        "total_lessons": total_lessons,
                        "completed_lessons": completed_lessons,
                        "overall_progress": overall_progress,
                    },
                },
            )
        )


class AdminUserListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCreateUserSerializer

    def get_queryset(self):
        return User.objects.filter(tenant=self.request.user.tenant)


class AdminUserStatusUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUpdateUserStatusSerializer

    def get_queryset(self):
        return User.objects.filter(tenant=self.request.user.tenant)


class ForgotPasswordView(APIView):
    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        user = User.objects.filter(phone_number=phone).first()
        if not user:
            raise AppException("User not found")

        send_otp(
            tenant_id=user.tenant_id,
            phone=phone,
            purpose="FORGOT_PASSWORD",
        )

        return Response(
            success_response(message="OTP sent for password reset"),
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    @swagger_auto_schema(request_body=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp_input = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(phone_number=phone).first()
        if not user:
            raise AppException("User not found")

        data = get_otp(
            tenant_id=user.tenant_id,
            phone=phone,
            purpose="FORGOT_PASSWORD",
        )

        if not data:
            raise AppException("OTP expired or not found")

        if data["otp"] != otp_input:
            raise AppException("Invalid OTP")

        user.set_password(new_password)
        user.save()

        delete_otp(
            tenant_id=user.tenant_id,
            phone=phone,
            purpose="FORGOT_PASSWORD",
        )

        return Response(
            success_response(message="Password reset successful"),
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: "User profile details"})
    def get(self, request):
        user = request.user

        return Response(
            success_response(
                data={
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "is_active": user.is_active,
                    "is_phone_verified": user.is_phone_verified,
                    "tenant": user.tenant.name if user.tenant else None,
                }
            ),
            status=status.HTTP_200_OK,
        )


class ProfileUpdateView(APIView):
    """Update user profile (name, email)"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ProfileUpdateSerializer,
        responses={200: "Profile updated successfully"},
    )
    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            success_response(
                message="Profile updated successfully",
                data={
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                },
            ),
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """Change user password"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={200: "Password changed successfully", 400: "Invalid password"},
    )
    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Verify current password
        if not user.check_password(serializer.validated_data["current_password"]):
            raise AppException(
                "Current password is incorrect", status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            success_response(message="Password changed successfully", data={}),
            status=status.HTTP_200_OK,
        )
