"""Weighted mastery update. Not a knowledge-tracing model."""

from app.services.learner_model import LearnerModel


def test_first_assessment_is_the_current_accuracy():
    model = LearnerModel(0.7, 0.3)
    assert model.next_mastery(None, 4, 5) == 80


def test_repeated_assessment_keeps_most_of_the_previous_mastery():
    model = LearnerModel(0.7, 0.3)
    # 60 * 0.7 + 80 * 0.3 = 66
    assert model.next_mastery(60, 4, 5) == 66


def test_weights_are_the_values_passed_in():
    model = LearnerModel(0.5, 0.5)
    assert model.next_mastery(60, 5, 5) == 80
