"""Embedding provider configuration and HTTP error handling. No live API calls."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import EmbeddingAPIError, EmbeddingConfigError
from app.services.embedding_service import EmbeddingService


def test_missing_api_key_is_a_configuration_error():
    settings = get_settings().model_copy(update={"embedding_api_key": ""})
    service = EmbeddingService(settings)
    with pytest.raises(EmbeddingConfigError, match="EMBEDDING_API_KEY"):
        service.embed_query("Explain Bayes theorem")


def _rebuild_settings(**overrides):
    values = get_settings().model_dump()
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_unknown_model_requires_an_explicit_dimension(monkeypatch):
    monkeypatch.delenv("EMBEDDING_DIMENSION", raising=False)
    with pytest.raises(ValidationError, match="EMBEDDING_DIMENSION"):
        _rebuild_settings(embedding_model="my-custom-model", embedding_dimension=None)


def test_fixed_model_rejects_the_wrong_dimension():
    with pytest.raises(ValidationError, match="1536"):
        _rebuild_settings(embedding_model="text-embedding-ada-002", embedding_dimension=384)


def test_openai_error_does_not_include_the_api_key(monkeypatch):
    class FakeResponse:
        status_code = 401

        def json(self):
            return {"error": {"message": "Incorrect API key provided: sk-secret"}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            authorization = kwargs["headers"]["Authorization"]
            assert authorization == "Bearer unit-test-key"
            assert "sk-secret" not in authorization
            return FakeResponse()

    monkeypatch.setattr("app.services.embedding_service.httpx.Client", FakeClient)
    service = EmbeddingService(get_settings())
    with pytest.raises(EmbeddingAPIError, match="rejected the API key") as caught:
        service.embed_texts(["Bayes theorem"])
    assert "unit-test-key" not in str(caught.value)
    assert "sk-secret" not in str(caught.value)


def test_openai_success_returns_the_provider_vector(monkeypatch):
    dimension = get_settings().resolved_embedding_dimension
    provider_vector = [0.0] * dimension
    provider_vector[3] = 0.42

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"data": [{"index": 0, "embedding": provider_vector}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.services.embedding_service.httpx.Client", FakeClient)
    vectors = EmbeddingService(get_settings()).embed_texts(["prior probability"])
    assert vectors == [provider_vector]


def test_dimension_mismatch_is_rejected(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"data": [{"index": 0, "embedding": [0.1, 0.2]}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.services.embedding_service.httpx.Client", FakeClient)
    with pytest.raises(EmbeddingAPIError, match="dimension"):
        EmbeddingService(get_settings()).embed_texts(["prior probability"])
