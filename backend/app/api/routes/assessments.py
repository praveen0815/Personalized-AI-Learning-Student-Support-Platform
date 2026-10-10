"""Assessment generation, retrieval, and submission."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_embedding_service, get_llm_service
from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.schemas.assessment import (
    AssessmentGenerationResponse,
    AssessmentRequest,
    PublicAssessment,
    SubmitAssessmentRequest,
    SubmitAssessmentResponse,
)
from app.services.assessment_service import AssessmentService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


def _service(
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    llm: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
) -> AssessmentService:
    return AssessmentService(db, embeddings, llm, settings)


@router.post(
    "/generate",
    response_model=AssessmentGenerationResponse,
    summary="Generate a grounded multiple-choice assessment",
    description=(
        "Retrieves uploaded material for the topic and asks the existing language model "
        "for multiple-choice questions. The response does not include correct answers. "
        "If the knowledge base has no relevant context, no questions are created."
    ),
)
def generate_assessment(
    body: AssessmentRequest,
    service: AssessmentService = Depends(_service),
) -> AssessmentGenerationResponse:
    result = service.generate(body.student_id, body.topic, body.number_of_questions)
    return AssessmentGenerationResponse.model_validate(result)


@router.post(
    "/adaptive",
    response_model=AssessmentGenerationResponse,
    summary="Generate an assessment matched to topic mastery",
    description=(
        "Chooses easy, medium, or hard questions from the student's topic mastery, "
        "reuses unseen questions when they exist, and generates any missing questions "
        "from the knowledge base."
    ),
)
def generate_adaptive_assessment(
    body: AssessmentRequest,
    service: AssessmentService = Depends(_service),
) -> AssessmentGenerationResponse:
    result = service.generate_adaptive(body.student_id, body.topic, body.number_of_questions)
    return AssessmentGenerationResponse.model_validate(result)


@router.get(
    "/{assessment_id}",
    response_model=PublicAssessment,
    summary="Get an assessment without answers",
    responses={404: {"description": "Assessment not found"}},
)
def get_assessment(
    assessment_id: UUID,
    service: AssessmentService = Depends(_service),
) -> PublicAssessment:
    return PublicAssessment.model_validate(service.get_public_assessment(assessment_id))


@router.post(
    "/{assessment_id}/submit",
    response_model=SubmitAssessmentResponse,
    summary="Score an assessment and update mastery",
)
def submit_assessment(
    assessment_id: UUID,
    body: SubmitAssessmentRequest,
    service: AssessmentService = Depends(_service),
) -> SubmitAssessmentResponse:
    result = service.submit(assessment_id, body.student_id, body.answers)
    return SubmitAssessmentResponse.model_validate(result)
