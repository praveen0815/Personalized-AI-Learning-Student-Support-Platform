export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configured && configured.length > 0 ? configured.replace(/\/$/, "") : "http://127.0.0.1:8000";
}

/** Development-only student id. Authentication is not part of this phase. */
export function getDemoStudentId(): string | null {
  const configured = process.env.NEXT_PUBLIC_DEMO_STUDENT_ID?.trim();
  return configured && configured.length > 0 ? configured : null;
}
