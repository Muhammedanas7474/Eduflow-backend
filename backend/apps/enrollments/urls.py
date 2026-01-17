from rest_framework.routers import DefaultRouter
from apps.enrollments.views import EnrollmentViewSet

router = DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')

urlpatterns = router.urls
