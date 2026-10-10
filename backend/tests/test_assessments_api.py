"""Assessment, mastery, gap, and adaptive API tests. The language model is stubbed."""

import json
import re
import uuid
from datetime import datetime, timezone

from app.api.deps import get_embedding_service, get_llm_service
from app.db.assessment_models import (
    Assessment,
    AssessmentAttempt,
    LearningGap,
    Question,
    QuestionAttempt,
    StudentTopicProgress,
)
from app.db.database import SessionLocal
from app.db.models import Document
from app.main import app
from app.services.assessment_prompt import ASSESSMENT_SYSTEM_PROMPT
from app.services.learning_gap_service import LearningGapService
from app.services.tutor_prompt import NO_CONTEXT_ANSWER
from app.services.vector_search_service import SearchHit, VectorSearchService
from app.core.config import get_settings
from tests.conftest import StubEmbeddings

DOCUMENT_ID = uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
CHUNK_ID = uuid.UUID("8c2d1b4e-5f7a-4c1d-9e2b-1a2b3c4d5e6f")
CHUNK_TEXT = "Bayes theorem updates a prior when evidence arrives."
TOPIC = "Bayes Theorem"


class RecordingLLM:
    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = list(responses or [])
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_message: str) -> str:
        self.calls.append((system_prompt, user_message))
        if self.responses:
            return self.responses.pop(0)
        return _questions_json(_difficulties_from(user_message), len(self.calls))


def _difficulties_from(user_message: str) -> list[str]:
    match = re.search(r"Use these difficulties in order: (.+)\.", user_message)
    assert match is not None
    return [part.strip() for part in match.group(1).split(",")]


def _questions_json(difficulties: list[str], batch: int, **overrides) -> str:
    questions = []
    for index, difficulty in enumerate(difficulties):
        item = {
            "question": f"Batch {batch} item {index}: what does Bayes theorem update?",
            "options": {
                "A": f"A prior {batch}-{index}",
                "B": f"A page {batch}-{index}",
                "C": f"A file {batch}-{index}",
                "D": f"A key {batch}-{index}",
            },
            "correct_answer": "A",
            "explanation": "The notes say a prior is updated.",
            "difficulty": difficulty,
        }
        item.update(overrides)
        questions.append(item)
    return json.dumps({"questions": questions})


def _hit(**overrides) -> SearchHit:
    values = {
        "document_id": DOCUMENT_ID,
        "document_name": "Probability Notes.pdf",
        "chunk_id": CHUNK_ID,
        "page_number": 1,
        "chunk_index": 0,
        "content": CHUNK_TEXT,
        "similarity": 0.92,
    }
    values.update(overrides)
    return SearchHit(**values)


def _patch_search(monkeypatch, hits: list[SearchHit]) -> None:
    def search(self, query_embedding, top_k):  # noqa: ANN001
        assert query_embedding
        assert top_k >= 1
        return hits

    monkeypatch.setattr(VectorSearchService, "search", search)


def _use_llm(llm: RecordingLLM) -> None:
    app.dependency_overrides[get_embedding_service] = lambda: StubEmbeddings()
    app.dependency_overrides[get_llm_service] = lambda: llm


def _seed_document() -> None:
    with SessionLocal() as db:
        db.add(
            Document(
                id=DOCUMENT_ID,
                filename="Probability Notes.pdf",
                title="Probability Notes",
                file_type="pdf",
                file_path="unused",
                total_pages=1,
                total_chunks=1,
                processing_status="completed",
            )
        )
        db.commit()


