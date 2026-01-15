from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import  VerifyOTPView,ForgotPasswordView,ResetPasswordView,ProfileView
from apps.accounts.views import LoginView,AdminDashboardView,InstructorDashboardView,StudentDashboardView,AdminUserListCreateView,AdminUserStatusUpdateView,RegisterView

urlpatterns = [ 
    path("verify-otp/", VerifyOTPView.as_view()),
    path("login/", LoginView.as_view()),
    path("register/", RegisterView.as_view(),name="register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("profile/", ProfileView.as_view(), name="profile"),

    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    path("admin/dashboard/", AdminDashboardView.as_view()),
    path("instructor/dashboard/", InstructorDashboardView.as_view()),
    path("student/dashboard/", StudentDashboardView.as_view()),

    path("admin/users/",AdminUserListCreateView.as_view(),name="admin-users"),
    path("admin/users/<int:pk>/status/",AdminUserStatusUpdateView.as_view(),name="admin-user-status"),
    


]
