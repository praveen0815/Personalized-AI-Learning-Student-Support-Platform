"""Create grounded assessments, score them, and update the learner record."""

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError, DatabaseUnavailableError, LLMAPIError
from app.db.assessment_models import (
    Assessment,
    AssessmentAttempt,
    LearningGap,
    Question,
    QuestionAttempt,
    Student,
    StudentTopicProgress,
)
from app.db.models import Document
from app.services.adaptive_assessment_service import AdaptiveAssessmentService
from app.services.assessment_prompt import ASSESSMENT_SYSTEM_PROMPT, build_generation_message
from app.services.embedding_service import EmbeddingService
from app.services.learner_model import LearnerModel
from app.services.learning_gap_service import LearningGapService
from app.services.llm_service import LLMService
from app.services.question_validation import ValidQuestion, parse_model_payload, validate_question
from app.services.tutor_prompt import NO_CONTEXT_ANSWER
from app.services.vector_search_service import SearchHit, VectorSearchService

CONTEXT_TOP_K = 5


class AssessmentService:
    def __init__(
        self,
        db: Session,
        embeddings: EmbeddingService,
        llm: LLMService,
        settings: Settings,
    ) -> None:
        self.db = db
        self.embeddings = embeddings
        self.llm = llm
        self.settings = settings
        self.learner = LearnerModel(settings.mastery_prior_weight, settings.mastery_current_weight)
        self.gaps = LearningGapService(settings)
        self.adaptive = AdaptiveAssessmentService(settings)

    def create_student(self, name: str) -> Student:
        student = Student(name=name.strip())
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def require_student(self, student_id: uuid.UUID) -> Student:
        student = self.db.get(Student, student_id)
        if student is None:
            raise AppError("Student not found.", status_code=404)
        return student

    def generate(self, student_id: uuid.UUID, topic: str, number_of_questions: int) -> dict:
        self.require_student(student_id)
        difficulties = ["medium"] * number_of_questions
        return self._create_from_difficulties(topic, difficulties)

    def generate_adaptive(self, student_id: uuid.UUID, topic: str, number_of_questions: int) -> dict:
        self.require_student(student_id)
        progress = self._progress_row(student_id, topic)
        mastery = None if progress is None else progress.mastery_score
        plan = self.adaptive.plan(mastery, number_of_questions)
        seen_text = self._seen_question_text(student_id, topic)
        existing = self._topic_questions(topic)
        slots: list[Question | str] = []
        used_ids: set[uuid.UUID] = set()
        for difficulty in plan:
            match = _pick_question(existing, used_ids, difficulty, unseen_only=seen_text)
            if match is None:
                slots.append(difficulty)
            else:
                slots.append(match)
                used_ids.add(match.id)
        missing = [slot for slot in slots if isinstance(slot, str)]
        if missing:
            hits = self._relevant_hits(topic)
            if hits:
                generated = self._generate_questions(topic, missing, hits)
                generated_iter = iter(generated)
                filled: list[Question | tuple[ValidQuestion, SearchHit]] = []
                for slot in slots:
                    if isinstance(slot, str):
                        filled.append(next(generated_iter))
                    else:
                        filled.append(slot)
                slots = filled
            else:
                filled = []
                for slot in slots:
                    if isinstance(slot, Question):
                        filled.append(slot)
                        continue
                    fallback = _pick_question(existing, used_ids, slot, unseen_only=None)
                    if fallback is None:
                        return {"status": "no_context", "message": NO_CONTEXT_ANSWER, "assessment": None}
                    filled.append(fallback)
                    used_ids.add(fallback.id)
                slots = filled
        assessment = self._store_mixed(topic, slots)
        return {"status": "created", "message": None, "assessment": self.public_assessment(assessment.id)}

    def get_public_assessment(self, assessment_id: uuid.UUID) -> dict:
        assessment = self.db.get(Assessment, assessment_id)
        if assessment is None:
            raise AppError("Assessment not found.", status_code=404)
        return self.public_assessment(assessment_id)

    def submit(self, assessment_id: uuid.UUID, student_id: uuid.UUID, answers: list) -> dict:
        self.require_student(student_id)
        assessment = self.db.get(Assessment, assessment_id)
        if assessment is None:
            raise AppError("Assessment not found.", status_code=404)
        questions = list(
            self.db.scalars(select(Question).where(Question.assessment_id == assessment_id).order_by(Question.created_at))
        )
        by_id = {question.id: question for question in questions}
        if len(answers) != len(questions):
            raise AppError("Submit one answer for every question.", status_code=400)
        seen: set[uuid.UUID] = set()
        graded: list[tuple[Question, str, bool]] = []
        for item in answers:
            if item.question_id in seen:
                raise AppError("Duplicate question id.", status_code=400)
            seen.add(item.question_id)
            question = by_id.get(item.question_id)
            if question is None:
                other = self.db.get(Question, item.question_id)
                if other is None:
                    raise AppError("Question not found.", status_code=400)
                raise AppError("Question does not belong to this assessment.", status_code=400)
            letter = item.selected_option.strip().upper()
            if letter not in (question.options or {}):
                raise AppError("Selected option is not valid for this question.", status_code=400)
            graded.append((question, letter, letter == question.correct_answer))
        if seen != set(by_id):
            raise AppError("Submit one answer for every question.", status_code=400)

        try:
            now = datetime.now(timezone.utc)
            correct_count = sum(1 for _question, _letter, ok in graded if ok)
            percentage = round(correct_count / len(graded) * 100, 2)
            attempt = AssessmentAttempt(
                student_id=student_id,
                assessment_id=assessment_id,
                started_at=now,
                completed_at=now,
                score=correct_count,
                total_questions=len(graded),
                percentage=percentage,
            )
            self.db.add(attempt)
            self.db.flush()
            for index, (question, letter, ok) in enumerate(graded):
                self.db.add(
                    QuestionAttempt(
                        attempt_id=attempt.id,
                        question_id=question.id,
                        student_answer=letter,
                        is_correct=ok,
                        created_at=now + timedelta(microseconds=index),
                    )
                )
            self.db.flush()
            topic_results = []
            gap_views = []
            for topic, topic_rows in _group_by_topic(graded).items():
                topic_correct = sum(1 for _question, _letter, ok in topic_rows if ok)
                progress = self._progress_row(student_id, topic)
                previous = None if progress is None else progress.mastery_score
                mastery = self.learner.next_mastery(previous, topic_correct, len(topic_rows))
                if progress is None:
                    progress = StudentTopicProgress(
                        student_id=student_id,
                        topic=topic,
                        mastery_score=mastery,
                        questions_attempted=len(topic_rows),
                        questions_correct=topic_correct,
                        last_assessed_at=now,
                        updated_at=now,
                    )
                    self.db.add(progress)
                else:
                    progress.mastery_score = mastery
                    progress.questions_attempted += len(topic_rows)
                    progress.questions_correct += topic_correct
                    progress.last_assessed_at = now
                    progress.updated_at = now
                flags = self._recent_flags(student_id, topic)
                gap = self.gaps.sync(self.db, student_id, topic, mastery, flags)
                topic_results.append(
                    {
                        "topic": topic,
                        "correct": topic_correct,
                        "attempted": len(topic_rows),
                        "mastery": mastery,
                    }
                )
                if gap is not None:
                    gap_views.append(_gap_view(gap))
            self.db.commit()
            self.db.refresh(attempt)
        except AppError:
            self.db.rollback()
            raise
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseUnavailableError("Database error while saving the assessment attempt.") from exc
        return {
            "attempt_id": attempt.id,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "percentage": attempt.percentage,
            "topic_results": topic_results,
            "learning_gaps": gap_views,
        }

    def list_progress(self, student_id: uuid.UUID) -> list[StudentTopicProgress]:
        self.require_student(student_id)
        return list(
            self.db.scalars(
                select(StudentTopicProgress)
                .where(StudentTopicProgress.student_id == student_id)
                .order_by(StudentTopicProgress.topic)
            )
        )

    def list_active_gaps(self, student_id: uuid.UUID) -> list[LearningGap]:
        self.require_student(student_id)
        return list(
            self.db.scalars(
                select(LearningGap)
                .where(LearningGap.student_id == student_id, LearningGap.status == "active")
                .order_by(LearningGap.detected_at)
            )
        )

    def public_assessment(self, assessment_id: uuid.UUID) -> dict:
        assessment = self.db.get(Assessment, assessment_id)
        if assessment is None:
            raise AppError("Assessment not found.", status_code=404)
        questions = list(
            self.db.scalars(
                select(Question).where(Question.assessment_id == assessment_id).order_by(Question.created_at, Question.id)
            )
        )
        return {
            "id": assessment.id,
            "title": assessment.title,
            "description": assessment.description,
            "topic": assessment.topic,
            "questions": [self._public_question(question) for question in questions],
        }

    def _create_from_difficulties(self, topic: str, difficulties: list[str]) -> dict:
        hits = self._relevant_hits(topic)
        if not hits:
            return {"status": "no_context", "message": NO_CONTEXT_ANSWER, "assessment": None}
        generated = self._generate_questions(topic, difficulties, hits)
        assessment = self._store_mixed(topic, generated)
        return {"status": "created", "message": None, "assessment": self.public_assessment(assessment.id)}

    def _relevant_hits(self, topic: str) -> list[SearchHit]:
        embedding = self.embeddings.embed_query(topic)
        hits = VectorSearchService(self.db, self.settings).search(embedding, CONTEXT_TOP_K)
        return [hit for hit in hits if hit.similarity >= self.settings.tutor_min_similarity]

    def _generate_questions(
        self,
        topic: str,
        difficulties: list[str],
        hits: list[SearchHit],
    ) -> list[tuple[ValidQuestion, SearchHit]]:
        source = hits[0]
        pending = list(difficulties)
        collected: list[ValidQuestion] = []
        attempts = self.settings.assessment_max_generation_attempts
        for _ in range(attempts):
            raw = self.llm.complete(
                ASSESSMENT_SYSTEM_PROMPT,
                build_generation_message(topic, pending, hits),
            )
            try:
                parsed = parse_model_payload(raw)
            except ValueError:
                parsed = []
            valid = [item for item in (validate_question(raw_item) for raw_item in parsed) if item is not None]
            aligned = _align_difficulties(valid, pending)
            if aligned is None:
                continue
            collected.extend(aligned)
            pending = []
            break
        if pending:
            raise LLMAPIError("The language model did not return valid assessment questions.")
        return [(question, source) for question in collected]

    def _store_mixed(
        self,
        topic: str,
        items: list[Question | tuple[ValidQuestion, SearchHit]],
    ) -> Assessment:
        now = datetime.now(timezone.utc)
        assessment = Assessment(
            title=f"{topic} check",
            description="Multiple-choice questions from the uploaded learning material.",
            topic=topic,
            created_at=now,
        )
        try:
            self.db.add(assessment)
            self.db.flush()
            for index, item in enumerate(items):
                created_at = now + timedelta(microseconds=index)
                if isinstance(item, Question):
                    self.db.add(_clone_question(item, assessment.id, topic, created_at))
                    continue
                question, hit = item
                self.db.add(
                    Question(
                        assessment_id=assessment.id,
                        question_text=question.question_text,
                        question_type="mcq",
                        topic=topic,
                        difficulty=question.difficulty,
                        options=question.options,
                        correct_answer=question.correct_answer,
                        explanation=question.explanation,
                        source_document_id=hit.document_id,
                        source_chunk_id=hit.chunk_id,
                        source_page_number=hit.page_number,
                        created_at=created_at,
                    )
                )
            self.db.commit()
            self.db.refresh(assessment)
            return assessment
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseUnavailableError("Database error while saving the assessment.") from exc

    def _public_question(self, question: Question) -> dict:
        document_name = None
        if question.source_document_id is not None:
            document = self.db.get(Document, question.source_document_id)
            if document is not None:
                document_name = document.filename
        return {
            "id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "topic": question.topic,
            "difficulty": question.difficulty,
            "options": question.options,
            "source_document_name": document_name,
            "source_page_number": question.source_page_number,
        }

    def _progress_row(self, student_id: uuid.UUID, topic: str) -> StudentTopicProgress | None:
        return self.db.scalar(
            select(StudentTopicProgress).where(
                StudentTopicProgress.student_id == student_id,
                StudentTopicProgress.topic == topic,
            )
        )

    def _topic_questions(self, topic: str) -> list[Question]:
        return list(
            self.db.scalars(select(Question).where(Question.topic == topic).order_by(Question.created_at, Question.id))
        )

    def _seen_question_text(self, student_id: uuid.UUID, topic: str) -> set[str]:
        rows = self.db.execute(
            select(Question.question_text)
            .join(QuestionAttempt, QuestionAttempt.question_id == Question.id)
            .join(AssessmentAttempt, AssessmentAttempt.id == QuestionAttempt.attempt_id)
            .where(AssessmentAttempt.student_id == student_id, Question.topic == topic)
        ).all()
        return {_normalize_text(row[0]) for row in rows}

    def _recent_flags(self, student_id: uuid.UUID, topic: str) -> list[bool]:
        rows = self.db.execute(
            select(QuestionAttempt.is_correct)
            .join(Question, Question.id == QuestionAttempt.question_id)
            .join(AssessmentAttempt, AssessmentAttempt.id == QuestionAttempt.attempt_id)
            .where(AssessmentAttempt.student_id == student_id, Question.topic == topic)
            .order_by(QuestionAttempt.created_at.desc())
            .limit(4)
        ).all()
        flags = [bool(row[0]) for row in rows]
        flags.reverse()
        return flags


