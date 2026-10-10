import { apiGet, apiPost } from "@/lib/api/client";
import type { Assessment, AssessmentGeneration, AssessmentResult } from "@/types/learning";

function assessmentErrorMessage(status: number, detail: string | null): string {
  if (detail) {
    return detail;
  }
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 404) {
    return "This assessment or student record could not be found.";
  }
  if (status === 422) {
    return "The assessment request was rejected.";
  }
  if (status === 503) {
    return "The assessment service is not available. Check the learning API configuration.";
  }
  if (status === 502 || status === 504) {
    return "The assessment could not be completed.";
  }
  return "The assessment could not be completed.";
}

export function generateAssessment(studentId: string, topic: string, numberOfQuestions = 5) {
  return apiPost<AssessmentGeneration>(
    "/api/v1/assessments/generate",
    {
      student_id: studentId,
      topic,
      number_of_questions: numberOfQuestions,
    },
    assessmentErrorMessage,
  );
}

export function generateAdaptiveAssessment(studentId: string, topic: string, numberOfQuestions = 5) {
  return apiPost<AssessmentGeneration>(
    "/api/v1/assessments/adaptive",
    {
      student_id: studentId,
      topic,
      number_of_questions: numberOfQuestions,
    },
    assessmentErrorMessage,
  );
}

export function getAssessment(assessmentId: string) {
  return apiGet<Assessment>(`/api/v1/assessments/${assessmentId}`, assessmentErrorMessage);
}

export function submitAssessment(
  assessmentId: string,
  studentId: string,
  answers: { question_id: string; selected_option: string }[],
) {
  return apiPost<AssessmentResult>(
    `/api/v1/assessments/${assessmentId}/submit`,
    {
      student_id: studentId,
      answers,
    },
    assessmentErrorMessage,
  );
}
