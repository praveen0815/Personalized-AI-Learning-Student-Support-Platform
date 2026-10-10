import type { Course } from "@/types/courses";

function documentIds(value: unknown): string[] | null | undefined {
  if (value === undefined || value === null) {
    return null;
  }
  if (!Array.isArray(value)) {
    return undefined;
  }
  const ids: string[] = [];
  for (const item of value) {
    if (typeof item !== "string" || item.trim().length === 0) {
      return undefined;
    }
    ids.push(item);
  }
  return ids;
}

export function parseCourse(value: unknown): Course | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.id !== "string" || record.id.trim().length === 0) {
    return null;
  }
  if (typeof record.title !== "string" || record.title.trim().length === 0) {
    return null;
  }
  if (typeof record.description !== "string") {
    return null;
  }
  const ids = documentIds(record.document_ids);
  if (ids === undefined) {
    return null;
  }
  return {
    id: record.id,
    title: record.title.trim(),
    description: record.description,
    document_ids: ids,
  };
}

export function parseCourseList(value: unknown): Course[] | null {
  if (!value || typeof value !== "object" || !("courses" in value)) {
    return null;
  }
  const courses = (value as { courses: unknown }).courses;
  if (!Array.isArray(courses)) {
    return null;
  }
  const parsed: Course[] = [];
  for (const item of courses) {
    const course = parseCourse(item);
    if (!course) {
      return null;
    }
    parsed.push(course);
  }
  return parsed;
}
