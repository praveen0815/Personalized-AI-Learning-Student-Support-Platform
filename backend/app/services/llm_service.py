"""Configurable chat providers for the tutor.

`openai` calls an OpenAI-compatible chat completions endpoint.
`mock` returns a fixed sentence for local checks and does not call a network API.
The API key is read from LLM_API_KEY and is never written to logs or responses.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import LLMAPIError, LLMConfigError, LLMTimeoutError

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(self, system_prompt: str, user_message: str) -> str:
        provider = self._require_provider()
        if provider == "mock":
            return "This explanation uses only the supplied learning material."
        return self._complete_openai(system_prompt, user_message)

    def _require_provider(self) -> str:
        provider = self.settings.llm_provider.strip().lower()
        if provider not in {"openai", "mock"}:
            raise LLMConfigError(
                "LLM_PROVIDER is not set. Use 'openai' or 'mock'."
            )
        if provider == "openai":
            if not self.settings.llm_model.strip():
                raise LLMConfigError("LLM_MODEL is required when LLM_PROVIDER is openai.")
            if not self.settings.llm_api_key.strip():
                raise LLMConfigError(
                    "LLM_API_KEY is not set. Add it to the environment or set LLM_PROVIDER=mock."
                )
        return provider

    def _complete_openai(self, system_prompt: str, user_message: str) -> str:
        url = self.settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        try:
            with httpx.Client(timeout=self.settings.llm_timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("The language model timed out.") from exc
        except httpx.HTTPError as exc:
            logger.warning("Language model request failed (%s)", type(exc).__name__)
            raise LLMAPIError("The language model could not be reached.") from exc

        if response.status_code >= 400:
            raise LLMAPIError(self._error_message(response))
        try:
            body = response.json()
        except ValueError as exc:
            raise LLMAPIError("The language model returned an unreadable response.") from exc

        answer = self._read_answer(body)
        if not answer.strip():
            raise LLMAPIError("The language model returned an empty answer.")
        return answer.strip()

    @staticmethod
    def _read_answer(body: Any) -> str:
        if not isinstance(body, dict):
            raise LLMAPIError("The language model returned an unexpected response.")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise LLMAPIError("The language model returned an unexpected response.")
        message = choices[0].get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise LLMAPIError("The language model returned an unexpected response.")
        return message["content"]

    def _error_message(self, response: httpx.Response) -> str:
        if response.status_code == 401:
            return "The language model rejected the API key."
        detail = ""
        try:
            body = response.json()
            error = body.get("error") if isinstance(body, dict) else None
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                detail = " ".join(error["message"].split())[:300]
        except ValueError:
            detail = ""
        detail = self._redact(detail)
        if detail:
            return f"The language model returned an error: {detail}"
        return f"The language model returned HTTP {response.status_code}."

    def _redact(self, text: str) -> str:
        secret = self.settings.llm_api_key.strip()
        if secret and secret in text:
            return text.replace(secret, "[redacted]")
        return text
