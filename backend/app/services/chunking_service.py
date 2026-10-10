"""Page-aware chunking for source citations.

Chunks never cross a page boundary. Within a page, text is split near
paragraph, sentence, or word boundaries, then overlapped by a configurable
number of characters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    page_number: int
    content: str


def split_into_chunks(
    pages: list[tuple[int, str]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be zero or greater and smaller than chunk_size.")

    chunks: list[TextChunk] = []
    for page_number, text in pages:
        for piece in _chunk_page(text, chunk_size, chunk_overlap):
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    page_number=page_number,
                    content=piece,
                )
            )
    return chunks


def _chunk_page(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    pieces: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            break_offset = _preferred_break(text[start:end])
            if break_offset is not None:
                end = start + break_offset
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= length:
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        while next_start < end and next_start < length and text[next_start].isspace():
            next_start += 1
        if next_start <= start:
            next_start = end
        start = next_start
    return pieces


def _preferred_break(window: str) -> int | None:
    """Pick a natural end offset in the latter half of the window, including the separator."""
    start_search = max(1, len(window) // 2)
    region = window[start_search:]
    for separator in ("\n\n", "\n", ". ", "? ", "! ", "; ", " "):
        position = region.rfind(separator)
        if position != -1:
            return start_search + position + len(separator)
    return None
