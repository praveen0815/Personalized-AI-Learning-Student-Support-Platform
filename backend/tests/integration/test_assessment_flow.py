"""Assessment flow against PostgreSQL + pgvector.

The query embedding is a known vector and the language model is a local stand-in.
No external language-model API is called.
"""

import json
import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.assessment_models import Question
from app.db.database import Base, enable_pgvector
from app.db.models import Document, DocumentChunk
from app.services.assessment_prompt import ASSESSMENT_SYSTEM_PROMPT
from app.services.assessment_service import AssessmentService


pytestmark = pytest.mark.integration


def _keys(value) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        found.update(value)
        for item in value.values():
            found.update(_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_keys(item))
    return found


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
        return json.dumps(
            {
                "questions": [
                    {
                        "question": "What does Bayes theorem update?",
                        "options": {
                            "A": "A prior when evidence arrives",
                            "B": "A page number",
                            "C": "A filename",
                            "D": "A password",
                        },
                        "correct_answer": "A",
                        "explanation": "The notes say a prior is updated when evidence arrives.",
                        "difficulty": "medium",
                    }
                ]
            }
        )


def test_grounded_assessment_submission_progress_and_gap():
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
            file_path="unused-by-assessment-test",
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
        service = AssessmentService(session, FixedEmbeddings(_basis(0, dimension)), llm, get_settings())
        student = service.create_student("Asha")
        created = service.generate(student.id, "Bayes Theorem", 1)

        assert created["status"] == "created"
        assert len(llm.calls) == 1
        system_prompt, user_message = llm.calls[0]
        assert system_prompt == ASSESSMENT_SYSTEM_PROMPT
        assert "Bayes theorem updates a prior when evidence arrives." in user_message
        assert "Photosynthesis" not in user_message
        public = created["assessment"]
        assert "correct_answer" not in _keys(public)
        assert "explanation" not in _keys(public)
        question = public["questions"][0]
        assert question["source_document_name"] == "Probability Notes.pdf"
        assert question["source_page_number"] == 1
        stored = session.get(Question, question["id"])
        assert stored is not None
        assert stored.correct_answer == "A"
        assert stored.source_document_id == document.id
        assert stored.source_chunk_id == bayes.id
        assert stored.source_page_number == 1

        result = service.submit(
            public["id"],
            student.id,
            [type("Answer", (), {"question_id": question["id"], "selected_option": "B"})()],
        )
        assert result["score"] == 0
        assert result["topic_results"][0]["mastery"] == 0
        assert result["learning_gaps"][0]["severity"] == "high"
        assert result["learning_gaps"][0]["reason"] == "1 of the last 1 questions was answered incorrectly."
        progress = service.list_progress(student.id)
        assert progress[0].topic == "Bayes Theorem"
        assert progress[0].questions_attempted == 1
        gaps = service.list_active_gaps(student.id)
        assert len(gaps) == 1
        assert gaps[0].topic == "Bayes Theorem"
    finally:
        session.close()
        Base.metadata.drop_all(bind=pg_engine)
        pg_engine.dispose()