def _create_student(client, name: str = "Asha") -> str:
    response = client.post("/api/v1/students", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def _generate(client, student_id: str, count: int = 5, topic: str = TOPIC) -> dict:
    response = client.post(
        "/api/v1/assessments/generate",
        json={"student_id": student_id, "topic": topic, "number_of_questions": count},
    )
    assert response.status_code == 200
    return response.json()


def _keys(value) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        found.update(value)
        for item in value.values():
            found.update(_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_keys(item))
    return found


def _set_mastery(student_id: str, mastery: float, topic: str = TOPIC) -> None:
    with SessionLocal() as db:
        db.add(
            StudentTopicProgress(
                student_id=uuid.UUID(student_id),
                topic=topic,
                mastery_score=mastery,
                questions_attempted=4,
                questions_correct=2,
                last_assessed_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()


def test_generation_uses_retrieved_context_and_hides_the_answer(client, monkeypatch):
    llm = RecordingLLM()
    _use_llm(llm)
    _patch_search(monkeypatch, [_hit()])
    _seed_document()
    student_id = _create_student(client)

    body = _generate(client, student_id, 2)

    assert body["status"] == "created"
    assessment = body["assessment"]
    assert assessment["topic"] == TOPIC
    assert len(assessment["questions"]) == 2
    assert {item["difficulty"] for item in assessment["questions"]} == {"medium"}
    assert assessment["questions"][0]["source_document_name"] == "Probability Notes.pdf"
    assert assessment["questions"][0]["source_page_number"] == 1
    assert "correct_answer" not in _keys(body)
    assert "explanation" not in _keys(body)
    assert len(llm.calls) == 1
    system_prompt, user_message = llm.calls[0]
    assert system_prompt == ASSESSMENT_SYSTEM_PROMPT
    assert CHUNK_TEXT in user_message
    assert "Page:" not in user_message
    with SessionLocal() as db:
        stored = db.query(Question).filter(Question.assessment_id == uuid.UUID(assessment["id"])).all()
        assert {row.correct_answer for row in stored} == {"A"}
        assert {row.source_chunk_id for row in stored} == {CHUNK_ID}
        assert {row.source_document_id for row in stored} == {DOCUMENT_ID}


def test_no_relevant_context_does_not_call_the_model(client, monkeypatch):
    llm = RecordingLLM()
    _use_llm(llm)
    _patch_search(monkeypatch, [_hit(similarity=0.2)])
    student_id = _create_student(client)

    response = client.post(
        "/api/v1/assessments/generate",
        json={"student_id": student_id, "topic": TOPIC, "number_of_questions": 2},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_context"
    assert response.json()["message"] == NO_CONTEXT_ANSWER
    assert response.json()["assessment"] is None
    assert llm.calls == []
    with SessionLocal() as db:
        assert db.query(Assessment).count() == 0


def test_invalid_model_output_is_rejected(client, monkeypatch):
    cases = [
        "not json",
        _questions_json(["medium"], 1, options={"A": "only", "B": "two", "C": "three"}),
        _questions_json(["extreme"], 1),
        _questions_json(["medium"], 1, correct_answer="E"),
    ]
    student_id = _create_student(client)
    _patch_search(monkeypatch, [_hit()])
    for raw in cases:
        llm = RecordingLLM([raw, raw])
        _use_llm(llm)
        response = client.post(
            "/api/v1/assessments/generate",
            json={"student_id": student_id, "topic": TOPIC, "number_of_questions": 1},
        )
        assert response.status_code == 502
        assert len(llm.calls) == 2
    with SessionLocal() as db:
        assert db.query(Assessment).count() == 0


def test_a_later_valid_response_is_accepted_within_the_retry_limit(client, monkeypatch):
    llm = RecordingLLM(["not json"])
    _use_llm(llm)
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)

    body = _generate(client, student_id, 1)

    assert body["status"] == "created"
    assert len(llm.calls) == 2


def test_invalid_generation_requests_are_rejected(client):
    student_id = _create_student(client)
    for payload in (
        {"student_id": student_id, "topic": "  ", "number_of_questions": 1},
        {"student_id": student_id, "topic": TOPIC, "number_of_questions": 0},
        {"student_id": student_id, "topic": TOPIC, "number_of_questions": 11},
    ):
        response = client.post("/api/v1/assessments/generate", json=payload)
        assert response.status_code == 422


def test_unknown_student_cannot_generate(client):
    response = client.post(
        "/api/v1/assessments/generate",
        json={"student_id": str(uuid.uuid4()), "topic": TOPIC, "number_of_questions": 1},
    )
    assert response.status_code == 404


def test_get_assessment_hides_answers_and_missing_assessment_is_404(client, monkeypatch):
    llm = RecordingLLM()
    _use_llm(llm)
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)
    created = _generate(client, student_id, 1)
    assessment_id = created["assessment"]["id"]

    fetched = client.get(f"/api/v1/assessments/{assessment_id}")
    assert fetched.status_code == 200
    assert "correct_answer" not in _keys(fetched.json())
    assert fetched.json()["questions"][0]["question_text"]

    missing = client.get(f"/api/v1/assessments/{uuid.uuid4()}")
    assert missing.status_code == 404


def test_valid_submission_updates_mastery_without_a_gap(client, monkeypatch):
    _use_llm(RecordingLLM())
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)
    created = _generate(client, student_id, 5)
    questions = created["assessment"]["questions"]
    answers = [{"question_id": questions[0]["id"], "selected_option": "B"}]
    answers.extend({"question_id": item["id"], "selected_option": "A"} for item in questions[1:])

    response = client.post(
        f"/api/v1/assessments/{created['assessment']['id']}/submit",
        json={"student_id": student_id, "answers": answers},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 4
    assert body["total_questions"] == 5
    assert body["percentage"] == 80
    assert body["topic_results"] == [{"topic": TOPIC, "correct": 4, "attempted": 5, "mastery": 80}]
    assert body["learning_gaps"] == []
    progress = client.get(f"/api/v1/students/{student_id}/progress")
    assert progress.json()["topics"] == [
        {"topic": TOPIC, "mastery": 80, "questions_attempted": 5, "questions_correct": 4}
    ]


def test_repeated_assessment_weights_the_previous_mastery(client, monkeypatch):
    _use_llm(RecordingLLM())
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)
    first = _generate(client, student_id, 5)
    _submit_letters(client, student_id, first, ["A", "A", "A", "A", "B"])
    second = _generate(client, student_id, 5)
    body = _submit_letters(client, student_id, second, ["A"] * 5)
    assert body["topic_results"][0]["mastery"] == 86
    progress = client.get(f"/api/v1/students/{student_id}/progress").json()
    assert progress["topics"][0]["questions_attempted"] == 10
    assert progress["topics"][0]["questions_correct"] == 9


def test_learning_gap_bands_and_reason(client, monkeypatch):
    _use_llm(RecordingLLM())
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)

    high = _generate(client, student_id, 5)
    # Last four answers: three wrong, one right. Overall 2/5 = 40.
    high_body = _submit_letters(client, student_id, high, ["A", "B", "B", "B", "A"])
    assert high_body["topic_results"][0]["mastery"] == 40
    assert high_body["learning_gaps"][0]["severity"] == "high"
    assert high_body["learning_gaps"][0]["reason"] == "3 of the last 4 questions were answered incorrectly."

    medium_student = _create_student(client, "Meera")
    medium = _generate(client, medium_student, 2)
    medium_body = _submit_letters(client, medium_student, medium, ["B", "A"])
    assert medium_body["topic_results"][0]["mastery"] == 50
    assert medium_body["learning_gaps"][0]["severity"] == "medium"

    clear_student = _create_student(client, "Ravi")
    clear = _generate(client, clear_student, 5)
    clear_body = _submit_letters(client, clear_student, clear, ["A", "A", "A", "B", "B"])
    assert clear_body["topic_results"][0]["mastery"] == 60
    assert clear_body["learning_gaps"] == []
    listed = client.get(f"/api/v1/students/{clear_student}/learning-gaps")
    assert listed.json()["learning_gaps"] == []


