"""Upload, document metadata, and search validation."""

import re
import uuid
from pathlib import Path

from sqlalchemy import select

from app.api.deps import get_embedding_service
from app.core.config import get_settings
from app.core.exceptions import EmbeddingAPIError
from app.db.database import SessionLocal
from app.db.models import Document, DocumentChunk
from app.main import app
from app.services.embedding_service import EmbeddingService
from tests.conftest import StubEmbeddings
from tests.pdf_factory import build_pdf


def _use_stub():
    app.dependency_overrides[get_embedding_service] = lambda: StubEmbeddings()


def test_rejects_non_pdf_extension(client):
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_rejects_pdf_extension_with_wrong_contents(client):
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]


def test_rejects_empty_upload(client):
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400


def test_rejects_pdf_with_no_extractable_text(client):
    _use_stub()
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("blank.pdf", build_pdf([""]), "application/pdf")},
    )
    assert response.status_code == 422
    assert "extractable text" in response.json()["detail"]


def test_rejects_oversized_pdf(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 32)
    payload = build_pdf(["Bayes theorem is longer than the test limit."])
    assert len(payload) > 32
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.pdf", payload, "application/pdf")},
    )
    assert response.status_code == 413


def test_upload_stores_metadata_chunks_and_page_numbers(client, tmp_path):
    _use_stub()
    payload = build_pdf(
        [
            "Bayes theorem updates a prior with evidence.",
            "",
            "The likelihood is multiplied by the prior.",
        ],
        title="Probability Notes",
    )
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": (r"..\..\secret.pdf", payload, "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "secret.pdf"
    assert body["total_pages"] == 3
    assert body["total_chunks"] == 2
    assert body["processing_status"] == "completed"
    assert "file_path" not in body
    assert "secret" not in body["document_id"]

    listed = client.get("/api/v1/knowledge/documents")
    assert listed.status_code == 200
    documents = listed.json()["documents"]
    assert len(documents) == 1
    assert documents[0]["id"] == body["document_id"]
    assert documents[0]["title"] == "Probability Notes"
    assert documents[0]["file_type"] == "pdf"
    assert "file_path" not in documents[0]

    detail = client.get(f"/api/v1/knowledge/documents/{body['document_id']}")
    assert detail.status_code == 200
    assert detail.json()["total_pages"] == 3
    assert detail.json()["total_chunks"] == 2
    assert detail.json()["processing_status"] == "completed"

    with SessionLocal() as db:
        document = db.get(Document, uuid.UUID(body["document_id"]))
        stored = Path(document.file_path)
        assert stored.parent == tmp_path.resolve()
        assert re.fullmatch(r"[0-9a-f]{32}\.pdf", stored.name)
        chunks = list(db.scalars(select(DocumentChunk).order_by(DocumentChunk.chunk_index)))
    assert [chunk.page_number for chunk in chunks] == [1, 3]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert "Bayes theorem" in chunks[0].content
    assert chunks[0].embedding[0] == 1.0
    assert len(chunks[0].embedding) == get_settings().resolved_embedding_dimension
    assert stored.read_bytes().startswith(b"%PDF")


def test_upload_passes_configured_chunk_size(client, monkeypatch):
    _use_stub()
    seen: dict[str, int] = {}
    from app.services import document_service as document_service_module

    real_split = document_service_module.split_into_chunks

    def spy(pages, chunk_size, chunk_overlap):
        seen["chunk_size"] = chunk_size
        seen["chunk_overlap"] = chunk_overlap
        return real_split(pages, chunk_size, chunk_overlap)

    monkeypatch.setattr(document_service_module, "split_into_chunks", spy)
    monkeypatch.setattr(get_settings(), "chunk_size", 400)
    monkeypatch.setattr(get_settings(), "chunk_overlap", 40)
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.pdf", build_pdf(["A short note about priors."]), "application/pdf")},
    )
    assert response.status_code == 201
    assert seen == {"chunk_size": 400, "chunk_overlap": 40}


def test_embedding_config_error_on_upload(client):
    settings = get_settings().model_copy(update={"embedding_api_key": ""})
    app.dependency_overrides[get_embedding_service] = lambda: EmbeddingService(settings)
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.pdf", build_pdf(["A note."]), "application/pdf")},
    )
    assert response.status_code == 503
    assert "EMBEDDING_API_KEY" in response.json()["detail"]
    assert "unit-test-key" not in response.text
    assert client.get("/api/v1/knowledge/documents").json()["documents"] == []


def test_embedding_api_failure_does_not_store_a_document(client, tmp_path):
    class FailingEmbeddings:
        def embed_texts(self, texts):
            raise EmbeddingAPIError("The embedding provider returned an error.")

    app.dependency_overrides[get_embedding_service] = lambda: FailingEmbeddings()
    response = client.post(
        "/api/v1/knowledge/documents",
        files={"file": ("notes.pdf", build_pdf(["A note."]), "application/pdf")},
    )
    assert response.status_code == 502
    assert "Traceback" not in response.text
    assert client.get("/api/v1/knowledge/documents").json()["documents"] == []
    assert list(tmp_path.glob("*.pdf")) == []


def test_document_not_found(client):
    response = client.get("/api/v1/knowledge/documents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_invalid_document_id(client):
    response = client.get("/api/v1/knowledge/documents/not-a-uuid")
    assert response.status_code == 422


def test_search_rejects_empty_query(client):
    _use_stub()
    for payload in ({"query": "   ", "top_k": 5}, {"query": "", "top_k": 5}, {"top_k": 5}):
        response = client.post("/api/v1/knowledge/search", json=payload)
        assert response.status_code == 422


def test_search_rejects_invalid_top_k(client):
    _use_stub()
    for top_k in (0, -1, 21):
        response = client.post(
            "/api/v1/knowledge/search",
            json={"query": "Explain Bayes theorem", "top_k": top_k},
        )
        assert response.status_code == 422


def test_search_on_non_postgres_backend_is_explicit(client):
    _use_stub()
    response = client.post(
        "/api/v1/knowledge/search",
        json={"query": "Explain Bayes theorem"},
    )
    assert response.status_code == 503
    assert "pgvector" in response.json()["detail"]
