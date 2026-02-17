import logging

from apps.courses.models import Course, Option, Question, Quiz
from apps.courses.serializers import QuizSerializer
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.ai_quiz_client import AIQuizClient

logger = logging.getLogger(__name__)


class GenerateQuizFromPDFView(APIView):
    """
    POST /api/ai/quizzes/generate-from-pdf/

    Body: { "course_id": 1, "pdf_key": "course-resources/file.pdf", "num_questions": 5 }

    Only INSTRUCTOR and ADMIN can generate quizzes.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # ── RBAC check ──
        if user.role not in ("INSTRUCTOR", "ADMIN"):
            return Response(
                {"detail": "Only instructors and admins can generate quizzes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── Validate input ──
        course_id = request.data.get("course_id")
        pdf_key = request.data.get("pdf_key")
        num_questions = request.data.get("num_questions", 5)

        if not course_id or not pdf_key:
            return Response(
                {"detail": "course_id and pdf_key are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Validate course ownership + tenant isolation ──
        try:
            course = Course.objects.get(id=course_id, tenant=user.tenant)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == "INSTRUCTOR" and course.created_by != user:
            return Response(
                {"detail": "You can only generate quizzes for your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── Extract JWT token from cookie to forward to AI service ──
        jwt_token = request.COOKIES.get(
            settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token")
        )
        if not jwt_token:
            # Fallback: try Authorization header
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                jwt_token = auth_header.split(" ", 1)[1]

        if not jwt_token:
            return Response(
                {"detail": "Could not extract JWT token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ── Call AI service ──
        try:
            ai_result = AIQuizClient.generate_quiz_from_pdf(
                pdf_key=pdf_key,
                jwt_token=jwt_token,
                num_questions=num_questions,
            )
        except RuntimeError as e:
            logger.error(f"AI service error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ── Save Quiz → Questions → Options ──
        questions_data = ai_result.get("questions", [])

        if not questions_data:
            return Response(
                {"detail": "AI service returned no questions."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        quiz = Quiz.objects.create(
            course=course,
            tenant=user.tenant,
            created_by=user,
            title=f"AI Quiz – {course.title}",
        )

        for q_data in questions_data:
            question = Question.objects.create(
                quiz=quiz,
                question_text=q_data["question"],
                correct_answer=q_data["correct_answer"],
            )

            for opt_text in q_data.get("options", []):
                Option.objects.create(
                    question=question,
                    option_text=opt_text,
                )

        logger.info(
            f"Quiz {quiz.id} created with {len(questions_data)} questions "
            f"for course {course.id} by user {user.id}"
        )

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizDetailView(APIView):
    """
    GET /api/ai/quizzes/<quiz_id>/

    Returns a quiz with all questions and options.
    Respects tenant isolation.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        user = request.user

        try:
            quiz = Quiz.objects.prefetch_related("questions__options").get(
                id=quiz_id, tenant=user.tenant
            )
        except Quiz.DoesNotExist:
            return Response(
                {"detail": "Quiz not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = QuizSerializer(quiz)
        return Response(serializer.data)


class CourseQuizzesView(APIView):
    """
    GET /api/ai/courses/<course_id>/quizzes/

    List all quizzes for a course.
    Respects tenant isolation.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        user = request.user

        quizzes = (
            Quiz.objects.filter(
                course_id=course_id,
                tenant=user.tenant,
            )
            .prefetch_related("questions__options")
            .order_by("-created_at")
        )

        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)


class LessonQuizView(APIView):
    """
    GET /api/ai/lessons/<lesson_id>/quiz/

    Returns the auto-generated quiz for a lesson.
    - If quiz is READY: returns full quiz data
    - If quiz is GENERATING: returns { status: "generating", quiz_id: ... }
    - If no quiz exists: returns { status: null }

    Used by frontend to poll for quiz after marking a lesson complete.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        user = request.user

        quiz = (
            Quiz.objects.filter(lesson_id=lesson_id, tenant=user.tenant)
            .prefetch_related("questions__options")
            .first()
        )

        if not quiz:
            return Response({"status": None, "quiz_id": None})

        if quiz.status == "GENERATING":
            return Response({"status": "generating", "quiz_id": quiz.id})

        if quiz.status == "FAILED":
            return Response({"status": "failed", "quiz_id": quiz.id})

        # READY
        serializer = QuizSerializer(quiz)
        return Response(
            {"status": "ready", "quiz_id": quiz.id, "quiz": serializer.data}
        )
