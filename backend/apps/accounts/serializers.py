from rest_framework import serializers

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
