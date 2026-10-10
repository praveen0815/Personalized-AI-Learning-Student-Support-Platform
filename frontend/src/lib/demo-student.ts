const STORAGE_KEY = "learnai.demoStudentId";

export function readStoredStudentId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.localStorage.getItem(STORAGE_KEY)?.trim();
  return value ? value : null;
}

export function rememberStudentId(studentId: string): void {
  window.localStorage.setItem(STORAGE_KEY, studentId);
}
