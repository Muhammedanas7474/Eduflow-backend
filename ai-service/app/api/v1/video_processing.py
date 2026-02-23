"""
Video processing API endpoints.
POST /api/v1/process-video — enqueue video for transcription + embedding
GET  /api/v1/process-video/status/{lesson_id} — check processing status
"""

from app.security.jwt import verify_jwt_token
from app.services.vector_service import VectorService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Video Processing"])

vector_service = VectorService()


class ProcessVideoRequest(BaseModel):
    course_id: int
    lesson_id: int
    s3_url: str
    tenant_id: int


class ProcessVideoResponse(BaseModel):
    message: str
    lesson_id: int
    status: str


@router.post("/process-video", response_model=ProcessVideoResponse)
async def process_video(
    request: ProcessVideoRequest,
):
    """
    Enqueue a video for transcription and embedding.
    The processing happens in the background via Celery.
    """
    from app.tasks import process_video_task

    # Set initial status
    vector_service.set_status(
        tenant_id=request.tenant_id,
        lesson_id=request.lesson_id,
        course_id=request.course_id,
        status="pending",
    )

    # Enqueue Celery task
    process_video_task.delay(
        course_id=request.course_id,
        lesson_id=request.lesson_id,
        s3_url=request.s3_url,
        tenant_id=request.tenant_id,
    )

    return ProcessVideoResponse(
        message="Video processing enqueued",
        lesson_id=request.lesson_id,
        status="pending",
    )


@router.get("/process-video/status/{lesson_id}")
async def get_processing_status(
    lesson_id: int,
    payload: dict = Depends(verify_jwt_token),
):
    """Check the processing status of a video lesson."""
    status = vector_service.get_status(lesson_id)
    if not status:
        raise HTTPException(status_code=404, detail="No processing record found")
    return status
