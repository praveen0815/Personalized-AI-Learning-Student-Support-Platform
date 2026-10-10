"""Question-shape checks used before an MCQ is stored."""

import pytest

from app.services.question_validation import parse_model_payload, validate_question


def _raw(**overrides):
    item = {
        "question": "What does Bayes theorem update?",
        "options": {"A": "A prior", "B": "A page number", "C": "A filename", "D": "A password"},
        "correct_answer": "A",
        "explanation": "The notes say it updates a prior.",
        "difficulty": "medium",
    }
    item.update(overrides)
    return item


def test_valid_question_normalizes_the_answer_letter():
    parsed = validate_question(_raw(correct_answer=" a "))
    assert parsed is not None
    assert parsed.correct_answer == "A"
    assert list(parsed.options) == ["A", "B", "C", "D"]


def test_options_may_be_a_list_of_four_strings():
    parsed = validate_question(_raw(options=["A prior", "A page", "A file", "A key"], correct_answer="A prior"))
    assert parsed is not None
    assert parsed.correct_answer == "A"


def test_malformed_json_is_rejected():
    with pytest.raises(ValueError):
        parse_model_payload("this is not json")


def test_wrong_number_of_options_is_rejected():
    assert validate_question(_raw(options={"A": "one", "B": "two", "C": "three"})) is None


def test_invalid_difficulty_is_rejected():
    assert validate_question(_raw(difficulty="extreme")) is None


def test_invalid_correct_answer_is_rejected():
    assert validate_question(_raw(correct_answer="E")) is None


def test_duplicate_option_text_is_rejected():
    assert validate_question(_raw(options={"A": "Same", "B": "same", "C": "Other", "D": "Else"})) is None
