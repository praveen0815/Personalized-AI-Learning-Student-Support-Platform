"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getLearningGaps } from "@/lib/api/learning-gaps";
import { getStudentProgress } from "@/lib/api/progress";
import { createStudent } from "@/lib/api/students";
import { brand } from "@/lib/brand";
import { readStoredStudentId, rememberStudentId } from "@/lib/demo-student";
import { getDemoStudentId } from "@/lib/env";
import type { LearningGap, TopicProgress } from "@/types/learning";

export type SectionState<T> =
  | { status: "loading" }
  | { status: "unconfigured" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };

function sectionError(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.status === 404) {
    return "This student record could not be found.";
  }
  return fallback;
}

export function useDashboardData() {
  const envStudentId = getDemoStudentId();
  const [studentId, setStudentId] = useState<string | null>(envStudentId);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [progress, setProgress] = useState<SectionState<TopicProgress[]>>(
    envStudentId ? { status: "loading" } : { status: "unconfigured" },
  );
  const [gaps, setGaps] = useState<SectionState<LearningGap[]>>(
    envStudentId ? { status: "loading" } : { status: "unconfigured" },
  );

  const loadProgress = useCallback(async (id: string) => {
    setProgress({ status: "loading" });
    try {
      const response = await getStudentProgress(id);
      setProgress({ status: "ready", data: response.topics });
    } catch (error) {
      setProgress({ status: "error", message: sectionError(error, "Unable to load learning progress.") });
    }
  }, []);

  const loadGaps = useCallback(async (id: string) => {
    setGaps({ status: "loading" });
    try {
      const response = await getLearningGaps(id);
      setGaps({ status: "ready", data: response.learning_gaps });
    } catch (error) {
      setGaps({ status: "error", message: sectionError(error, "Unable to load learning gaps.") });
    }
  }, []);

  useEffect(() => {
    if (envStudentId) {
      return;
    }
    const stored = readStoredStudentId();
    const timer = window.setTimeout(() => {
      if (stored) {
        setStudentId(stored);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [envStudentId]);

  useEffect(() => {
    if (!studentId) {
      return;
    }
    const timer = window.setTimeout(() => {
      void loadProgress(studentId);
      void loadGaps(studentId);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [studentId, loadProgress, loadGaps]);

  const createDevelopmentStudent = useCallback(async () => {
    if (envStudentId || studentId || creating) {
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const student = await createStudent(brand.studentLabel);
      rememberStudentId(student.id);
      setStudentId(student.id);
    } catch {
      setCreateError("Unable to create the development student.");
    } finally {
      setCreating(false);
    }
  }, [creating, envStudentId, studentId]);

  return {
    studentId,
    envStudentId,
    creating,
    createError,
    progress,
    gaps,
    reloadProgress: () => {
      if (studentId) {
        void loadProgress(studentId);
      }
    },
    reloadGaps: () => {
      if (studentId) {
        void loadGaps(studentId);
      }
    },
    createDevelopmentStudent,
  };
}
