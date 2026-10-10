"use client";

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { BookOpen, Library } from "lucide-react";
import { LearningDocumentList } from "@/components/courses/LearningDocumentList";
import { PageTitle } from "@/components/layout/PageTitle";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { createCourse, listCourses } from "@/lib/api/courses";
import { listDocuments } from "@/lib/api/knowledge";
import { validateCourseDraft } from "@/lib/courses/draft";
import type { Course } from "@/types/courses";
import type { KnowledgeDocument } from "@/types/learning";

const fieldClass =
  "mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-body text-slate-900 focus-visible:border-indigo-600 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 disabled:opacity-60";

type CourseStatus = "loading" | "unavailable" | "error" | "empty" | "ready";
type ResourceStatus = "loading" | "error" | "empty" | "ready";

export function CoursesScreen() {
  const [courseStatus, setCourseStatus] = useState<CourseStatus>("loading");
  const [courseMessage, setCourseMessage] = useState("Unable to load courses.");
  const [courses, setCourses] = useState<Course[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [formErrors, setFormErrors] = useState<string[]>([]);
  const [createStatus, setCreateStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [createMessage, setCreateMessage] = useState("");
  const [created, setCreated] = useState<Course | null>(null);
  const [resourceStatus, setResourceStatus] = useState<ResourceStatus>("loading");
  const [resourceMessage, setResourceMessage] = useState("Unable to load learning materials.");
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);

  const loadCourses = useCallback(async () => {
    setCourseStatus("loading");
    setCourseMessage("");
    try {
      const next = await listCourses();
      setCourses(next);
      setCourseStatus(next.length === 0 ? "empty" : "ready");
    } catch (error) {
      setCourses([]);
      if (error instanceof ApiError && error.status === 404) {
        setCourseMessage(error.message);
        setCourseStatus("unavailable");
        return;
      }
      setCourseMessage(error instanceof ApiError ? error.message : "Unable to load courses.");
      setCourseStatus("error");
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setResourceStatus("loading");
    try {
      const response = await listDocuments();
      if (!response || !Array.isArray(response.documents)) {
        setDocuments([]);
        setResourceMessage("The learning API returned an unexpected document list.");
        setResourceStatus("error");
        return;
      }
      setDocuments(response.documents);
      setResourceStatus(response.documents.length === 0 ? "empty" : "ready");
    } catch {
      setDocuments([]);
      setResourceMessage("Unable to load learning materials.");
      setResourceStatus("error");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadCourses();
      void loadDocuments();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadCourses, loadDocuments]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (createStatus === "submitting") {
      return;
    }
    const validated = validateCourseDraft(title, description);
    if (!validated.ok) {
      setFormErrors(validated.errors);
      setCreateStatus("idle");
      setCreateMessage("");
      setCreated(null);
      return;
    }
    setFormErrors([]);
    setCreateStatus("submitting");
    setCreateMessage("");
    setCreated(null);
    try {
      const course = await createCourse(validated.draft);
      setCreated(course);
      setCreateStatus("success");
      setCreateMessage("Course created.");
      setTitle("");
      setDescription("");
    } catch (error) {
      setCreateStatus("error");
      setCreateMessage(error instanceof ApiError ? error.message : "The course could not be created.");
      return;
    }
    await loadCourses();
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-5">
      <PageTitle title="My Courses" />
      <div>
        <h2 className="text-page-title text-slate-900">My Courses</h2>
        <p className="mt-1 max-w-2xl text-secondary text-slate-500">
          Courses come from the learning API. Knowledge-base documents stay in their own list until a course response includes their ids.
        </p>
      </div>

      <Card>
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-indigo-700" aria-hidden="true" />
          <h3 className="text-section text-slate-900">Courses</h3>
        </div>
        {courseStatus === "loading" ? <Skeleton className="mt-3 h-16" /> : null}
        {courseStatus === "error" ? <ErrorState message={courseMessage} onRetry={() => void loadCourses()} /> : null}
        {courseStatus === "unavailable" ? (
          <EmptyState icon={BookOpen} title="No course list is available." message={courseMessage} />
        ) : null}
        {courseStatus === "empty" ? (
          <EmptyState
            icon={BookOpen}
            title="No courses yet."
            message="The learning API returned an empty course list."
          />
        ) : null}
        {courseStatus === "ready" ? (
          <ul className="mt-3 divide-y divide-slate-100">
            {courses.map((course) => (
              <li key={course.id} className="flex items-start justify-between gap-3 py-2">
                <div>
                  <p className="text-body font-medium text-slate-900">{course.title}</p>
                  {course.description ? <p className="mt-1 text-secondary text-slate-600">{course.description}</p> : null}
                </div>
                <ButtonLink href={`/courses/${encodeURIComponent(course.id)}`} variant="secondary">
                  Open
                </ButtonLink>
              </li>
            ))}
          </ul>
        ) : null}

        <form className="mt-4 border-t border-slate-100 pt-4" onSubmit={onCreate}>
          <h4 className="text-card-title text-slate-900">Create a course</h4>
          <p className="mt-1 text-secondary text-slate-500">
            Title and description are sent to the course API. This page does not store a course on its own.
          </p>
          <div className="mt-3 space-y-3">
            <div>
              <label htmlFor="course-title" className="text-label uppercase text-slate-500">
                Title
              </label>
              <input
                id="course-title"
                className={`${fieldClass} h-9`}
                value={title}
                maxLength={200}
                disabled={createStatus === "submitting"}
                onChange={(event) => setTitle(event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="course-description" className="text-label uppercase text-slate-500">
                Description
              </label>
              <textarea
                id="course-description"
                className={`${fieldClass} min-h-20 py-2`}
                value={description}
                maxLength={2000}
                disabled={createStatus === "submitting"}
                onChange={(event) => setDescription(event.target.value)}
              />
            </div>
          </div>
          {formErrors.length > 0 ? (
            <ul className="mt-3 space-y-1" role="alert">
              {formErrors.map((error) => (
                <li key={error} className="text-secondary text-rose-700">
                  {error}
                </li>
              ))}
            </ul>
          ) : null}
          {createStatus === "error" ? (
            <p className="mt-3 text-secondary text-rose-700" role="alert">
              {createMessage}
            </p>
          ) : null}
          {createStatus === "success" && created ? (
            <p className="mt-3 text-secondary text-slate-700" role="status">
              {createMessage} {created.title}
            </p>
          ) : null}
          <Button className="mt-3" type="submit" disabled={createStatus === "submitting"}>
            {createStatus === "submitting" ? "Creating" : "Create course"}
          </Button>
        </form>
      </Card>

      <Card>
        <div className="flex items-center gap-2">
          <Library className="h-4 w-4 text-indigo-700" aria-hidden="true" />
          <h3 className="text-section text-slate-900">Learning resources</h3>
        </div>
        <p className="mt-2 text-secondary text-slate-500">
          Documents already stored in the knowledge base. Uploads stay on the knowledge base page.
        </p>
        {resourceStatus === "loading" ? <Skeleton className="mt-3 h-16" /> : null}
        {resourceStatus === "error" ? (
          <ErrorState message={resourceMessage} onRetry={() => void loadDocuments()} />
        ) : null}
        {resourceStatus === "empty" ? (
          <EmptyState
            icon={Library}
            title="No learning materials available yet."
            message="Upload a PDF in the knowledge base to add a resource."
          />
        ) : null}
        {resourceStatus === "ready" ? <LearningDocumentList documents={documents} /> : null}
        <ButtonLink className="mt-3" href="/knowledge" variant="secondary">
          Open knowledge base
        </ButtonLink>
      </Card>
    </div>
  );
}
