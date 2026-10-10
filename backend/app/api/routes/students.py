"""Student records, topic progress, and learning gaps."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_embedding_service, get_llm_service
from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.schemas.assessment import (
    LearningGapView,
    StudentCreateRequest,
    StudentGapsResponse,
    StudentProgressResponse,
    StudentResponse,
    TopicProgressView,
)
from app.services.assessment_service import AssessmentService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/v1/students", tags=["students"])


def _service(
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    llm: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
) -> AssessmentService:
    return AssessmentService(db, embeddings, llm, settings)


@router.post("", response_model=StudentResponse, status_code=201, summary="Create a student")
def create_student(
    body: StudentCreateRequest,
    service: AssessmentService = Depends(_service),
) -> StudentResponse:
    student = service.create_student(body.name)
    return StudentResponse.model_validate(student, from_attributes=True)


@router.get(
    "/{student_id}/progress",
    response_model=StudentProgressResponse,
    summary="Topic mastery for one student",
    responses={404: {"description": "Student not found"}},
)
def student_progress(
    student_id: UUID,
    service: AssessmentService = Depends(_service),
) -> StudentProgressResponse:
    topics = [
        TopicProgressView(
            topic=row.topic,
            mastery=row.mastery_score,
            questions_attempted=row.questions_attempted,
            questions_correct=row.questions_correct,
        )
        for row in service.list_progress(student_id)
    ]
    return StudentProgressResponse(student_id=student_id, topics=topics)


@router.get(
    "/{student_id}/learning-gaps",
    response_model=StudentGapsResponse,
    summary="Active learning gaps for one student",
    responses={404: {"description": "Student not found"}},
)
def student_learning_gaps(
    student_id: UUID,
    service: AssessmentService = Depends(_service),
) -> StudentGapsResponse:
    gaps = [
        LearningGapView(
            topic=row.topic,
            mastery=row.mastery_score,
            severity=row.severity,
            reason=row.reason,
            status=row.status,
            detected_at=row.detected_at,
        )
        for row in service.list_active_gaps(student_id)
    ]
    return StudentGapsResponse(student_id=student_id, learning_gaps=gaps)
