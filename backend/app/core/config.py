"""Runtime configuration loaded from the environment and backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Dimensions are fixed by the model authors. text-embedding-3 also accepts a
# smaller EMBEDDING_DIMENSION via the API's dimensions parameter.
KNOWN_EMBEDDING_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "baai/bge-small-en-v1.5": 384,
    "baai/bge-base-en-v1.5": 768,
    "sentence-transformers/all-minilm-l6-v2": 384,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    database_url: str = Field(alias="DATABASE_URL")
    embedding_provider: str = Field(default="", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="", alias="EMBEDDING_MODEL")
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="EMBEDDING_BASE_URL",
    )
    embedding_dimension: int | None = Field(default=None, alias="EMBEDDING_DIMENSION")
    embedding_timeout_seconds: float = Field(default=60.0, alias="EMBEDDING_TIMEOUT_SECONDS")
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    llm_provider: str = Field(default="", alias="LLM_PROVIDER")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_timeout_seconds: float = Field(default=60.0, alias="LLM_TIMEOUT_SECONDS")
    tutor_min_similarity: float = Field(default=0.55, alias="TUTOR_MIN_SIMILARITY")
    mastery_prior_weight: float = Field(default=0.7, alias="MASTERY_PRIOR_WEIGHT")
    mastery_current_weight: float = Field(default=0.3, alias="MASTERY_CURRENT_WEIGHT")
    learning_gap_threshold: float = Field(default=60.0, alias="LEARNING_GAP_THRESHOLD")
    learning_gap_medium_floor: float = Field(default=50.0, alias="LEARNING_GAP_MEDIUM_FLOOR")
    adaptive_easy_below: float = Field(default=40.0, alias="ADAPTIVE_EASY_BELOW")
    adaptive_hard_at: float = Field(default=70.0, alias="ADAPTIVE_HARD_AT")
    assessment_max_generation_attempts: int = Field(default=2, alias="ASSESSMENT_MAX_GENERATION_ATTEMPTS")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        provider = self.embedding_provider.strip().lower()
        if provider not in {"openai", "local"}:
            raise ValueError("EMBEDDING_PROVIDER must be 'openai' or 'local'.")
        self.embedding_provider = provider

        model_name = self.embedding_model.strip()
        if not model_name:
            raise ValueError("EMBEDDING_MODEL is required.")
        self.embedding_model = model_name

        if self.chunk_size < 1:
            raise ValueError("CHUNK_SIZE must be a positive integer.")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be zero or greater and smaller than CHUNK_SIZE.")
        if self.max_upload_bytes < 1:
            raise ValueError("MAX_UPLOAD_BYTES must be a positive integer.")
        if self.embedding_timeout_seconds <= 0:
            raise ValueError("EMBEDDING_TIMEOUT_SECONDS must be positive.")
        if self.llm_timeout_seconds <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be positive.")
        if not 0 <= self.tutor_min_similarity <= 1:
            raise ValueError("TUTOR_MIN_SIMILARITY must be between 0 and 1.")
        if not 0 <= self.mastery_prior_weight <= 1 or not 0 <= self.mastery_current_weight <= 1:
            raise ValueError("Mastery weights must be between 0 and 1.")
        if abs((self.mastery_prior_weight + self.mastery_current_weight) - 1) > 1e-6:
            raise ValueError("MASTERY_PRIOR_WEIGHT and MASTERY_CURRENT_WEIGHT must sum to 1.")
        if self.learning_gap_medium_floor > self.learning_gap_threshold:
            raise ValueError("LEARNING_GAP_MEDIUM_FLOOR cannot be above LEARNING_GAP_THRESHOLD.")
        if self.adaptive_easy_below > self.adaptive_hard_at:
            raise ValueError("ADAPTIVE_EASY_BELOW cannot be above ADAPTIVE_HARD_AT.")
        if self.assessment_max_generation_attempts < 1:
            raise ValueError("ASSESSMENT_MAX_GENERATION_ATTEMPTS must be at least 1.")

        llm_provider = self.llm_provider.strip().lower()
        if llm_provider and llm_provider not in {"openai", "mock"}:
            raise ValueError("LLM_PROVIDER must be 'openai' or 'mock'.")
        self.llm_provider = llm_provider
        self.llm_model = self.llm_model.strip()

        inferred = KNOWN_EMBEDDING_DIMENSIONS.get(model_name.lower())
        allows_custom_dimension = model_name.lower().startswith("text-embedding-3")
        if self.embedding_dimension is None:
            if inferred is None:
                raise ValueError(
                    f"Cannot infer the embedding dimension for model '{model_name}'. "
                    "Set EMBEDDING_DIMENSION to that model's vector size."
                )
            self.embedding_dimension = inferred
        elif self.embedding_dimension < 1:
            raise ValueError("EMBEDDING_DIMENSION must be a positive integer.")
        elif inferred is not None and self.embedding_dimension != inferred and not allows_custom_dimension:
            raise ValueError(
                f"EMBEDDING_DIMENSION {self.embedding_dimension} does not match "
                f"model '{model_name}', which uses {inferred} dimensions."
            )
        return self

    @property
    def resolved_embedding_dimension(self) -> int:
        if self.embedding_dimension is None:
            raise ValueError("EMBEDDING_DIMENSION is not configured.")
        return self.embedding_dimension

    def resolved_upload_dir(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        resolved = path.resolve()
        return resolved


@lru_cache
def get_settings() -> Settings:
    return Settings()
