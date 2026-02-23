"""
SQLAlchemy model for storing lesson transcript embeddings in PGVector.
"""

import uuid

from app.core.database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID


class LessonEmbedding(Base):
    __tablename__ = "lesson_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    lesson_id = Column(Integer, nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<LessonEmbedding lesson={self.lesson_id} "
            f"time={self.start_time:.1f}-{self.end_time:.1f}>"
        )


class ProcessingStatus(Base):
    """Track video processing status per lesson."""

    __tablename__ = "lesson_processing_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Integer, nullable=False, index=True)
    lesson_id = Column(Integer, nullable=False, unique=True, index=True)
    course_id = Column(Integer, nullable=False)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    chunks_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
