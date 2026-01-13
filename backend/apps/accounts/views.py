from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, UpdateAPIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.tenants.models import Tenant

from apps.accounts.serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    RegisterSerializer,
    AdminCreateUserSerializer,
    AdminUpdateUserStatusSerializer,
)

from apps.common.responses import success_response
from apps.common.exceptions import AppException
from apps.common.permissions import IsAdmin, IsInstructor, IsStudent

from .utils import set_otp, get_otp, delete_otp


class SendOTPView(APIView):
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        otp = set_otp(phone, purpose="general")
        print(f"OTP for {phone}: {otp}")

        return Response(
            success_response(message="OTP sent successfully"),
            status=status.HTTP_200_OK
        )



class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp_input = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        data = get_otp(phone, purpose=purpose)

        if not data:
            raise AppException("OTP expired or not found")

        if data["otp"] != otp_input:
            raise AppException("Invalid OTP")

        delete_otp(phone, purpose=purpose)

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




class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if User.objects.filter(phone_number=serializer.validated_data["phone_number"]).exists():
            raise AppException("User already exists")

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
            success_response(message="Registration successful. OTP sent."),
            status=201
        )



class LoginView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(phone_number=phone).first()

        if not user:
            raise AppException("User not found")

        if not user.check_password(password):
            raise AppException(
                "Invalid phone number or password",
                status_code=401
            )


        if not user.is_active:
            raise AppException("Account is disabled")

        otp = set_otp(phone, purpose="login")
        print(f"LOGIN OTP for {phone}: {otp}")

        return Response(
            success_response(message="OTP sent for login"),
            status=status.HTTP_200_OK
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
            success_response(message="Instructor dashboard")
        )



class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        return Response(
            success_response(message="Student dashboard")
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

