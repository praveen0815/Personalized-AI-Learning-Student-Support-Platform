"""Language-model provider errors. No live API calls."""

import httpx
import pytest

from app.core.config import get_settings
from app.core.exceptions import LLMAPIError, LLMConfigError, LLMTimeoutError
from app.services.llm_service import LLMService


def _openai_settings():
    return get_settings().model_copy(
        update={
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "llm_api_key": "sk-test-secret",
            "llm_base_url": "https://api.openai.com/v1",
        }
    )


def test_openai_error_redacts_the_api_key(monkeypatch):
    class FakeResponse:
        status_code = 500

        def json(self):
            return {"error": {"message": "failure for key sk-test-secret"}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers, json):
            assert headers["Authorization"] == "Bearer sk-test-secret"
            assert url.endswith("/chat/completions")
            assert json["messages"][0]["role"] == "system"
            assert json["messages"][1]["content"] == "student question"
            return FakeResponse()

    monkeypatch.setattr("app.services.llm_service.httpx.Client", FakeClient)
    with pytest.raises(LLMAPIError) as caught:
        LLMService(_openai_settings()).complete("system rules", "student question")
    assert "sk-test-secret" not in str(caught.value)
    assert "[redacted]" in str(caught.value)


def test_openai_timeout(monkeypatch):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            raise httpx.TimeoutException("timed out")

    monkeypatch.setattr("app.services.llm_service.httpx.Client", FakeClient)
    with pytest.raises(LLMTimeoutError, match="timed out"):
        LLMService(_openai_settings()).complete("system rules", "student question")


def test_mock_provider_does_not_use_the_network():
    settings = get_settings().model_copy(update={"llm_provider": "mock", "llm_api_key": ""})
    answer = LLMService(settings).complete("system rules", "What is a black hole?")
    assert answer == "This explanation uses only the supplied learning material."
    assert "black hole" not in answer


def test_missing_provider_is_a_configuration_error():
    settings = get_settings().model_copy(update={"llm_provider": ""})
    with pytest.raises(LLMConfigError, match="LLM_PROVIDER"):
        LLMService(settings).complete("system rules", "Explain Bayes theorem")
