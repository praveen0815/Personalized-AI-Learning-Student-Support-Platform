"""PDF extraction and cleaning."""

import pytest

from app.core.exceptions import InvalidPdfError
from app.services.pdf_service import clean_text, extract_pdf
from tests.pdf_factory import build_pdf


def test_clean_text_collapses_whitespace_and_keeps_paragraphs():
    cleaned = clean_text("Bayes   theorem\r\n\r\n\r\nuses   evidence\x00")
    assert cleaned == "Bayes theorem\n\nuses evidence"


def test_extract_pdf_preserves_page_numbers_and_skips_empty_pages():
    data = build_pdf(
        [
            "Bayes theorem updates a prior with evidence.",
            "",
            "The likelihood is multiplied by the prior.",
        ],
        title="Probability Notes",
    )
    extracted = extract_pdf(data)
    assert extracted.total_pages == 3
    assert extracted.title == "Probability Notes"
    assert [page_number for page_number, _text in extracted.pages] == [1, 3]
    assert "Bayes theorem" in extracted.pages[0][1]
    assert "likelihood" in extracted.pages[1][1]


def test_extract_pdf_with_no_text():
    data = build_pdf([""])
    extracted = extract_pdf(data)
    assert extracted.total_pages == 1
    assert extracted.pages == []


def test_extract_pdf_rejects_invalid_bytes():
    with pytest.raises(InvalidPdfError):
        extract_pdf(b"%PDF-1.7 this is not a readable document")


def test_extract_pdf_rejects_empty_input():
    with pytest.raises(InvalidPdfError):
        extract_pdf(b"")
