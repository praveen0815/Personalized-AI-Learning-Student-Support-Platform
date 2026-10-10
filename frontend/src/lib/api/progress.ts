import { apiGet } from "@/lib/api/client";
import type { StudentProgress } from "@/types/learning";

function progressErrorMessage(status: number, detail: string | null): string {
  if (detail) {
    return detail;
  }
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 404) {
    return "This student record could not be found.";
  }
  return "Unable to load learning progress.";
}

export function getStudentProgress(studentId: string): Promise<StudentProgress> {
  return apiGet<StudentProgress>(`/api/v1/students/${studentId}/progress`, progressErrorMessage);
}
