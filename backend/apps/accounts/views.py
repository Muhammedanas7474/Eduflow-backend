from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, UpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg.utils import swagger_auto_schema

from apps.accounts.models import User
from apps.tenants.models import Tenant
from apps.accounts.serializers import (
    VerifyOTPSerializer,
    LoginSerializer,
    RegisterSerializer,
    AdminCreateUserSerializer,
    AdminUpdateUserStatusSerializer,
    ResetPasswordSerializer,ForgotPasswordSerializer
)

from apps.common.responses import success_response, error_response
from apps.common.exceptions import AppException
from apps.common.permissions import IsAdmin, IsInstructor, IsStudent
from .utils import set_otp, get_otp, delete_otp








class VerifyOTPView(APIView):
    def post(self, request):
        try:
            serializer = VerifyOTPSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone = serializer.validated_data["phone_number"]
            otp_input = serializer.validated_data["otp"]
            purpose = serializer.validated_data["purpose"]

            data = get_otp(phone, purpose)

            if not data:
                raise AppException("OTP expired or not found")

            if data["otp"] != otp_input:
                raise AppException("Invalid OTP")

            delete_otp(phone, purpose)

            user = User.objects.filter(phone_number=phone).first()
            if not user:
                raise AppException("User not found")

            user.is_phone_verified = True
            user.is_active = True
            user.save()

            refresh = RefreshToken.for_user(user)

            return Response(
                success_response(
                    message="OTP verified successfully",
                    data={
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "role": user.role
                    }
                ),
                status=200
            )

        except AppException as e:
            return Response(
                error_response(e.message, e.code),
                status=e.status_code
            )




class RegisterView(APIView):
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if User.objects.filter(
                phone_number=serializer.validated_data["phone_number"]
            ).exists():
                raise AppException(
                    "User already exists",
                    status_code=409,
                    code="USER_EXISTS"
                )

            tenant = Tenant.objects.first()

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

            otp = set_otp(user.phone_number, purpose="register")
            print(f"REGISTER OTP for {user.phone_number}: {otp}")

            return Response(
                success_response(
                    message="Registration successful. OTP sent."
                ),
                status=201
            )

        except AppException as e:
            return Response(
                error_response(e.message, e.code),
                status=e.status_code
            )




class LoginView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone = serializer.validated_data["phone_number"]
            password = serializer.validated_data["password"]

            user = User.objects.filter(phone_number=phone).first()
            if not user:
                raise AppException("User not found", status_code=404)

            if not user.check_password(password):
                raise AppException(
                    "Invalid phone number or password",
                    status_code=401,
                    code="INVALID_CREDENTIALS"
                )

            if not user.is_active:
                raise AppException("Account disabled", status_code=403)

            otp = set_otp(phone, purpose="login")
            print(f"LOGIN OTP for {phone}: {otp}")

            return Response(
                success_response(message="OTP sent for login"),
                status=200
            )

        except AppException as e:
            return Response(
                error_response(e.message, e.code),
                status=e.status_code
            )



class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response(
            success_response(
                message="Welcome Admin",
                data={"role": request.user.role}
            )
        )




class InstructorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        return Response(
            success_response(
                message="Welcome Instructor",
                data={"role": request.user.role}
            )
        )



class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        return Response(
            success_response(
                message="Welcome Student",
                data={"role": request.user.role}
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
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        user = User.objects.filter(phone_number=phone).first()
        if not user:
            raise AppException("User not found")

        otp = set_otp(phone, purpose="forgot")
        print(f"FORGOT PASSWORD OTP for {phone}: {otp}")

        return Response(
            success_response(message="OTP sent for password reset"),
            status=status.HTTP_200_OK
        )

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp_input = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        data = get_otp(phone, purpose="forgot")

        if not data:
            raise AppException("OTP expired or not found")

        if data["otp"] != otp_input:
            raise AppException("Invalid OTP")

        user = User.objects.filter(phone_number=phone).first()
        if not user:
            raise AppException("User not found")

        user.set_password(new_password)
        user.save()

        delete_otp(phone, purpose="forgot")

        return Response(
            success_response(message="Password reset successful"),
            status=status.HTTP_200_OK
        )

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            success_response(
                data={
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "is_active": user.is_active,
                    "is_phone_verified": user.is_phone_verified,
                    "tenant": user.tenant.name if user.tenant else None,
                }
            ),
            status=status.HTTP_200_OK
        )