def test_active_gap_is_updated_then_resolved(client, monkeypatch):
    _use_llm(RecordingLLM())
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)
    first = _submit_letters(client, student_id, _generate(client, student_id, 1), ["B"])
    detected_at = first["learning_gaps"][0]["detected_at"].rstrip("Z")
    assert first["topic_results"][0]["mastery"] == 0

    second = _submit_letters(client, student_id, _generate(client, student_id, 1), ["B"])
    assert second["topic_results"][0]["mastery"] == 0
    assert second["learning_gaps"][0]["detected_at"].rstrip("Z") == detected_at
    with SessionLocal() as db:
        assert db.query(LearningGap).filter(LearningGap.status == "active").count() == 1

    # 0 -> 30 -> 51 -> 65.7, which clears the active gap.
    for _ in range(3):
        _submit_letters(client, student_id, _generate(client, student_id, 1), ["A"])
    listed = client.get(f"/api/v1/students/{student_id}/learning-gaps")
    assert listed.json()["learning_gaps"] == []
    with SessionLocal() as db:
        stored = db.query(LearningGap).one()
        assert stored.status == "resolved"
        assert stored.resolved_at is not None


def test_submission_validation(client, monkeypatch):
    _use_llm(RecordingLLM())
    _patch_search(monkeypatch, [_hit()])
    student_id = _create_student(client)
    created = _generate(client, student_id, 2)
    other = _generate(client, student_id, 1)
    assessment_id = created["assessment"]["id"]
    first_id = created["assessment"]["questions"][0]["id"]
    second_id = created["assessment"]["questions"][1]["id"]
    foreign_id = other["assessment"]["questions"][0]["id"]

    def submit(payload, expected: int):
        response = client.post(f"/api/v1/assessments/{assessment_id}/submit", json=payload)
        assert response.status_code == expected
        return response

    submit({"student_id": str(uuid.uuid4()), "answers": [{"question_id": first_id, "selected_option": "A"}]}, 404)
    missing_assessment = client.post(
        f"/api/v1/assessments/{uuid.uuid4()}/submit",
        json={"student_id": student_id, "answers": [{"question_id": first_id, "selected_option": "A"}]},
    )
    assert missing_assessment.status_code == 404
    submit(
        {
            "student_id": student_id,
            "answers": [
                {"question_id": str(uuid.uuid4()), "selected_option": "A"},
                {"question_id": second_id, "selected_option": "A"},
            ],
        },
        400,
    )
    submit(
        {
            "student_id": student_id,
            "answers": [
                {"question_id": foreign_id, "selected_option": "A"},
                {"question_id": second_id, "selected_option": "A"},
            ],
        },
        400,
    )
    duplicate = submit(
        {
            "student_id": student_id,
            "answers": [
                {"question_id": first_id, "selected_option": "A"},
                {"question_id": first_id, "selected_option": "A"},
            ],
        },
        400,
    )
    assert duplicate.json()["detail"] == "Duplicate question id."
    submit(
        {
            "student_id": student_id,
            "answers": [
                {"question_id": first_id, "selected_option": "Z"},
                {"question_id": second_id, "selected_option": "A"},
            ],
        },
        400,
    )
    missing = submit(
        {"student_id": student_id, "answers": [{"question_id": first_id, "selected_option": "A"}]},
        400,
    )
    assert missing.json()["detail"] == "Submit one answer for every question."
    with SessionLocal() as db:
        assert db.query(AssessmentAttempt).count() == 0
        assert db.query(QuestionAttempt).count() == 0


