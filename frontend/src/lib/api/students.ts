import { apiPost } from "@/lib/api/client";
import type { Student } from "@/types/learning";

export function createStudent(name: string): Promise<Student> {
  return apiPost<Student>("/api/v1/students", { name });
}
