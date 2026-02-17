import logging
import os

from app.schemas.quiz_schema import QuizFromPDFRequest, QuizRequest, QuizResponse
from app.security.rbac import require_roles
from app.services.pdf_service import PDFService
from app.services.quiz_service import QuizService
from app.services.s3_service import S3Service
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quiz", tags=["AI Quiz"])


@router.post("/generate", response_model=QuizResponse)
def generate_quiz(
    request: QuizRequest,
    data=Depends(require_roles("INSTRUCTOR", "ADMIN")),
):
    """Generate a quiz from raw text (original endpoint)."""
    return QuizService.generate_quiz(
        text=request.lesson_text,
        num_questions=request.num_questions,
    )


@router.post("/generate-from-pdf", response_model=QuizResponse)
def generate_quiz_from_pdf(
    request: QuizFromPDFRequest,
    data=Depends(require_roles("INSTRUCTOR", "ADMIN")),
):
    """
    Full pipeline:
    1. Download PDF from S3
    2. Extract text with pdfplumber
    3. Generate MCQs with Flan-T5
    4. Return structured JSON
    """
    s3 = S3Service()
    tmp_path = None

    try:
        # Step 1 — Download from S3
        logger.info(f"Downloading PDF: {request.pdf_key}")
        tmp_path = s3.download_file(request.pdf_key)

        # Step 2 — Extract text
        logger.info("Extracting text from PDF …")
        text = PDFService.extract_text(tmp_path)
        logger.info(f"Extracted {len(text)} characters from PDF.")

        # Step 3 — Generate quiz
        logger.info(f"Generating {request.num_questions} questions …")
        result = QuizService.generate_quiz(
            text=text,
            num_questions=request.num_questions,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in generate-from-pdf")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {e}")
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
