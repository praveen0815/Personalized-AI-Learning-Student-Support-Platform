"""Validate structured multiple-choice questions before they are stored."""

import json
import re
from dataclasses import dataclass
from typing import Any

OPTION_KEYS = ("A", "B", "C", "D")
ALLOWED_DIFFICULTIES = ("easy", "medium", "hard")


@dataclass(frozen=True)
class ValidQuestion:
    question_text: str
    options: dict[str, str]
    correct_answer: str
    explanation: str
    difficulty: str


def parse_model_payload(raw_text: str) -> list[dict[str, Any]]:
    """Pull a JSON object or list out of a model response."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start_object = cleaned.find("{")
    start_list = cleaned.find("[")
    if start_object == -1 and start_list == -1:
        raise ValueError("The model response did not contain JSON.")
    if start_object == -1 or (start_list != -1 and start_list < start_object):
        start = start_list
        end = cleaned.rfind("]")
    else:
        start = start_object
        end = cleaned.rfind("}")
    if end <= start:
        raise ValueError("The model response did not contain JSON.")
    payload = json.loads(cleaned[start : end + 1])
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        items = payload["questions"]
    else:
        raise ValueError("The model response did not contain a question list.")
    if any(not isinstance(item, dict) for item in items):
        raise ValueError("Each question must be a JSON object.")
    return items


def validate_question(raw: dict[str, Any]) -> ValidQuestion | None:
    """Return a normalized question, or None when the item breaks the MCQ rules."""
    question_text = _clean_text(raw.get("question") or raw.get("question_text"))
    explanation = _clean_text(raw.get("explanation"))
    difficulty = _clean_text(raw.get("difficulty")).lower()
    options = _normalize_options(raw.get("options"))
    correct_answer = _normalize_correct_answer(raw.get("correct_answer"), options)
    if not question_text or not explanation or options is None or correct_answer is None:
        return None
    if difficulty not in ALLOWED_DIFFICULTIES:
        return None
    return ValidQuestion(
        question_text=question_text,
        options=options,
        correct_answer=correct_answer,
        explanation=explanation,
        difficulty=difficulty,
    )


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_options(value: Any) -> dict[str, str] | None:
    if isinstance(value, list):
        if len(value) != 4:
            return None
        mapping = {key: _clean_text(item) for key, item in zip(OPTION_KEYS, value, strict=True)}
    elif isinstance(value, dict):
        if set(value.keys()) != set(OPTION_KEYS):
            return None
        mapping = {key: _clean_text(value.get(key)) for key in OPTION_KEYS}
    else:
        return None
    if any(not text for text in mapping.values()):
        return None
    folded = [text.casefold() for text in mapping.values()]
    if len(set(folded)) != 4:
        return None
    return mapping


def _normalize_correct_answer(value: Any, options: dict[str, str] | None) -> str | None:
    if options is None or not isinstance(value, str):
        return None
    token = value.strip()
    if len(token) == 1 and token.upper() in options:
        return token.upper()
    matches = [key for key, text in options.items() if text.casefold() == token.casefold()]
    if len(matches) == 1:
        return matches[0]
    return None
