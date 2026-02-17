from app.api.v1.courses import router as courses_router
from app.api.v1.demo import router as demo_router

# Routers
from app.api.v1.health import router as health_router
from app.api.v1.insights import router as insights_router
from app.api.v1.protected import router as protected_router
from app.api.v1.quiz import router as quiz_router
from app.core.config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.service_name,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(protected_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(quiz_router, prefix="/api/v1")
