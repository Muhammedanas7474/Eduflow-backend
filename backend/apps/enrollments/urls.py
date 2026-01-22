from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.enrollments.views import (
    EnrollmentViewSet,
    LessonProgressViewSet,
    EnrollmentRequestViewSet,
    InstructorCourseEnrollmentsAPIView,
    AdminEnrollmentRequestReviewAPIView,
    InstructorEnrollmentRequestReviewAPIView,
    InstructorCourseProgressAPIView,
)

router = DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'lesson-progress', LessonProgressViewSet, basename='lesson-progress')
router.register(
    r'enrollment-requests',
    EnrollmentRequestViewSet,
    basename='enrollment-requests'
)

urlpatterns = router.urls + [
    path(
        "instructor/courses/<int:course_id>/enrollments/",
        InstructorCourseEnrollmentsAPIView.as_view(),
        name="instructor-course-enrollments",
    ),
    path(
        "admin/enrollment-requests/<int:request_id>/review/",
        AdminEnrollmentRequestReviewAPIView.as_view(),
        name="admin-enrollment-request-review",
    ),
    path(
        "instructor/enrollment-requests/<int:request_id>/review/",
        InstructorEnrollmentRequestReviewAPIView.as_view(),
        name="instructor-enrollment-request-review",
    ),
    path(
        "instructor/courses/<int:course_id>/progress/",
        InstructorCourseProgressAPIView.as_view(),
        name="instructor-course-progress",
    ),
]
