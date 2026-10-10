"""Shared FastAPI dependencies."""

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


def get_embedding_service(settings: Settings = Depends(get_settings)) -> EmbeddingService:
    return EmbeddingService(settings)


def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    return LLMService(settings)
