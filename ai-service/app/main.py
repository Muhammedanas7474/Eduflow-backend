import logging
from contextlib import asynccontextmanager

from app.api.v1.courses import router as courses_router
from app.api.v1.demo import router as demo_router

# Routers
from app.api.v1.health import router as health_router
from app.api.v1.insights import router as insights_router
from app.api.v1.protected import router as protected_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.rag import router as rag_router
from app.api.v1.video_processing import router as video_processing_router
from app.core.config import settings
from app.core.database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.service_name,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(protected_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(quiz_router, prefix="/api/v1")
app.include_router(video_processing_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
