"""
Celery tasks for course-related background work.
"""

import logging

import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def trigger_video_processing(self, lesson_id, course_id, video_url, tenant_id):
    """
    Notify the AI service to start processing a video lesson.
    Called after a lesson with a video_url is created or updated.
    """
    ai_url = getattr(settings, "AI_SERVICE_URL", "http://eduflow-ai:8002")
    endpoint = f"{ai_url}/api/v1/process-video"

    # Build an internal service token for auth
    from apps.accounts.models import User
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        # Use the first admin user's token for auth
        admin = User.objects.filter(role="ADMIN").first()
        if admin:
            token = str(AccessToken.for_user(admin))
        else:
            logger.warning("No admin user found for AI service auth")
            return

        response = requests.post(
            endpoint,
            json={
                "course_id": course_id,
                "lesson_id": lesson_id,
                "s3_url": video_url,
                "tenant_id": tenant_id,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

        if response.status_code == 200:
            logger.info(
                f"Video processing triggered for lesson {lesson_id}: "
                f"{response.json()}"
            )
        else:
            logger.error(f"AI service returned {response.status_code}: {response.text}")
            self.retry()

    except requests.exceptions.ConnectionError as e:
        logger.warning(
            f"AI service not reachable for lesson {lesson_id}: {e}. " "Will retry."
        )
        self.retry(exc=e)
    except Exception as e:
        logger.error(f"Failed to trigger video processing: {e}")
