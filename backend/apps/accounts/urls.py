from apps.accounts.views import (
    AdminDashboardView,
    AdminUserListCreateView,
    AdminUserStatusUpdateView,
    ChangePasswordView,
    ForgotPasswordView,
    InstructorDashboardView,
    LoginView,
    ProfileUpdateView,
    ProfileView,
    RegisterView,
    ResetPasswordView,
    StudentDashboardView,
    VerifyOTPView,
)
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("verify-otp/", VerifyOTPView.as_view()),
    path("login/", LoginView.as_view()),
    path("register/", RegisterView.as_view(), name="register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("admin/dashboard/", AdminDashboardView.as_view()),
    path("instructor/dashboard/", InstructorDashboardView.as_view()),
    path("student/dashboard/", StudentDashboardView.as_view()),
    path("admin/users/", AdminUserListCreateView.as_view(), name="admin-users"),
    path(
        "admin/users/<int:pk>/status/",
        AdminUserStatusUpdateView.as_view(),
        name="admin-user-status",
    ),
]
