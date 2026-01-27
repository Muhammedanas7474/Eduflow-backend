from rest_framework import serializers, status

from ..common.exceptions import AppException
from ..tenants.models import Tenant
from .models import User


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()
    purpose = serializers.CharField()

    def validate_purpose(self, value):
        value = value.upper()
        if value not in ["LOGIN", "REGISTER", "FORGOT_PASSWORD"]:
            raise serializers.ValidationError("Invalid purpose")
        return value


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()
    tenant_id = serializers.IntegerField()


class RegisterSerializer(serializers.Serializer):
    tenant_id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        if User.objects.filter(phone_number=data["phone_number"]).exists():
            raise AppException(
                "Phone number already registered",
                status.HTTP_409_CONFLICT,
                "PHONE_EXISTS",
            )

        if User.objects.filter(email=data["email"]).exists():
            raise AppException(
                "Email already registered", status.HTTP_409_CONFLICT, "EMAIL_EXISTS"
            )
        if not Tenant.objects.filter(id=data["tenant_id"]).exists():
            raise AppException(
                "Invalid tenant selected", status.HTTP_409_CONFLICT, "TENANT"
            )

        return data


class AdminCreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "role", "is_active", "full_name", "email"]

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data["phone_number"],
            tenant=self.context["request"].user.tenant,
        )
        user.role = validated_data["role"]
        user.is_active = validated_data.get("is_active", True)
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "role", "is_active", "is_phone_verified"]


class AdminUpdateUserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_active"]


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()
    new_password = serializers.CharField(write_only=True)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = ["full_name", "email"]

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise AppException(
                "Email already registered by another user", status.HTTP_400_BAD_REQUEST
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise AppException(
                "New passwords do not match", status.HTTP_400_BAD_REQUEST
            )
        return attrs