def test_adaptive_prompt_follows_mastery(client, monkeypatch):
    _patch_search(monkeypatch, [_hit()])
    cases = [
        (None, "medium, medium, medium, medium, medium"),
        (35, "easy, easy, easy, medium, medium"),
        (39.99, "easy, easy, easy, medium, medium"),
        (40, "medium, medium, medium, medium, medium"),
        (69.99, "medium, medium, medium, medium, medium"),
        (70, "medium, medium, hard, hard, medium"),
        (82, "medium, medium, hard, hard, medium"),
    ]
    for mastery, expected in cases:
        llm = RecordingLLM()
        _use_llm(llm)
        student_id = _create_student(client, f"Student {mastery}")
        topic = f"Bayes {mastery}"
        if mastery is not None:
            _set_mastery(student_id, mastery, topic)
        response = client.post(
            "/api/v1/assessments/adaptive",
            json={"student_id": student_id, "topic": topic, "number_of_questions": 5},
        )
        assert response.status_code == 200, mastery
        _, user_message = llm.calls[0]
        assert f"Use these difficulties in order: {expected}." in user_message
        difficulties = [item["difficulty"] for item in response.json()["assessment"]["questions"]]
        assert difficulties == [part.strip() for part in expected.split(",")]


def test_adaptive_prefers_unseen_questions_and_reuses_seen_when_context_is_missing(client, monkeypatch):
    student_id = _create_student(client)
    _set_mastery(student_id, 50)
    seen, unseen = _seed_questions(student_id)
    llm = RecordingLLM()
    _use_llm(llm)
    _patch_search(monkeypatch, [_hit()])

    response = client.post(
        "/api/v1/assessments/adaptive",
        json={"student_id": student_id, "topic": TOPIC, "number_of_questions": 1},
    )

    assert response.status_code == 200
    assert response.json()["assessment"]["questions"][0]["question_text"] == "Unseen Bayes question"
    assert llm.calls == []

    _mark_seen(student_id, unseen)
    _patch_search(monkeypatch, [])
    reused = client.post(
        "/api/v1/assessments/adaptive",
        json={"student_id": student_id, "topic": TOPIC, "number_of_questions": 1},
    )
    assert reused.status_code == 200
    assert reused.json()["status"] == "created"
    assert llm.calls == []
    assert reused.json()["assessment"]["questions"][0]["question_text"] in {
        "Seen Bayes question",
        "Unseen Bayes question",
    }
    assert seen is not None


