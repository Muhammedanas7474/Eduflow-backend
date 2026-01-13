from rest_framework import serializers
from .models import User
from ..common.exceptions import AppException

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()
    purpose = serializers.ChoiceField(choices=["login", "register"])



class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)



from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        if User.objects.filter(phone_number=data["phone_number"]).exists():
            raise AppException("Phone number already registered", "PHONE_EXISTS")

        if User.objects.filter(email=data["email"]).exists():
            raise AppException("Email already registered", "EMAIL_EXISTS")

        return data




class AdminCreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "role", "is_active"]

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
        fields = [
            "id",
            "phone_number",
            "role",
            "is_active",
            "is_phone_verified"
        ]

class AdminUpdateUserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_active"]


