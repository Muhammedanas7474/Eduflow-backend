from django.urls import path
from apps.accounts.views import SendOTPView, VerifyOTPView
from apps.accounts.views import LoginView,AdminDashboardView,InstructorDashboardView,StudentDashboardView

urlpatterns = [
    path("send-otp/", SendOTPView.as_view()),
    path("verify-otp/", VerifyOTPView.as_view()),
    path("login/", LoginView.as_view()),
    path("admin/dashboard/", AdminDashboardView.as_view()),
    path("instructor/dashboard/", InstructorDashboardView.as_view()),
    path("student/dashboard/", StudentDashboardView.as_view()),
]
