from django.urls import path
from apps.accounts.views import SendOTPView, VerifyOTPView
from apps.accounts.views import LoginView

urlpatterns = [
    path("send-otp/", SendOTPView.as_view()),
    path("verify-otp/", VerifyOTPView.as_view()),
    path("login/", LoginView.as_view()),
]
