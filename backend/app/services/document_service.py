"""Store an uploaded educational PDF as metadata, chunks, and embeddings."""

import re
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    AppError,
    DatabaseUnavailableError,
    EmptyPdfError,
    InvalidPdfError,
)
from app.db.database import ensure_database_available
from app.db.models import Document, DocumentChunk
from app.services.chunking_service import split_into_chunks
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import extract_pdf

_PDF_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
    "binary/octet-stream",
}


class DocumentService:
    def __init__(self, db: Session, embeddings: EmbeddingService, settings: Settings) -> None:
        self.db = db
        self.embeddings = embeddings
        self.settings = settings

    def list_documents(self) -> list[Document]:
        ensure_database_available(self.db)
        return list(self.db.scalars(select(Document).order_by(Document.created_at.desc())))

    def get_document(self, document_id: uuid.UUID) -> Document | None:
        ensure_database_available(self.db)
        return self.db.get(Document, document_id)

    def ingest_pdf(self, original_filename: str, content_type: str | None, data: bytes) -> Document:
        safe_name = sanitize_filename(original_filename)
        validate_upload(content_type, data, self.settings.max_upload_bytes)
        extracted = extract_pdf(data)
        if not extracted.pages:
            raise EmptyPdfError("The PDF contains no extractable text.")

        chunks = split_into_chunks(
            extracted.pages,
            self.settings.chunk_size,
            self.settings.chunk_overlap,
        )
        if not chunks:
            raise EmptyPdfError("The PDF contains no extractable text.")

        ensure_database_available(self.db)
        vectors = self.embeddings.embed_texts([chunk.content for chunk in chunks])
        stored_path = self._write_pdf(data)
        try:
            return self._persist(
                filename=safe_name,
                title=extracted.title or Path(safe_name).stem,
                file_path=stored_path,
                total_pages=extracted.total_pages,
                chunks=chunks,
                vectors=vectors,
            )
        except Exception:
            stored_path.unlink(missing_ok=True)
            raise

    def _write_pdf(self, data: bytes) -> Path:
        upload_dir = self.settings.resolved_upload_dir()
        destination = (upload_dir / f"{uuid.uuid4().hex}.pdf").resolve()
        if not destination.is_relative_to(upload_dir) or destination.parent != upload_dir:
            raise InvalidPdfError("The file could not be stored safely.")
        try:
            destination.write_bytes(data)
        except OSError as exc:
            raise AppError("The uploaded file could not be stored.", status_code=500) from exc
        return destination

    def _persist(
        self,
        filename: str,
        title: str,
        file_path: Path,
        total_pages: int,
        chunks,
        vectors: list[list[float]],
    ) -> Document:
        document = Document(
            filename=filename,
            title=title[:500],
            file_type="pdf",
            file_path=str(file_path),
            total_pages=total_pages,
            total_chunks=len(chunks),
            processing_status="completed",
        )
        try:
            self.db.add(document)
            self.db.flush()
            for chunk, vector in zip(chunks, vectors, strict=True):
                self.db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        page_number=chunk.page_number,
                        content=chunk.content,
                        embedding=vector,
                    )
                )
            self.db.commit()
            self.db.refresh(document)
            return document
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseUnavailableError("Database error while saving the document.") from exc
        except Exception:
            self.db.rollback()
            raise


def sanitize_filename(filename: str) -> str:
    name = Path(filename or "").name.replace("\x00", "").strip()
    if not name:
        raise InvalidPdfError("A PDF filename is required.")
    if not name.lower().endswith(".pdf"):
        raise InvalidPdfError("Only PDF files are supported.")
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    if len(name) > 200:
        name = name[:196] + ".pdf"
    return name


def validate_upload(content_type: str | None, data: bytes, max_upload_bytes: int) -> None:
    if content_type:
        mime = content_type.split(";")[0].strip().lower()
        if mime not in _PDF_MIME_TYPES:
            raise InvalidPdfError("Only PDF files are supported.")
    if not data:
        raise InvalidPdfError("The uploaded file is empty.")
    if len(data) > max_upload_bytes:
        raise AppError(
            f"File exceeds the maximum upload size of {max_upload_bytes} bytes.",
            status_code=413,
        )
    header = data[:1024].lstrip()
    if not header.startswith(b"%PDF"):
        raise InvalidPdfError("The uploaded file is not a PDF.")
