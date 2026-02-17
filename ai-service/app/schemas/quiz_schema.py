from typing import List

from pydantic import BaseModel


class QuizRequest(BaseModel):
    lesson_text: str
    num_questions: int = 5


class QuizFromPDFRequest(BaseModel):
    pdf_key: str
    num_questions: int = 5


class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: str


class QuizResponse(BaseModel):
    questions: List[Question]
