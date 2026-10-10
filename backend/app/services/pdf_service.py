"""Extract and clean text from educational PDFs with PyMuPDF."""

import re
from dataclasses import dataclass

import pymupdf

from app.core.exceptions import EmptyPdfError, InvalidPdfError


@dataclass(frozen=True)
class ExtractedPdf:
    total_pages: int
    title: str | None
    pages: list[tuple[int, str]]


def clean_text(text: str) -> str:
    """Normalize whitespace while keeping paragraph breaks."""
    text = text.replace("\x00", "").replace("\u00ad", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(data: bytes) -> ExtractedPdf:
    """Return 1-based page numbers and cleaned text. Empty pages are omitted."""
    if not data:
        raise InvalidPdfError("The uploaded file is empty.")
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise InvalidPdfError("The uploaded file is not a valid PDF.") from exc

    try:
        if document.needs_pass:
            raise InvalidPdfError("Encrypted PDFs are not supported.")
        total_pages = document.page_count
        if total_pages < 1:
            raise EmptyPdfError("The PDF contains no pages.")

        metadata = document.metadata or {}
        raw_title = metadata.get("title") if isinstance(metadata, dict) else None
        title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else None

        pages: list[tuple[int, str]] = []
        for index, page in enumerate(document, start=1):
            cleaned = clean_text(page.get_text("text") or "")
            if cleaned:
                pages.append((index, cleaned))
        return ExtractedPdf(total_pages=total_pages, title=title, pages=pages)
    except (InvalidPdfError, EmptyPdfError):
        raise
    except Exception as exc:
        raise InvalidPdfError("The uploaded file could not be read as a PDF.") from exc
    finally:
        document.close()
