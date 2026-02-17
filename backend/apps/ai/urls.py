from django.urls import path

from .views import (
    CourseQuizzesView,
    GenerateQuizFromPDFView,
    LessonQuizView,
    QuizDetailView,
)

urlpatterns = [
    path(
        "quizzes/generate-from-pdf/",
        GenerateQuizFromPDFView.as_view(),
        name="generate-quiz-from-pdf",
    ),
    path(
        "quizzes/<int:quiz_id>/",
        QuizDetailView.as_view(),
        name="quiz-detail",
    ),
    path(
        "courses/<int:course_id>/quizzes/",
        CourseQuizzesView.as_view(),
        name="course-quizzes",
    ),
    path(
        "lessons/<int:lesson_id>/quiz/",
        LessonQuizView.as_view(),
        name="lesson-quiz",
    ),
]
