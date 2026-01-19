from rest_framework.routers import DefaultRouter
from apps.enrollments.views import EnrollmentViewSet,LessonProgressViewSet

router = DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'lesson-progress',LessonProgressViewSet, basename='lesson-progress')

urlpatterns = router.urls