def _align_difficulties(questions: list[ValidQuestion], difficulties: list[str]) -> list[ValidQuestion] | None:
    buckets: dict[str, list[ValidQuestion]] = {name: [] for name in dict.fromkeys(difficulties)}
    for question in questions:
        if question.difficulty in buckets:
            buckets[question.difficulty].append(question)
    needed = Counter(difficulties)
    if any(len(buckets.get(name, [])) < count for name, count in needed.items()):
        return None
    return [buckets[name].pop(0) for name in difficulties]


def _clone_question(source: Question, assessment_id: uuid.UUID, topic: str, created_at: datetime) -> Question:
    return Question(
        assessment_id=assessment_id,
        question_text=source.question_text,
        question_type=source.question_type,
        topic=topic,
        difficulty=source.difficulty,
        options=source.options,
        correct_answer=source.correct_answer,
        explanation=source.explanation,
        source_document_id=source.source_document_id,
        source_chunk_id=source.source_chunk_id,
        source_page_number=source.source_page_number,
        created_at=created_at,
    )


def _group_by_topic(graded: list[tuple[Question, str, bool]]) -> dict[str, list[tuple[Question, str, bool]]]:
    grouped: dict[str, list[tuple[Question, str, bool]]] = {}
    for row in graded:
        grouped.setdefault(row[0].topic, []).append(row)
    return grouped


def _gap_view(gap: LearningGap) -> dict:
    return {
        "topic": gap.topic,
        "mastery": gap.mastery_score,
        "severity": gap.severity,
        "reason": gap.reason,
        "status": gap.status,
        "detected_at": gap.detected_at,
    }


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def _pick_question(
    existing: list[Question],
    used_ids: set[uuid.UUID],
    difficulty: str,
    *,
    unseen_only: set[str] | None,
) -> Question | None:
    for question in existing:
        if question.id in used_ids or question.difficulty != difficulty:
            continue
        if unseen_only is not None and _normalize_text(question.question_text) in unseen_only:
            continue
        return question
    return None