def test_openapi_lists_assessment_routes(client):
    spec = client.get("/openapi.json")
    docs = client.get("/docs")
    assert spec.status_code == 200
    assert docs.status_code == 200
    paths = spec.json()["paths"]
    for path in (
        "/api/v1/assessments/generate",
        "/api/v1/assessments/adaptive",
        "/api/v1/assessments/{assessment_id}",
        "/api/v1/assessments/{assessment_id}/submit",
        "/api/v1/students",
        "/api/v1/students/{student_id}/progress",
        "/api/v1/students/{student_id}/learning-gaps",
    ):
        assert path in paths
    assert spec.json()["info"]["version"] == "0.3.0"


def test_gap_service_does_not_duplicate_an_active_row(client):
    student_id = uuid.uuid4()
    with SessionLocal() as db:
        from app.db.assessment_models import Student

        db.add(Student(id=student_id, name="Gap"))
        db.commit()
        service = LearningGapService(get_settings())
        service.sync(db, student_id, TOPIC, 42, [False, False, False, True])
        db.commit()
        service.sync(db, student_id, TOPIC, 55, [False, True, True, True])
        db.commit()
        active = db.query(LearningGap).filter(LearningGap.status == "active").all()
        assert len(active) == 1
        assert active[0].severity == "medium"
        assert active[0].reason == "1 of the last 4 questions were answered incorrectly."
        service.sync(db, student_id, TOPIC, 70, [True, True, True, True])
        db.commit()
        assert db.query(LearningGap).filter(LearningGap.status == "active").count() == 0


def _submit_letters(client, student_id: str, created: dict, letters: list[str]) -> dict:
    questions = created["assessment"]["questions"]
    answers = [
        {"question_id": question["id"], "selected_option": letter}
        for question, letter in zip(questions, letters, strict=True)
    ]
    response = client.post(
        f"/api/v1/assessments/{created['assessment']['id']}/submit",
        json={"student_id": student_id, "answers": answers},
    )
    assert response.status_code == 200
    return response.json()


def _seed_questions(student_id: str) -> tuple[uuid.UUID, uuid.UUID]:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        assessment = Assessment(title="Seed", description="", topic=TOPIC, created_at=now)
        db.add(assessment)
        db.flush()
        options = {"A": "Prior", "B": "Page", "C": "File", "D": "Key"}
        seen = Question(
            assessment_id=assessment.id,
            question_text="Seen Bayes question",
            question_type="mcq",
            topic=TOPIC,
            difficulty="medium",
            options=options,
            correct_answer="A",
            explanation="Stored explanation.",
            created_at=now,
        )
        unseen = Question(
            assessment_id=assessment.id,
            question_text="Unseen Bayes question",
            question_type="mcq",
            topic=TOPIC,
            difficulty="medium",
            options=options,
            correct_answer="A",
            explanation="Stored explanation.",
            created_at=now,
        )
        db.add_all([seen, unseen])
        db.flush()
        attempt = AssessmentAttempt(
            student_id=uuid.UUID(student_id),
            assessment_id=assessment.id,
            started_at=now,
            completed_at=now,
            score=0,
            total_questions=1,
            percentage=0,
        )
        db.add(attempt)
        db.flush()
        db.add(
            QuestionAttempt(
                attempt_id=attempt.id,
                question_id=seen.id,
                student_answer="B",
                is_correct=False,
                created_at=now,
            )
        )
        db.commit()
        return seen.id, unseen.id


def _mark_seen(student_id: str, question_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        question = db.get(Question, question_id)
        attempt = AssessmentAttempt(
            student_id=uuid.UUID(student_id),
            assessment_id=question.assessment_id,
            started_at=now,
            completed_at=now,
            score=0,
            total_questions=1,
            percentage=0,
        )
        db.add(attempt)
        db.flush()
        db.add(
            QuestionAttempt(
                attempt_id=attempt.id,
                question_id=question_id,
                student_answer="B",
                is_correct=False,
                created_at=now,
            )
        )
        db.commit()
