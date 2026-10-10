"use client";

import { useCallback, useEffect, useState } from "react";
import { BookOpen, Library } from "lucide-react";
import { LearningDocumentList } from "@/components/courses/LearningDocumentList";
import { PageTitle } from "@/components/layout/PageTitle";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { getCourse } from "@/lib/api/courses";
import { listDocuments } from "@/lib/api/knowledge";
import { resourcesForCourse, type CourseResources } from "@/lib/courses/resources";
import type { Course } from "@/types/courses";

type CourseStatus = "loading" | "error" | "ready";
type ResourceStatus = "idle" | "loading" | "error" | "ready";

export function CourseDetailScreen({ courseId }: { courseId: string }) {
  const [courseStatus, setCourseStatus] = useState<CourseStatus>("loading");
  const [courseMessage, setCourseMessage] = useState("Unable to load this course.");
  const [course, setCourse] = useState<Course | null>(null);
  const [resourceStatus, setResourceStatus] = useState<ResourceStatus>("idle");
  const [resourceMessage, setResourceMessage] = useState("Unable to load learning materials.");
  const [resources, setResources] = useState<CourseResources | null>(null);

  const loadCourse = useCallback(async () => {
    const id = courseId.trim();
    if (!id) {
      setCourse(null);
      setCourseMessage("This course is not available from the learning API.");
      setCourseStatus("error");
      return;
    }
    setCourseStatus("loading");
    setResources(null);
    setResourceStatus("idle");
    try {
      const next = await getCourse(id);
      setCourse(next);
      setCourseStatus("ready");
    } catch (error) {
      setCourse(null);
      setCourseMessage(error instanceof ApiError ? error.message : "Unable to load this course.");
      setCourseStatus("error");
    }
  }, [courseId]);

  const loadResources = useCallback(async (next: Course) => {
    if (next.document_ids === null) {
      setResources(resourcesForCourse(next, []));
      setResourceStatus("ready");
      return;
    }
    setResourceStatus("loading");
    try {
      const response = await listDocuments();
      if (!response || !Array.isArray(response.documents)) {
        setResources(null);
        setResourceMessage("The learning API returned an unexpected document list.");
        setResourceStatus("error");
        return;
      }
      setResources(resourcesForCourse(next, response.documents));
      setResourceStatus("ready");
    } catch {
      setResources(null);
      setResourceMessage("Unable to load learning materials.");
      setResourceStatus("error");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadCourse();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadCourse]);

  useEffect(() => {
    if (!course) {
      return;
    }
    const timer = window.setTimeout(() => {
      void loadResources(course);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [course, loadResources]);

  return (
    <div className="mx-auto w-full max-w-5xl space-y-5">
      <PageTitle title={course?.title ?? "Course"} />
      <ButtonLink href="/courses" variant="ghost">
        All courses
      </ButtonLink>
      <Card>
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-indigo-700" aria-hidden="true" />
          <h2 className="text-page-title text-slate-900">{course?.title ?? "Course"}</h2>
        </div>
        {courseStatus === "loading" ? <Skeleton className="mt-3 h-16" /> : null}
        {courseStatus === "error" ? <ErrorState message={courseMessage} onRetry={() => void loadCourse()} /> : null}
        {courseStatus === "ready" && course?.description ? (
          <p className="mt-2 text-secondary text-slate-600">{course.description}</p>
        ) : null}
      </Card>

      {courseStatus === "ready" && course ? (
        <Card>
          <div className="flex items-center gap-2">
            <Library className="h-4 w-4 text-indigo-700" aria-hidden="true" />
            <h3 className="text-section text-slate-900">Learning resources</h3>
          </div>
          {resourceStatus === "loading" ? <Skeleton className="mt-3 h-16" /> : null}
          {resourceStatus === "error" ? (
            <ErrorState message={resourceMessage} onRetry={() => void loadResources(course)} />
          ) : null}
          {resourceStatus === "ready" && resources && !resources.linked ? (
            <EmptyState
              icon={Library}
              title="No document ids on this course."
              message="The course response does not include knowledge-base documents."
            />
          ) : null}
          {resourceStatus === "ready" && resources?.linked && resources.documents.length === 0 && resources.missingIds.length === 0 ? (
            <EmptyState
              icon={Library}
              title="No learning resources on this course."
              message="The course response included an empty document list."
            />
          ) : null}
          {resourceStatus === "ready" && resources && resources.documents.length > 0 ? (
            <LearningDocumentList documents={resources.documents} />
          ) : null}
          {resourceStatus === "ready" && resources && resources.missingIds.length > 0 ? (
            <ul className="mt-3 space-y-1">
              {resources.missingIds.map((id) => (
                <li key={id} className="break-all font-mono text-meta text-slate-500">
                  {id} is not in the knowledge base.
                </li>
              ))}
            </ul>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
