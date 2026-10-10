"""Configurable embedding providers.

`local` uses fastembed on this machine and does not need an API key.
`openai` calls an OpenAI-compatible embeddings endpoint. The API key is read
from EMBEDDING_API_KEY and is never hard-coded.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import EmbeddingAPIError, EmbeddingConfigError

logger = logging.getLogger(__name__)

_LOCAL_MODELS: dict[str, Any] = {}


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        provider = self._require_provider()
        if not texts:
            return []
        if any(not text or not text.strip() for text in texts):
            raise EmbeddingAPIError("Cannot embed empty text.")

        if provider == "openai":
            vectors = self._embed_openai(texts)
        else:
            vectors = self._embed_local(texts, is_query=False)
        self._validate_vectors(vectors, expected_count=len(texts))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        provider = self._require_provider()
        cleaned = text.strip()
        if not cleaned:
            raise EmbeddingAPIError("Cannot embed an empty query.")
        if provider == "openai":
            vectors = self._embed_openai([cleaned])
        else:
            vectors = self._embed_local([cleaned], is_query=True)
        self._validate_vectors(vectors, expected_count=1)
        return vectors[0]

    def _require_provider(self) -> str:
        provider = self.settings.embedding_provider
        if provider not in {"openai", "local"}:
            raise EmbeddingConfigError("EMBEDDING_PROVIDER must be 'openai' or 'local'.")
        if not self.settings.embedding_model:
            raise EmbeddingConfigError("EMBEDDING_MODEL is required.")
        if provider == "openai" and not self.settings.embedding_api_key.strip():
            raise EmbeddingConfigError(
                "EMBEDDING_API_KEY is not set. Add it to the environment or switch "
                "EMBEDDING_PROVIDER to 'local'."
            )
        if self.settings.embedding_dimension is None or self.settings.embedding_dimension < 1:
            raise EmbeddingConfigError(
                "EMBEDDING_DIMENSION is not set and could not be inferred from EMBEDDING_MODEL."
            )
        return provider

    def _validate_vectors(self, vectors: list[list[float]], expected_count: int) -> None:
        expected_dim = self.settings.resolved_embedding_dimension
        if len(vectors) != expected_count:
            raise EmbeddingAPIError("The embedding provider returned an unexpected number of vectors.")
        for vector in vectors:
            if len(vector) != expected_dim:
                raise EmbeddingAPIError(
                    f"The embedding provider returned dimension {len(vector)}, "
                    f"but EMBEDDING_DIMENSION is {expected_dim}."
                )

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        url = self.settings.embedding_base_url.rstrip("/") + "/embeddings"
        headers = {
            "Authorization": f"Bearer {self.settings.embedding_api_key}",
            "Content-Type": "application/json",
        }
        ordered: list[list[float] | None] = [None] * len(texts)
        batch_size = 64
        try:
            with httpx.Client(timeout=self.settings.embedding_timeout_seconds) as client:
                for start in range(0, len(texts), batch_size):
                    batch = texts[start : start + batch_size]
                    payload: dict[str, Any] = {
                        "model": self.settings.embedding_model,
                        "input": batch,
                    }
                    if self.settings.embedding_model.lower().startswith("text-embedding-3"):
                        payload["dimensions"] = self.settings.resolved_embedding_dimension
                    response = client.post(url, headers=headers, json=payload)
                    if response.status_code >= 400:
                        raise EmbeddingAPIError(self._openai_error_message(response))
                    body = response.json()
                    data = body.get("data")
                    if not isinstance(data, list):
                        raise EmbeddingAPIError("The embedding provider returned an unexpected response.")
                    for item in data:
                        if not isinstance(item, dict):
                            raise EmbeddingAPIError("The embedding provider returned an unexpected response.")
                        index = item.get("index")
                        embedding = item.get("embedding")
                        if not isinstance(index, int) or not isinstance(embedding, list):
                            raise EmbeddingAPIError("The embedding provider returned an unexpected response.")
                        absolute = start + index
                        if absolute < 0 or absolute >= len(ordered):
                            raise EmbeddingAPIError("The embedding provider returned an unexpected response.")
                        ordered[absolute] = self._as_float_list(embedding)
        except EmbeddingAPIError:
            raise
        except httpx.TimeoutException as exc:
            raise EmbeddingAPIError("The embedding provider timed out.") from exc
        except httpx.HTTPError as exc:
            logger.warning("Embedding request failed (%s)", type(exc).__name__)
            raise EmbeddingAPIError("The embedding provider could not be reached.") from exc
        except ValueError as exc:
            raise EmbeddingAPIError("The embedding provider returned an unreadable response.") from exc

        if any(vector is None for vector in ordered):
            raise EmbeddingAPIError("The embedding provider omitted one or more vectors.")
        return [vector for vector in ordered if vector is not None]

    def _embed_local(self, texts: list[str], *, is_query: bool) -> list[list[float]]:
        model = self._load_local_model()
        try:
            if is_query and hasattr(model, "query_embed"):
                raw_vectors = model.query_embed(texts)
            else:
                raw_vectors = model.embed(texts)
            return [self._as_float_list(vector) for vector in raw_vectors]
        except EmbeddingAPIError:
            raise
        except Exception as exc:
            logger.warning("Local embedding failed (%s)", type(exc).__name__)
            detail = " ".join(str(exc).split())[:300]
            raise EmbeddingAPIError(f"Local embedding failed: {detail}") from exc

    def _load_local_model(self) -> Any:
        model_name = self.settings.embedding_model
        cached = _LOCAL_MODELS.get(model_name)
        if cached is not None:
            return cached
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise EmbeddingConfigError(
                "The local embedding provider requires the fastembed package. "
                "Install backend requirements or set EMBEDDING_PROVIDER=openai."
            ) from exc
        try:
            model = TextEmbedding(model_name=model_name)
        except Exception as exc:
            logger.warning("Could not load local embedding model (%s)", type(exc).__name__)
            detail = " ".join(str(exc).split())[:300]
            raise EmbeddingConfigError(f"Could not load embedding model '{model_name}': {detail}") from exc
        _LOCAL_MODELS[model_name] = model
        return model

    @staticmethod
    def _as_float_list(value: Any) -> list[float]:
        try:
            if hasattr(value, "tolist"):
                value = value.tolist()
            return [float(item) for item in value]
        except (TypeError, ValueError) as exc:
            raise EmbeddingAPIError("The embedding provider returned a non-numeric vector.") from exc

    @staticmethod
    def _openai_error_message(response: httpx.Response) -> str:
        detail = ""
        try:
            body = response.json()
            error = body.get("error") if isinstance(body, dict) else None
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                detail = " ".join(error["message"].split())[:300]
        except ValueError:
            detail = ""
        if response.status_code == 401:
            return "The embedding provider rejected the API key."
        if detail:
            return f"The embedding provider returned an error: {detail}"
        return f"The embedding provider returned HTTP {response.status_code}."
