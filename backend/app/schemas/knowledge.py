"""Request and response models for the knowledge-base API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    filename: str
    total_pages: int
    total_chunks: int
    processing_status: str


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    title: str
    file_type: str
    total_pages: int
    total_chunks: int
    processing_status: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="Natural-language search text.",
        examples=["Explain Bayes theorem"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of matching chunks to return.",
    )

    @field_validator("query")
    @classmethod
    def query_must_contain_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Query must not be empty")
        return cleaned


class SearchResult(BaseModel):
    document_id: UUID
    document_name: str
    chunk_id: UUID
    page_number: int
    chunk_index: int
    content: str
    similarity: float = Field(description="Cosine similarity from pgvector (1 - cosine distance).")


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
