"""
Background Celery tasks for video processing pipeline.
"""

import logging

from app.celery_app import celery_app
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.transcription_service import TranscriptionService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_video_task(
    self,
    course_id: int,
    lesson_id: int,
    s3_url: str,
    tenant_id: int,
):
    """
    Full video processing pipeline:
    1. Download from S3
    2. Transcribe with Whisper
    3. Chunk transcript
    4. Generate embeddings
    5. Store in PGVector
    """
    vector_service = VectorService()

    try:
        # Update status
        vector_service.set_status(
            tenant_id=tenant_id,
            lesson_id=lesson_id,
            course_id=course_id,
            status="processing",
        )

        logger.info(
            f"[TASK] Processing video: lesson={lesson_id}, "
            f"course={course_id}, s3={s3_url}"
        )

        # Step 1 & 2: Download + Transcribe
        transcription_service = TranscriptionService()
        segments = transcription_service.transcribe_from_s3(s3_url)

        if not segments:
            vector_service.set_status(
                tenant_id=tenant_id,
                lesson_id=lesson_id,
                course_id=course_id,
                status="failed",
                error_message="Transcription produced no segments",
            )
            return {"status": "failed", "reason": "empty_transcript"}

        logger.info(f"[TASK] Transcribed {len(segments)} segments")

        # Step 3: Chunk
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_segments(segments)
        logger.info(f"[TASK] Created {len(chunks)} chunks")

        # Step 4: Embed
        embedding_service = EmbeddingService()
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_batch(texts)
        logger.info(f"[TASK] Generated {len(embeddings)} embeddings")

        # Step 5: Store
        stored = vector_service.store_chunks(
            tenant_id=tenant_id,
            course_id=course_id,
            lesson_id=lesson_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        # Update status to completed
        vector_service.set_status(
            tenant_id=tenant_id,
            lesson_id=lesson_id,
            course_id=course_id,
            status="completed",
            chunks_count=stored,
        )

        logger.info(
            f"[TASK] ✅ Video processing complete: "
            f"lesson={lesson_id}, chunks={stored}"
        )

        return {
            "status": "completed",
            "lesson_id": lesson_id,
            "chunks_stored": stored,
        }

    except Exception as e:
        logger.error(f"[TASK] ❌ Video processing failed: {e}", exc_info=True)

        vector_service.set_status(
            tenant_id=tenant_id,
            lesson_id=lesson_id,
            course_id=course_id,
            status="failed",
            error_message=str(e)[:500],
        )

        # Retry on transient errors
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"[TASK] Max retries exceeded for lesson {lesson_id}")

        return {"status": "failed", "error": str(e)[:200]}
