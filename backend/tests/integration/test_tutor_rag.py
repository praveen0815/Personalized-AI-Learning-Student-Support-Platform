"""Tutor retrieval against PostgreSQL + pgvector.

The query embedding is a known vector so this test does not call an embedding API.
The language model is a local stand-in. Similarity and source fields come from pgvector.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.database import Base, enable_pgvector
from app.db.models import Document, DocumentChunk
from app.services.tutor_prompt import TUTOR_SYSTEM_PROMPT
from app.services.tutor_service import TutorService


pytestmark = pytest.mark.integration


def _basis(index: int, dimension: int) -> list[float]:
    vector = [0.0] * dimension
    vector[index] = 1.0
    return vector


class FixedEmbeddings:
    def __init__(self, vector: list[float]) -> None:
        self.vector = vector

    def embed_query(self, text: str) -> list[float]:
        return self.vector


class RecordingLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_message: str) -> str:
        self.calls.append((system_prompt, user_message))
        return "Bayes theorem updates a prior using evidence from the supplied notes."


def test_tutor_uses_pgvector_hits_and_a_mocked_llm():
    url = os.getenv("INTEGRATION_DATABASE_URL", "")
    if not url.startswith("postgresql"):
        pytest.skip(
            "Set INTEGRATION_DATABASE_URL to a PostgreSQL database whose name contains 'test'."
        )
    database_name = make_url(url).database or ""
    if "test" not in database_name.lower():
        pytest.skip("Refusing to run against a database name that does not contain 'test'.")

    try:
        pg_engine = create_engine(url, pool_pre_ping=True)
        with pg_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL is not available for the integration test ({type(exc).__name__}).")

    enable_pgvector(pg_engine)
    Base.metadata.drop_all(bind=pg_engine)
    Base.metadata.create_all(bind=pg_engine)

    dimension = get_settings().resolved_embedding_dimension
    Session = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        document = Document(
            id=uuid.uuid4(),
            filename="Probability Notes.pdf",
            title="Probability Notes",
            file_type="pdf",
            file_path="unused-by-tutor-test",
            total_pages=2,
            total_chunks=2,
            processing_status="completed",
        )
        session.add(document)
        session.flush()
        bayes = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            page_number=1,
            content="Bayes theorem updates a prior when evidence arrives.",
            embedding=_basis(0, dimension),
        )
        plants = DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            page_number=2,
            content="Photosynthesis converts sunlight into chemical energy.",
            embedding=_basis(1, dimension),
        )
        session.add_all([bayes, plants])
        session.commit()

        llm = RecordingLLM()
        tutor = TutorService(
            session,
            FixedEmbeddings(_basis(0, dimension)),
            llm,
            get_settings(),
        )
        response = tutor.answer("Explain Bayes theorem in simple terms", top_k=2)

        assert response.answer == "Bayes theorem updates a prior using evidence from the supplied notes."
        assert len(response.sources) == 1
        source = response.sources[0]
        assert source.document_id == document.id
        assert source.document_name == "Probability Notes.pdf"
        assert source.page_number == 1
        assert source.chunk_id == bayes.id
        assert source.similarity > 0.99
        assert len(llm.calls) == 1
        system_prompt, user_message = llm.calls[0]
        assert system_prompt == TUTOR_SYSTEM_PROMPT
        assert "Bayes theorem updates a prior when evidence arrives." in user_message
        assert "Photosynthesis" not in user_message
        assert "Document: Probability Notes.pdf" in user_message
        assert "Page: 1" in user_message
    finally:
        session.close()
        Base.metadata.drop_all(bind=pg_engine)
        pg_engine.dispose()
