from pydantic import BaseModel


class CourseInsightRequest(BaseModel):
    course_id: int
    topic: str


class CourseInsightResponse(BaseModel):
    course_id: int
    topic: str
    ai_summary: str
