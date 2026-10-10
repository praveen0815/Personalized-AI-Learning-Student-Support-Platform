"""Tutor HTTP route. Retrieval and citations come from the Phase 1 knowledge base."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_embedding_service, get_llm_service
from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.schemas.tutor import TutorChatRequest, TutorChatResponse
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.tutor_service import TutorService

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])


@router.post(
    "/chat",
    response_model=TutorChatResponse,
    summary="Answer a question from uploaded learning material",
    description=(
        "Embeds the question with the existing embedding service, retrieves chunks with "
        "pgvector, and asks the language model to answer from those chunks only. "
        "Source metadata is copied from the retrieved records. If nothing is relevant "
        "enough, the language model is not called."
    ),
)
def tutor_chat(
    body: TutorChatRequest,
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    llm: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
) -> TutorChatResponse:
    return TutorService(db, embeddings, llm, settings).answer(body.question, body.top_k)
