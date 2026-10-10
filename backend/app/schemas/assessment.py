"""Student-facing assessment and progress models.

Correct answers and explanations are stored on the question row and are not
part of these response models.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StudentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, examples=["Asha"])

    @field_validator("name")
    @classmethod
    def name_must_contain_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name must not be empty")
        return cleaned


class StudentResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime


class AssessmentRequest(BaseModel):
    student_id: UUID
    topic: str = Field(..., min_length=1, max_length=200, examples=["Bayes Theorem"])
    number_of_questions: int = Field(default=5, ge=1, le=10)

    @field_validator("topic")
    @classmethod
    def topic_must_contain_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Topic must not be empty")
        return cleaned


class PublicQuestion(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    topic: str
    difficulty: str
    options: dict[str, str]
    source_document_name: str | None = None
    source_page_number: int | None = None


class PublicAssessment(BaseModel):
    id: UUID
    title: str
    description: str
    topic: str
    questions: list[PublicQuestion]


class AssessmentGenerationResponse(BaseModel):
    status: Literal["created", "no_context"]
    message: str | None = None
    assessment: PublicAssessment | None = None


class AnswerSubmission(BaseModel):
    question_id: UUID
    selected_option: str = Field(..., min_length=1, max_length=8)


class SubmitAssessmentRequest(BaseModel):
    student_id: UUID
    answers: list[AnswerSubmission] = Field(..., min_length=1)


class TopicResult(BaseModel):
    topic: str
    correct: int
    attempted: int
    mastery: float


class LearningGapView(BaseModel):
    topic: str
    mastery: float
    severity: str
    reason: str
    status: str
    detected_at: datetime


class SubmitAssessmentResponse(BaseModel):
    attempt_id: UUID
    score: int
    total_questions: int
    percentage: float
    topic_results: list[TopicResult]
    learning_gaps: list[LearningGapView]


class TopicProgressView(BaseModel):
    topic: str
    mastery: float
    questions_attempted: int
    questions_correct: int


class StudentProgressResponse(BaseModel):
    student_id: UUID
    topics: list[TopicProgressView]


class StudentGapsResponse(BaseModel):
    student_id: UUID
    learning_gaps: list[LearningGapView]
