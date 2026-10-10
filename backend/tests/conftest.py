"""Unit-test setup. Forces SQLite so pytest never writes to PostgreSQL."""

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["EMBEDDING_PROVIDER"] = "openai"
os.environ["EMBEDDING_MODEL"] = "text-embedding-3-small"
os.environ["EMBEDDING_API_KEY"] = "unit-test-key"
os.environ["EMBEDDING_DIMENSION"] = "1536"
os.environ["CHUNK_SIZE"] = "1000"
os.environ["CHUNK_OVERLAP"] = "150"
os.environ["MAX_UPLOAD_BYTES"] = "20971520"
os.environ["UPLOAD_DIR"] = "uploads"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_MODEL"] = "mock"
os.environ["LLM_TIMEOUT_SECONDS"] = "60"
os.environ["TUTOR_MIN_SIMILARITY"] = "0.55"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import Base, engine
from app.db import models  # noqa: F401
from app.main import app


class StubEmbeddings:
    """Deterministic stand-in used so unit tests never call an embedding API."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        dimension = get_settings().resolved_embedding_dimension
        vectors: list[list[float]] = []
        for index, _text in enumerate(texts):
            vector = [0.0] * dimension
            vector[0] = float(index + 1)
            vectors.append(vector)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
