import { apiGet } from "@/lib/api/client";
import type { StudentLearningGaps } from "@/types/learning";

function gapsErrorMessage(status: number, detail: string | null): string {
  if (detail) {
    return detail;
  }
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 404) {
    return "This student record could not be found.";
  }
  return "Unable to load learning gaps.";
}

export function getLearningGaps(studentId: string): Promise<StudentLearningGaps> {
  return apiGet<StudentLearningGaps>(`/api/v1/students/${studentId}/learning-gaps`, gapsErrorMessage);
}
