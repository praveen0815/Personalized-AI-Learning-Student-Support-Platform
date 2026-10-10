"""Explainable mastery update.

This is a weighted average for an MVP learner record. It is not Deep Knowledge
Tracing, Bayesian Knowledge Tracing, or a validated measurement model.

First attempt:
    mastery = accuracy * 100

Later attempts:
    new = (old_mastery * prior_weight) + (accuracy * 100 * current_weight)

Default weights are 0.7 for the previous mastery and 0.3 for the current accuracy.
With old mastery 60 and current accuracy 80%:
    60 * 0.7 + 80 * 0.3 = 66
"""


class LearnerModel:
    def __init__(self, prior_weight: float, current_weight: float) -> None:
        self.prior_weight = prior_weight
        self.current_weight = current_weight

    def next_mastery(self, previous: float | None, correct: int, attempted: int) -> float:
        if attempted < 1:
            raise ValueError("Mastery needs at least one answered question.")
        accuracy_points = (correct / attempted) * 100
        if previous is None:
            updated = accuracy_points
        else:
            updated = (previous * self.prior_weight) + (accuracy_points * self.current_weight)
        return round(updated, 2)
