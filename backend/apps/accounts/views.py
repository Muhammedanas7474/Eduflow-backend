from django.shortcuts import render
from rest_framework.views import APIView
from apps.accounts.serializers import SendOTPSerializer,VerifyOTPSerializer
from apps.accounts.utils import generate_otp
from apps.accounts.models import OTP,User
from rest_framework.response import Response
from apps.common.responses import success_response
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.serializers import LoginSerializer
from apps.common.responses import success_response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



class SendOTPView(APIView):
    @swagger_auto_schema(
        request_body=SendOTPSerializer,
        responses={200: "OTP sent successfully"}
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp = generate_otp()

        OTP.objects.create(phone_number=phone, otp=otp)

        
        print(f"OTP for {phone} is {otp}")

        return Response(
            success_response(message="OTP sent successfully")
        )


class VerifyOTPView(APIView):
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={200: "OTP verified"}
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        try:
            otp_obj = OTP.objects.filter(
                phone_number=phone,
                otp=otp,
                is_used=False
            ).latest("created_at")
        except OTP.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid OTP"},
                status=400
            )

        
        if timezone.now() - otp_obj.created_at > timedelta(minutes=5):
            return Response(
                {"success": False, "message": "OTP expired"},
                status=400
            )

        otp_obj.is_used = True
        otp_obj.save()

        user = User.objects.filter(phone_number=phone).first()
        if user:
            user.is_phone_verified = True
            user.save()

        return Response(
            success_response(message="OTP verified successfully")
        )




 
class LoginView(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access": openapi.Schema(type=openapi.TYPE_STRING),
                                "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                                "role": openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        user = User.objects.filter(
            phone_number=phone,
            is_phone_verified=True
        ).first()

        if not user:
            return Response(
                {"success": False, "message": "Phone not verified"},
                status=400
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            success_response(
                data={
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": user.role
                },
                message="Login successful"
            )
        )
