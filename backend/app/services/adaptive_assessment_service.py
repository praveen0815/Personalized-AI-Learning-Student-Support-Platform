"""Choose the next question difficulties from topic mastery.

The plan is deterministic:

- No previous mastery: every question is medium.
- mastery < ADAPTIVE_EASY_BELOW (default 40): about 60% easy, the rest medium.
  Five questions become easy, easy, easy, medium, medium.
- ADAPTIVE_EASY_BELOW <= mastery < ADAPTIVE_HARD_AT (default 70): every question is medium.
- mastery >= ADAPTIVE_HARD_AT: half the questions are hard and the rest are medium.
  Five questions become medium, medium, hard, hard, medium.

This is not a reinforcement-learning policy.
"""

import math

from app.core.config import Settings


def plan_difficulties(
    mastery: float | None,
    count: int,
    *,
    easy_below: float,
    hard_at: float,
) -> list[str]:
    if count < 1:
        raise ValueError("An assessment needs at least one question.")
    if mastery is None or easy_below <= mastery < hard_at:
        return ["medium"] * count
    if mastery < easy_below:
        easy_count = min(count, math.ceil(count * 0.6))
        return ["easy"] * easy_count + ["medium"] * (count - easy_count)
    hard_count = count // 2
    medium_count = count - hard_count
    if hard_count == 0:
        return ["medium"] * count
    trailing = 1 if count % 2 == 1 else 0
    leading = medium_count - trailing
    return ["medium"] * leading + ["hard"] * hard_count + ["medium"] * trailing


class AdaptiveAssessmentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def plan(self, mastery: float | None, count: int) -> list[str]:
        return plan_difficulties(
            mastery,
            count,
            easy_below=self.settings.adaptive_easy_below,
            hard_at=self.settings.adaptive_hard_at,
        )
