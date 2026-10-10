"""pgvector similarity against a real PostgreSQL database.

Skipped unless INTEGRATION_DATABASE_URL points at a database whose name contains "test".
This test inserts known vectors and reads cosine similarity from pgvector.
It does not call an embedding API.
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
from app.services.vector_search_service import VectorSearchService


pytestmark = pytest.mark.integration


def _basis(index: int, dimension: int) -> list[float]:
    vector = [0.0] * dimension
    vector[index] = 1.0
    return vector


def test_pgvector_ranks_chunks_by_cosine_similarity():
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
            filename="Engineering Mathematics.pdf",
            title="Engineering Mathematics",
            file_type="pdf",
            file_path="unused-by-search",
            total_pages=2,
            total_chunks=2,
            processing_status="completed",
        )
        session.add(document)
        session.flush()
        alpha = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            page_number=24,
            content="Alpha chunk about Bayes theorem.",
            embedding=_basis(0, dimension),
        )
        beta = DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            page_number=25,
            content="Beta chunk about unrelated material.",
            embedding=_basis(1, dimension),
        )
        session.add_all([alpha, beta])
        session.commit()

        hits = VectorSearchService(session, get_settings()).search(_basis(0, dimension), top_k=2)
        assert len(hits) == 2
        assert hits[0].content == "Alpha chunk about Bayes theorem."
        assert hits[0].document_name == "Engineering Mathematics.pdf"
        assert hits[0].document_id == document.id
        assert hits[0].page_number == 24
        assert hits[0].chunk_index == 0
        assert hits[0].similarity > 0.99
        assert hits[1].content == "Beta chunk about unrelated material."
        assert hits[1].similarity < 0.01
        assert hits[0].similarity > hits[1].similarity
    finally:
        session.close()
        Base.metadata.drop_all(bind=pg_engine)
        pg_engine.dispose()
