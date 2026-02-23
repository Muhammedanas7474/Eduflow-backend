"""
RAG (Retrieval-Augmented Generation) API endpoint.
POST /api/v1/rag/ask — student asks a doubt about a lesson
"""

from app.services.rag_service import RAGService
from app.services.vector_service import VectorService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["RAG"])

rag_service = RAGService()
vector_service = VectorService()


class RAGRequest(BaseModel):
    course_id: int
    lesson_id: int
    question: str
    current_time: float | None = None


class SourceRef(BaseModel):
    start: float
    end: float
    text_preview: str


class RAGResponse(BaseModel):
    answer: str
    sources: list[SourceRef]


@router.post("/rag/ask", response_model=RAGResponse)
async def ask_doubt(
    request: RAGRequest,
):
    """
    Answer a student's question grounded in the lesson transcript.
    Falls back to direct OpenAI if embeddings aren't available.
    """
    # Check if lesson has been processed
    has_data = vector_service.has_embeddings(request.lesson_id)

    if has_data:
        # Full RAG path — grounded in transcript
        result = rag_service.ask(
            lesson_id=request.lesson_id,
            question=request.question,
            current_time=request.current_time,
        )
    else:
        # Check if actively processing
        status = vector_service.get_status(request.lesson_id)
        if status and status["status"] == "processing":
            raise HTTPException(
                status_code=202,
                detail="This lesson is still being processed. Please try again later.",
            )

        # Fallback — use OpenAI directly without transcript context
        result = rag_service.fallback_ask(request.question)

    return RAGResponse(
        answer=result["answer"],
        sources=[SourceRef(**s) for s in result["sources"]],
    )
