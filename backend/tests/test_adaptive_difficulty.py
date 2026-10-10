"""Deterministic difficulty plans."""

import pytest

from app.services.adaptive_assessment_service import plan_difficulties


def _plan(mastery, count=5):
    return plan_difficulties(mastery, count, easy_below=40, hard_at=70)


def test_no_previous_progress_defaults_to_medium():
    assert _plan(None) == ["medium"] * 5


def test_mastery_below_40_is_easy_focused():
    expected = ["easy", "easy", "easy", "medium", "medium"]
    assert _plan(35) == expected
    assert _plan(39.99) == expected


def test_mastery_from_40_to_just_under_70_is_medium():
    assert _plan(40) == ["medium"] * 5
    assert _plan(50) == ["medium"] * 5
    assert _plan(69.99) == ["medium"] * 5


def test_mastery_at_or_above_70_mixes_medium_and_hard():
    expected = ["medium", "medium", "hard", "hard", "medium"]
    assert _plan(70) == expected
    assert _plan(82) == expected


def test_count_must_be_positive():
    with pytest.raises(ValueError):
        _plan(50, count=0)
