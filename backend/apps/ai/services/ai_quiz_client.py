import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

AI_SERVICE_BASE = settings.AI_SERVICE_URL  # e.g. "http://eduflow-ai:8002"


class AIQuizClient:
    """
    Client that calls the FastAPI AI service to generate quizzes from PDFs.
    Forwards the instructor's JWT for authentication.
    """

    @staticmethod
    def generate_quiz_from_pdf(
        pdf_key: str,
        jwt_token: str,
        num_questions: int = 5,
    ) -> dict:
        """
        Call the AI service /api/v1/quiz/generate-from-pdf endpoint.

        Args:
            pdf_key: S3 object key for the PDF file
            jwt_token: Bearer JWT token to forward for auth
            num_questions: Number of MCQs to generate

        Returns:
            dict with {"questions": [...]}

        Raises:
            RuntimeError on any failure
        """
        url = f"{AI_SERVICE_BASE}/api/v1/quiz/generate-from-pdf"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "pdf_key": pdf_key,
            "num_questions": num_questions,
        }

        try:
            logger.info(f"Calling AI service: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code != 200:
                error_detail = response.json().get("detail", response.text)
                raise RuntimeError(
                    f"AI service returned {response.status_code}: {error_detail}"
                )

            return response.json()

        except requests.ConnectionError as e:
            raise RuntimeError(f"Cannot reach AI service at {url}: {e}") from e
        except requests.Timeout:
            raise RuntimeError("AI service timed out (120s). The PDF may be too large.")
