from app.schemas.course_ai import CourseInsightRequest, CourseInsightResponse
from app.security.rbac import require_roles
from app.services.course_ai_service import CourseAIService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/insights", tags=["AI Insights"])


@router.post("", response_model=CourseInsightResponse)
def generate_insight(
    request: CourseInsightRequest,
    data=Depends(require_roles("INSTRUCTOR", "ADMIN")),
):
    """
    Generate AI insight for a course.
    Only INSTRUCTOR and ADMIN allowed.
    """

    result = CourseAIService.generate_insight(
        course_id=request.course_id,
        topic=request.topic,
    )

    return result
