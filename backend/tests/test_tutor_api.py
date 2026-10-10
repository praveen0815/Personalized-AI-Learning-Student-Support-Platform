"""Tutor API tests. The language model and vector search are stubbed."""

import uuid

from app.api.deps import get_embedding_service, get_llm_service
from app.core.exceptions import EmbeddingAPIError, LLMAPIError
from app.main import app
from app.services.tutor_prompt import NO_CONTEXT_ANSWER, TUTOR_SYSTEM_PROMPT
from app.services.vector_search_service import SearchHit, VectorSearchService
from tests.conftest import StubEmbeddings

DOCUMENT_ID = uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
CHUNK_ID = uuid.UUID("8c2d1b4e-5f7a-4c1d-9e2b-1a2b3c4d5e6f")
CHUNK_TEXT = "Bayes theorem updates a prior when evidence arrives."


class RecordingLLM:
    def __init__(self, answer: str = "Bayes theorem updates a prior using new evidence.") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_message: str) -> str:
        self.calls.append((system_prompt, user_message))
        return self.answer


def _hit(**overrides) -> SearchHit:
    values = {
        "document_id": DOCUMENT_ID,
        "document_name": "Probability Notes.pdf",
        "chunk_id": CHUNK_ID,
        "page_number": 1,
        "chunk_index": 0,
        "content": CHUNK_TEXT,
        "similarity": 0.92,
    }
    values.update(overrides)
    return SearchHit(**values)


def _patch_search(monkeypatch, hits: list[SearchHit]) -> None:
    def search(self, query_embedding, top_k):  # noqa: ANN001
        assert top_k >= 1
        assert query_embedding
        return hits

    monkeypatch.setattr(VectorSearchService, "search", search)


def _use_stubs(llm: RecordingLLM) -> None:
    app.dependency_overrides[get_embedding_service] = lambda: StubEmbeddings()
    app.dependency_overrides[get_llm_service] = lambda: llm


def test_tutor_returns_answer_and_database_sources(client, monkeypatch):
    llm = RecordingLLM(
        "The notes say page 99 and similarity 0.01, which the model must not be trusted to cite."
    )
    _use_stubs(llm)
    _patch_search(monkeypatch, [_hit()])

    response = client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain Bayes theorem in simple terms", "top_k": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == llm.answer
    assert body["sources"] == [
        {
            "document_id": str(DOCUMENT_ID),
            "document_name": "Probability Notes.pdf",
            "page_number": 1,
            "chunk_id": str(CHUNK_ID),
            "similarity": 0.92,
        }
    ]
    assert len(llm.calls) == 1
    system_prompt, user_message = llm.calls[0]
    assert system_prompt == TUTOR_SYSTEM_PROMPT
    assert "SOURCE 1" in user_message
    assert "Document: Probability Notes.pdf" in user_message
    assert "Page: 1" in user_message
    assert CHUNK_TEXT in user_message
    assert "Explain Bayes theorem in simple terms" in user_message
    assert "page 99" not in user_message


def test_empty_question_is_rejected(client):
    for payload in (
        {"question": "   ", "top_k": 5},
        {"question": "", "top_k": 5},
        {"top_k": 5},
    ):
        response = client.post("/api/v1/tutor/chat", json=payload)
        assert response.status_code == 422


def test_invalid_top_k_is_rejected(client):
    for top_k in (0, -1, 21):
        response = client.post(
            "/api/v1/tutor/chat",
            json={"question": "Explain Bayes theorem", "top_k": top_k},
        )
        assert response.status_code == 422


def test_no_relevant_context_does_not_call_the_model(client, monkeypatch):
    llm = RecordingLLM()
    _use_stubs(llm)
    _patch_search(monkeypatch, [_hit(similarity=0.2, content="Unrelated chemistry note.")])

    response = client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain Bayes theorem in simple terms"},
    )

    assert response.status_code == 200
    assert response.json() == {"answer": NO_CONTEXT_ANSWER, "sources": []}
    assert llm.calls == []


def test_empty_search_does_not_call_the_model(client, monkeypatch):
    llm = RecordingLLM()
    _use_stubs(llm)
    _patch_search(monkeypatch, [])

    response = client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain Bayes theorem in simple terms"},
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert llm.calls == []


def test_llm_failure_is_a_controlled_error(client, monkeypatch):
    class FailingLLM:
        def complete(self, system_prompt: str, user_message: str) -> str:
            raise LLMAPIError("The language model rejected the API key.")

    app.dependency_overrides[get_embedding_service] = lambda: StubEmbeddings()
    app.dependency_overrides[get_llm_service] = lambda: FailingLLM()
    _patch_search(monkeypatch, [_hit()])

    response = client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain Bayes theorem in simple terms"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The language model rejected the API key."
    assert "Traceback" not in response.text
    assert "unit-test-key" not in response.text
    assert "sk-" not in response.text


def test_missing_llm_configuration(client, monkeypatch):
    from app.core.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings().model_copy(update={"llm_provider": ""})
    app.dependency_overrides[get_embedding_service] = lambda: StubEmbeddings()
    app.dependency_overrides[get_llm_service] = lambda: LLMService(settings)
    _patch_search(monkeypatch, [_hit()])

    response = client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain Bayes theorem in simple terms"},
    )

    assert response.status_code == 503
    assert "LLM_PROVIDER" in response.json()["detail"]
    assert "Traceback" not in response.text


def test_embedding_failure_does_not_call_the_model(client):
    class FailingEmbeddings:
        def embed_query(self, text: str) -> list[float]:
            raise EmbeddingAPIError("The embedding provider returned an error.")

    llm = RecordingLLM()
    app.dependency_overrides[get_embedding_service] = lambda: FailingEmbeddings()
    app.dependency_overrides[get_llm_service] = lambda: llm

    response = client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain Bayes theorem in simple terms"},
    )

    assert response.status_code == 502
    assert llm.calls == []
    assert "Traceback" not in response.text


def test_openapi_documents_tutor_chat(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/tutor/chat"]["post"]
    assert operation["requestBody"]
    assert "TutorChatResponse" in schema["components"]["schemas"]
