import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_lesson_quiz(self, quiz_id, lesson_id, tenant_id):
    """
    Celery task: generate an AI quiz for a lesson's PDF resources.
    Called automatically when a student marks a lesson as complete.
    The Quiz row already exists with status='GENERATING'.
    """
    from apps.courses.models import Lesson, LessonResource, Option, Question, Quiz

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        lesson = Lesson.objects.get(id=lesson_id, tenant_id=tenant_id)
    except (Quiz.DoesNotExist, Lesson.DoesNotExist) as e:
        logger.error(f"Quiz or Lesson not found: {e}")
        return

    # Find PDF resources for this lesson
    pdf_resources = LessonResource.objects.filter(lesson=lesson).exclude(
        file_type="link"
    )
    pdf_resource = None
    for res in pdf_resources:
        if res.file_url and (
            res.file_url.endswith(".pdf") or "pdf" in res.file_type.lower()
        ):
            pdf_resource = res
            break

    if not pdf_resource:
        logger.warning(f"No PDF resource found for lesson {lesson_id}")
        quiz.status = "FAILED"
        quiz.save()
        return

    # Extract S3 key from the full URL
    import re

    pdf_key = pdf_resource.file_url
    s3_match = re.search(r"\.amazonaws\.com/(.+)$", pdf_key)
    if s3_match:
        from urllib.parse import unquote

        pdf_key = unquote(s3_match.group(1))

    # Call the AI service (no JWT needed — internal service call)
    from .services.ai_quiz_client import AIQuizClient

    try:
        ai_result = AIQuizClient.generate_quiz_from_pdf(
            pdf_key=pdf_key,
            jwt_token="internal-celery-task",  # AI service trusts internal calls
            num_questions=5,
        )
    except RuntimeError as e:
        logger.error(f"AI service error for lesson {lesson_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        quiz.status = "FAILED"
        quiz.save()
        return

    # Save questions and options
    questions_data = ai_result.get("questions", [])
    if not questions_data:
        logger.warning(f"AI returned no questions for lesson {lesson_id}")
        quiz.status = "FAILED"
        quiz.save()
        return

    for q_data in questions_data:
        question = Question.objects.create(
            quiz=quiz,
            question_text=q_data["question"],
            correct_answer=q_data["correct_answer"],
        )
        for opt_text in q_data.get("options", []):
            Option.objects.create(question=question, option_text=opt_text)

    quiz.status = "READY"
    quiz.save()

    logger.info(
        f"Auto-quiz {quiz.id} ready: {len(questions_data)} questions "
        f"for lesson {lesson_id}"
    )
