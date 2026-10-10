import { ApiError, apiGet, apiPost } from "@/lib/api/client";
import { parseCourse, parseCourseList } from "@/lib/courses/parse";
import type { Course, CourseDraft } from "@/types/courses";

function listError(status: number, detail: string | null): string {
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 404) {
    return "The learning API does not provide a course list.";
  }
  if (detail) {
    return detail;
  }
  return "Unable to load courses.";
}

function courseError(status: number, detail: string | null): string {
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 404) {
    return "This course is not available from the learning API.";
  }
  if (detail) {
    return detail;
  }
  return "Unable to load this course.";
}

function createError(status: number, detail: string | null): string {
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 404 || status === 405) {
    return "Course creation is not available on the learning API.";
  }
  if (status === 422) {
    return detail ?? "The learning API rejected this course.";
  }
  if (detail) {
    return detail;
  }
  return "The course could not be created.";
}

export async function listCourses(): Promise<Course[]> {
  const body = await apiGet<unknown>("/api/v1/courses", listError);
  const courses = parseCourseList(body);
  if (!courses) {
    throw new ApiError("The learning API returned an unexpected course list.", 200);
  }
  return courses;
}

export async function getCourse(courseId: string): Promise<Course> {
  const body = await apiGet<unknown>(`/api/v1/courses/${encodeURIComponent(courseId)}`, courseError);
  const course = parseCourse(body);
  if (!course) {
    throw new ApiError("The learning API returned an unexpected course.", 200);
  }
  return course;
}

export async function createCourse(draft: CourseDraft): Promise<Course> {
  const body = await apiPost<unknown>("/api/v1/courses", draft, createError);
  const course = parseCourse(body);
  if (!course) {
    throw new ApiError("The learning API returned an unexpected course.", 200);
  }
  return course;
}
