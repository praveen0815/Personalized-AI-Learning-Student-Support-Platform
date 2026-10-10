"""Chunking keeps page numbers and stays within the configured size."""

import pytest

from app.services.chunking_service import split_into_chunks


def test_short_page_is_one_chunk():
    chunks = split_into_chunks([(4, "Bayes theorem relates conditional probabilities.")], 1000, 150)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 4
    assert chunks[0].content.startswith("Bayes theorem")


def test_chunks_do_not_cross_pages_and_indexes_are_sequential():
    pages = [(1, "A" * 50), (2, "B" * 50)]
    chunks = split_into_chunks(pages, chunk_size=20, chunk_overlap=5)
    assert chunks
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    page_one = [chunk for chunk in chunks if chunk.page_number == 1]
    page_two = [chunk for chunk in chunks if chunk.page_number == 2]
    assert page_one and page_two
    assert all(set(chunk.content) == {"A"} for chunk in page_one)
    assert all(set(chunk.content) == {"B"} for chunk in page_two)
    assert all(len(chunk.content) <= 20 for chunk in chunks)


def test_chunks_break_on_sentences_and_overlap():
    sentence = "Bayes theorem updates probability using evidence. "
    text = sentence * 12
    chunks = split_into_chunks([(7, text.strip())], chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(chunk.page_number == 7 for chunk in chunks)
    assert all(len(chunk.content) <= 100 for chunk in chunks)
    assert all(chunk.content.endswith(".") for chunk in chunks[:-1])
    # The next chunk starts inside the tail of the previous one.
    assert chunks[1].content[:20] in chunks[0].content or chunks[0].content[-20:] in chunks[1].content


def test_empty_page_text_produces_no_chunk():
    assert split_into_chunks([(1, "   \n")], 100, 10) == []


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        split_into_chunks([(1, "text")], chunk_size=50, chunk_overlap=50)
