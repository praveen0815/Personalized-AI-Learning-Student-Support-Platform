"""Orchestrate retrieval from the Phase 1 knowledge base and a grounded answer."""

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.tutor import TutorChatResponse, TutorSource
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.tutor_prompt import NO_CONTEXT_ANSWER, TUTOR_SYSTEM_PROMPT, build_user_message
from app.services.vector_search_service import VectorSearchService


class TutorService:
    def __init__(
        self,
        db: Session,
        embeddings: EmbeddingService,
        llm: LLMService,
        settings: Settings,
    ) -> None:
        self.db = db
        self.embeddings = embeddings
        self.llm = llm
        self.settings = settings

    def answer(self, question: str, top_k: int) -> TutorChatResponse:
        query_embedding = self.embeddings.embed_query(question)
        hits = VectorSearchService(self.db, self.settings).search(query_embedding, top_k)
        relevant = [
            hit for hit in hits if hit.similarity >= self.settings.tutor_min_similarity
        ]
        if not relevant:
            return TutorChatResponse(answer=NO_CONTEXT_ANSWER, sources=[])

        answer = self.llm.complete(
            TUTOR_SYSTEM_PROMPT,
            build_user_message(question, relevant),
        )
        return TutorChatResponse(
            answer=answer,
            sources=[
                TutorSource(
                    document_id=hit.document_id,
                    document_name=hit.document_name,
                    page_number=hit.page_number,
                    chunk_id=hit.chunk_id,
                    similarity=hit.similarity,
                )
                for hit in relevant
            ],
        )
