"""Detect and update explainable learning gaps from stored answers.

Rules, using the configured threshold (default 60) and medium floor (default 50):

- mastery >= threshold: no active gap
- medium floor <= mastery < threshold: medium gap
- mastery < medium floor: high gap

These are product rules for the MVP, not a scientific diagnosis.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.assessment_models import LearningGap


def gap_reason(correct_flags: list[bool]) -> str:
    """Describe the latest answers. `correct_flags` is oldest-to-newest, at most four."""
    window = correct_flags[-4:]
    total = len(window)
    incorrect = sum(1 for flag in window if not flag)
    verb = "was" if total == 1 else "were"
    return f"{incorrect} of the last {total} questions {verb} answered incorrectly."


class LearningGapService:
    def __init__(self, settings: Settings) -> None:
        self.threshold = settings.learning_gap_threshold
        self.medium_floor = settings.learning_gap_medium_floor

    def severity_for(self, mastery: float) -> str | None:
        if mastery >= self.threshold:
            return None
        if mastery >= self.medium_floor:
            return "medium"
        return "high"

    def sync(
        self,
        db: Session,
        student_id: uuid.UUID,
        topic: str,
        mastery: float,
        correct_flags: list[bool],
    ) -> LearningGap | None:
        """Update the one active gap for this student and topic. Returns the active gap, if any."""
        active = db.scalar(
            select(LearningGap).where(
                LearningGap.student_id == student_id,
                LearningGap.topic == topic,
                LearningGap.status == "active",
            )
        )
        severity = self.severity_for(mastery)
        reason = gap_reason(correct_flags) if correct_flags else f"Mastery is {mastery}%."
        now = datetime.now(timezone.utc)
        if severity is None:
            if active is not None:
                active.status = "resolved"
                active.mastery_score = mastery
                active.resolved_at = now
            return None
        if active is None:
            active = LearningGap(
                student_id=student_id,
                topic=topic,
                mastery_score=mastery,
                reason=reason,
                severity=severity,
                status="active",
                detected_at=now,
            )
            db.add(active)
            return active
        active.mastery_score = mastery
        active.severity = severity
        active.reason = reason
        return active
