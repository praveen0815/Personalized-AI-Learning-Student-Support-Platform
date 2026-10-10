"""Request and response models for the source-grounded tutor."""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TutorChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="Student question answered only from uploaded learning material.",
        examples=["Explain Bayes theorem in simple terms"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of knowledge-base chunks to retrieve before applying the similarity threshold.",
    )

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Question must not be empty")
        return cleaned


class TutorSource(BaseModel):
    document_id: UUID
    document_name: str = Field(description="Filename stored with the document record.")
    page_number: int = Field(description="Page number stored on the retrieved chunk.")
    chunk_id: UUID = Field(description="Identifier of the retrieved chunk.")
    similarity: float = Field(description="Cosine similarity returned by pgvector for this chunk.")


class TutorChatResponse(BaseModel):
    answer: str
    sources: list[TutorSource]
