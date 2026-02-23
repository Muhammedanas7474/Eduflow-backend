"""
SQLAlchemy engine + session factory for PGVector.
Connects to the same Postgres instance as the Django backend.
"""

import logging

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    """Yield a DB session, close on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create the pgvector extension and all tables.
    Safe to call multiple times (CREATE IF NOT EXISTS).
    If pgvector is not installed, the service still starts
    but RAG features will be unavailable.
    """
    pgvector_available = False
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        logger.info("PGVector extension ensured")
        pgvector_available = True
    except Exception as e:
        logger.warning(f"Could not create vector extension (may need superuser): {e}")
        # Check if it already exists
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                )
                if result.fetchone():
                    pgvector_available = True
                    logger.info("PGVector extension already exists")
        except Exception:
            pass

    if pgvector_available:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("RAG tables created/verified")
        except Exception as e:
            logger.error(f"Could not create RAG tables: {e}")
            logger.warning("RAG features will be unavailable")
    else:
        logger.warning(
            "PGVector extension not available. RAG features will be disabled. "
            "Install pgvector and restart to enable RAG."
        )
