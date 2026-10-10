import { apiPost } from "@/lib/api/client";
import type { TutorReply } from "@/types/learning";

function tutorErrorMessage(status: number, detail: string | null): string {
  if (detail) {
    return detail;
  }
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 422) {
    return "The question was rejected. Enter a non-empty question.";
  }
  if (status === 503) {
    return "The tutor is not available. Check the learning API configuration.";
  }
  if (status === 502 || status === 504) {
    return "The tutor could not complete an answer.";
  }
  return "The tutor could not answer this question.";
}

export function askTutor(question: string, topK = 5): Promise<TutorReply> {
  return apiPost<TutorReply>("/api/v1/tutor/chat", { question, top_k: topK }, tutorErrorMessage);
}
