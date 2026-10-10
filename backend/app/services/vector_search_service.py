"""pgvector cosine similarity search over stored chunks."""

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import DatabaseUnavailableError, EmbeddingAPIError


@dataclass(frozen=True)
class SearchHit:
    document_id: uuid.UUID
    document_name: str
    chunk_id: uuid.UUID
    page_number: int
    chunk_index: int
    content: str
    similarity: float


class VectorSearchService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        bind = self.db.get_bind()
        if bind.dialect.name != "postgresql":
            raise DatabaseUnavailableError(
                "Semantic search requires PostgreSQL with the pgvector extension."
            )

        expected = self.settings.resolved_embedding_dimension
        if len(query_embedding) != expected:
            raise EmbeddingAPIError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"the configured dimension {expected}."
            )

        # Built only from numeric embedding values produced by the embedding service.
        vector_literal = "[" + ",".join(f"{float(value):.8f}" for value in query_embedding) + "]"
        statement = text(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id AS document_id,
                d.filename AS document_name,
                c.page_number AS page_number,
                c.chunk_index AS chunk_index,
                c.content AS content,
                (1 - (c.embedding <=> CAST(:embedding AS vector))) AS similarity
            FROM document_chunks AS c
            JOIN documents AS d ON d.id = c.document_id
            ORDER BY c.embedding <=> CAST(:embedding AS vector), c.chunk_index
            LIMIT :top_k
            """
        )
        try:
            rows = self.db.execute(
                statement,
                {"embedding": vector_literal, "top_k": top_k},
            ).mappings().all()
        except Exception as exc:
            raise DatabaseUnavailableError(
                "Semantic search failed. Confirm that pgvector is enabled and the "
                "embedding dimension matches the document_chunks.embedding column."
            ) from exc

        hits: list[SearchHit] = []
        for row in rows:
            hits.append(
                SearchHit(
                    document_id=row["document_id"],
                    document_name=row["document_name"],
                    chunk_id=row["chunk_id"],
                    page_number=int(row["page_number"]),
                    chunk_index=int(row["chunk_index"]),
                    content=row["content"],
                    similarity=round(float(row["similarity"]), 6),
                )
            )
        return hits
