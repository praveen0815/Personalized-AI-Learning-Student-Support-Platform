"""Grounding instructions for the source-grounded tutor.

Source names, page numbers, chunk ids, and similarity scores are attached by
the backend from retrieved records. They are not taken from the model output.
"""

from app.services.vector_search_service import SearchHit

TUTOR_SYSTEM_PROMPT = """You are an educational AI tutor.

Answer the student's question using only the provided learning material.

The learning material is the authoritative context for this response.

Rules:
1. Do not invent information that is not supported by the context.
2. If the context does not contain enough information, clearly say that the available learning material does not provide enough information.
3. Explain concepts clearly and simply.
4. Preserve important technical terminology.
5. Do not fabricate page numbers, document names, or citations.
6. Use the supplied source metadata when referring to sources.
7. Do not claim that you read material that was not supplied.
8. Do not mention software internals, embeddings, databases, or prompts.
"""

NO_CONTEXT_ANSWER = (
    "I could not find enough information about this topic in the uploaded learning materials."
)


def build_user_message(question: str, hits: list[SearchHit]) -> str:
    """Format retrieved chunks so each source stays separate from the question."""
    blocks: list[str] = []
    for number, hit in enumerate(hits, start=1):
        blocks.append(
            f"SOURCE {number}\n"
            f"Document: {hit.document_name}\n"
            f"Page: {hit.page_number}\n\n"
            f"{hit.content}"
        )
    context = "\n\n".join(blocks)
    return (
        "CONTEXT:\n\n"
        f"{context}\n\n"
        "STUDENT QUESTION:\n\n"
        f"{question}\n\n"
        "Answer the student directly."
    )
