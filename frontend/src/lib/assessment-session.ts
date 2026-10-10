import type { AssessmentResult } from "@/types/learning";

const STORAGE_KEY = "learnai.latestAssessmentResult";

export type ReviewAnswer = {
  question_id: string;
  question_text: string;
  selected_option: string;
  option_text: string;
};

export type StoredAssessmentReview = {
  result: AssessmentResult;
  title: string;
  topic: string;
  answers: ReviewAnswer[];
};

function isResult(value: unknown): value is AssessmentResult {
  if (!value || typeof value !== "object") {
    return false;
  }
  const result = value as AssessmentResult;
  return (
    typeof result.attempt_id === "string" &&
    typeof result.score === "number" &&
    typeof result.total_questions === "number" &&
    typeof result.percentage === "number" &&
    Array.isArray(result.topic_results) &&
    Array.isArray(result.learning_gaps)
  );
}

export function saveAssessmentReview(review: StoredAssessmentReview): void {
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(review));
}

export function readAssessmentReview(): StoredAssessmentReview | null {
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    const review = parsed as StoredAssessmentReview;
    if (!isResult(review.result) || typeof review.title !== "string" || typeof review.topic !== "string") {
      return null;
    }
    if (!Array.isArray(review.answers)) {
      return null;
    }
    return review;
  } catch {
    return null;
  }
}
