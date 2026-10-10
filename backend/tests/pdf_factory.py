"""Build small in-memory PDFs for tests."""

import pymupdf


def build_pdf(pages: list[str], title: str | None = None) -> bytes:
    document = pymupdf.open()
    if title:
        document.set_metadata({"title": title})
    for text in pages:
        page = document.new_page()
        if text:
            page.insert_textbox(
                pymupdf.Rect(72, 72, 540, 770),
                text,
                fontsize=11,
                fontname="helv",
            )
    try:
        return document.tobytes()
    finally:
        document.close()
