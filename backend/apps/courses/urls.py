from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, LessonResourceViewSet, LessonViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("lesson-resources", LessonResourceViewSet, basename="lesson-resources")

urlpatterns = router.urls
