"""Prompt for grounded multiple-choice generation.

Page numbers and document names are attached by the backend from retrieved
chunks. The model is not asked to invent them.
"""

from app.services.vector_search_service import SearchHit

ASSESSMENT_SYSTEM_PROMPT = """You write multiple-choice questions for a student.

Use only the supplied learning material. Do not add facts that are not supported by that material.

Rules:
1. Every question must be answerable from the supplied context.
2. Each question has exactly four options labeled A, B, C, and D.
3. Exactly one option is correct.
4. Include a short explanation that cites the idea from the context, not a page number.
5. Do not invent document names, page numbers, or citations.
6. Use only these difficulty labels: easy, medium, hard.
7. Return JSON only, with no markdown.

JSON shape:
{"questions":[{"question":"...","options":{"A":"...","B":"...","C":"...","D":"..."},"correct_answer":"A","explanation":"...","difficulty":"medium"}]}
"""


def build_generation_message(
    topic: str,
    difficulties: list[str],
    hits: list[SearchHit],
) -> str:
    blocks: list[str] = []
    for number, hit in enumerate(hits, start=1):
        blocks.append(f"SOURCE {number}\n{hit.content}")
    context = "\n\n".join(blocks)
    difficulty_line = ", ".join(difficulties)
    return (
        f"Topic: {topic}\n"
        f"Create exactly {len(difficulties)} questions.\n"
        f"Use these difficulties in order: {difficulty_line}.\n\n"
        "CONTEXT:\n\n"
        f"{context}"
    )
