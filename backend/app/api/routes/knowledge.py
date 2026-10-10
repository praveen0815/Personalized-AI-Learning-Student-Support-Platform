"""Knowledge-base HTTP routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_embedding_service
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.database import get_db
from app.schemas.knowledge import (
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Upload an educational PDF",
    description=(
        "Accepts one PDF, extracts page text, chunks it, embeds each chunk, "
        "and stores the document plus vectors in PostgreSQL."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file"),
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    filename = file.filename or ""
    try:
        data = await file.read()
    except Exception as exc:
        raise AppError("The file upload failed.", status_code=400) from exc
    finally:
        await file.close()

    document = DocumentService(db, embeddings, settings).ingest_pdf(
        filename,
        file.content_type,
        data,
    )
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        total_pages=document.total_pages,
        total_chunks=document.total_chunks,
        processing_status=document.processing_status,
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
)
def list_documents(
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    settings: Settings = Depends(get_settings),
) -> DocumentListResponse:
    documents = DocumentService(db, embeddings, settings).list_documents()
    return DocumentListResponse(documents=[DocumentSummary.model_validate(item) for item in documents])


@router.get(
    "/documents/{document_id}",
    response_model=DocumentSummary,
    summary="Get one document",
    responses={404: {"description": "Document not found"}},
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    settings: Settings = Depends(get_settings),
) -> DocumentSummary:
    document = DocumentService(db, embeddings, settings).get_document(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=404)
    return DocumentSummary.model_validate(document)


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search uploaded material by meaning",
    description=(
        "Embeds the query and returns the closest chunks using pgvector cosine similarity. "
        "Similarity scores come from the database, not from a fixed value."
    ),
)
def search_knowledge(
    body: SearchRequest,
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    query_embedding = embeddings.embed_query(body.query)
    hits = VectorSearchService(db, settings).search(query_embedding, body.top_k)
    return SearchResponse(
        query=body.query,
        results=[
            SearchResult(
                document_id=hit.document_id,
                document_name=hit.document_name,
                chunk_id=hit.chunk_id,
                page_number=hit.page_number,
                chunk_index=hit.chunk_index,
                content=hit.content,
                similarity=hit.similarity,
            )
            for hit in hits
        ],
    )
