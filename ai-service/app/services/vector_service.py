"""
Vector storage service using PGVector.
Stores, retrieves, and searches lesson embeddings.
"""

import logging

from app.core.database import SessionLocal
from app.models.embedding_model import LessonEmbedding, ProcessingStatus

logger = logging.getLogger(__name__)


class VectorService:
    """Manage lesson embeddings in PGVector."""

    def store_chunks(
        self,
        tenant_id: int,
        course_id: int,
        lesson_id: int,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> int:
        """
        Store chunked text + embeddings in the database.

        Args:
            chunks: List of {text, start_time, end_time}
            embeddings: List of embedding vectors (same length as chunks)

        Returns:
            Number of chunks stored
        """
        db = SessionLocal()
        try:
            # Delete existing embeddings for this lesson (for re-processing)
            db.query(LessonEmbedding).filter(
                LessonEmbedding.lesson_id == lesson_id,
                LessonEmbedding.tenant_id == tenant_id,
            ).delete()

            for chunk, embedding in zip(chunks, embeddings):
                record = LessonEmbedding(
                    tenant_id=tenant_id,
                    course_id=course_id,
                    lesson_id=lesson_id,
                    chunk_text=chunk["text"],
                    embedding=embedding,
                    start_time=chunk["start_time"],
                    end_time=chunk["end_time"],
                )
                db.add(record)

            db.commit()
            logger.info(f"Stored {len(chunks)} embeddings for lesson {lesson_id}")
            return len(chunks)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store embeddings: {e}")
            # If tables are missing, we just return 0 stored
            if "relation" in str(e) and "does not exist" in str(e):
                return 0
            raise
        finally:
            db.close()

    def similarity_search(
        self,
        lesson_id: int,
        query_embedding: list[float],
        top_k: int = 5,
        current_time: float | None = None,
    ) -> list[dict]:
        """
        Find the most similar chunks to the query embedding.

        If current_time is provided, applies a time-proximity boost
        to favor chunks near the student's current video position.

        Returns:
            List of {text, start_time, end_time, score} dicts
        """
        db = SessionLocal()
        try:
            # Use pgvector cosine distance operator <=>
            # Lower distance = more similar
            query = db.query(
                LessonEmbedding.chunk_text,
                LessonEmbedding.start_time,
                LessonEmbedding.end_time,
                LessonEmbedding.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),
            ).filter(
                LessonEmbedding.lesson_id == lesson_id,
            )

            results = query.order_by("distance").limit(top_k * 2).all()

            ranked = []
            for row in results:
                score = 1.0 - row.distance  # Convert distance to similarity

                # Time proximity boost: if within 120 seconds, boost score
                if current_time is not None:
                    time_diff = min(
                        abs(row.start_time - current_time),
                        abs(row.end_time - current_time),
                    )
                    if time_diff < 120:
                        score += 0.1 * (1 - time_diff / 120)

                ranked.append(
                    {
                        "text": row.chunk_text,
                        "start_time": row.start_time,
                        "end_time": row.end_time,
                        "score": round(score, 4),
                    }
                )

            # Re-sort by boosted score and take top_k
            ranked.sort(key=lambda x: x["score"], reverse=True)
            return ranked[:top_k]

        finally:
            db.close()

    def delete_lesson_embeddings(self, lesson_id: int, tenant_id: int) -> int:
        """Delete all embeddings for a lesson. Returns count deleted."""
        db = SessionLocal()
        try:
            count = (
                db.query(LessonEmbedding)
                .filter(
                    LessonEmbedding.lesson_id == lesson_id,
                    LessonEmbedding.tenant_id == tenant_id,
                )
                .delete()
            )
            db.commit()
            return count
        finally:
            db.close()

    def has_embeddings(self, lesson_id: int) -> bool:
        """Check if a lesson already has embeddings."""
        db = SessionLocal()
        try:
            return (
                db.query(LessonEmbedding)
                .filter(LessonEmbedding.lesson_id == lesson_id)
                .first()
                is not None
            )
        except Exception:
            return False
        finally:
            db.close()

    # --- Processing Status ---

    def set_status(
        self,
        tenant_id: int,
        lesson_id: int,
        course_id: int,
        status: str,
        error_message: str | None = None,
        chunks_count: int = 0,
    ):
        """Create or update processing status for a lesson."""
        db = SessionLocal()
        try:
            record = (
                db.query(ProcessingStatus)
                .filter(ProcessingStatus.lesson_id == lesson_id)
                .first()
            )
            if record:
                record.status = status
                record.error_message = error_message
                record.chunks_count = chunks_count
            else:
                record = ProcessingStatus(
                    tenant_id=tenant_id,
                    lesson_id=lesson_id,
                    course_id=course_id,
                    status=status,
                    error_message=error_message,
                    chunks_count=chunks_count,
                )
                db.add(record)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to set status (likely missing tables): {e}")
            db.rollback()
        finally:
            db.close()

    def get_status(self, lesson_id: int) -> dict | None:
        """Get processing status for a lesson."""
        db = SessionLocal()
        try:
            record = (
                db.query(ProcessingStatus)
                .filter(ProcessingStatus.lesson_id == lesson_id)
                .first()
            )
            if not record:
                return None
            return {
                "lesson_id": record.lesson_id,
                "status": record.status,
                "error_message": record.error_message,
                "chunks_count": record.chunks_count,
                "updated_at": str(record.updated_at) if record.updated_at else None,
            }
        except Exception:
            return None
        finally:
            db.close()
