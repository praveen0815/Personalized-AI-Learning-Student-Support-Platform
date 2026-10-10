"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { LearningGapCard } from "@/components/dashboard/LearningGapCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { getLearningGaps } from "@/lib/api/learning-gaps";
import { readStoredStudentId } from "@/lib/demo-student";
import { getDemoStudentId } from "@/lib/env";
import type { LearningGap } from "@/types/learning";

type LoadStatus = "loading" | "unconfigured" | "error" | "ready";

function orderGaps(gaps: LearningGap[]): LearningGap[] {
  return [...gaps].sort((left, right) => {
    if (left.severity === right.severity) {
      return left.mastery - right.mastery;
    }
    return left.severity === "high" ? -1 : 1;
  });
}

export function LearningGapsScreen() {
  const envStudentId = getDemoStudentId();
  const [studentId, setStudentId] = useState<string | null>(envStudentId);
  const [status, setStatus] = useState<LoadStatus>(envStudentId ? "loading" : "unconfigured");
  const [message, setMessage] = useState("");
  const [gaps, setGaps] = useState<LearningGap[]>([]);

  const load = useCallback(async (id: string) => {
    setStatus("loading");
    try {
      const response = await getLearningGaps(id);
      setGaps(orderGaps(Array.isArray(response.learning_gaps) ? response.learning_gaps : []));
      setStatus("ready");
    } catch (error) {
      setGaps([]);
      setStatus("error");
      setMessage(error instanceof ApiError ? error.message : "Unable to load learning gaps.");
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
      void load(studentId);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [studentId, load]);

  const high = gaps.filter((gap) => gap.severity === "high").length;
  const medium = gaps.filter((gap) => gap.severity === "medium").length;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
      <PageTitle title="Learning Gaps" />
      <div>
        <h2 className="text-page-title text-slate-900">Learning Gaps</h2>
        <p className="mt-1 text-secondary text-slate-500">Active gaps returned by the learner record.</p>
        {studentId ? <p className="mt-1 break-all font-mono text-meta text-slate-500">Student {studentId}</p> : null}
      </div>

      {status === "loading" ? <Skeleton className="h-24" /> : null}
      {status === "error" ? (
        <ErrorState
          message={message}
          onRetry={() => {
            if (studentId) {
              void load(studentId);
            }
          }}
        />
      ) : null}
      {status === "unconfigured" ? (
        <div className="rounded-lg border border-slate-200 bg-white px-4">
          <EmptyState
            icon={AlertTriangle}
            title="No learning gaps to show."
            message="Connect a student record to see topics that need attention."
          />
        </div>
      ) : null}
      {status === "ready" && gaps.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white px-4">
          <EmptyState icon={CheckCircle2} title="You're on track." message="No active learning gaps were detected." />
        </div>
      ) : null}
      {status === "ready" && gaps.length > 0 ? (
        <>
          <p className="font-mono text-meta text-slate-500">
            {gaps.length} active · {high} high · {medium} medium
          </p>
          <div className="space-y-3">
            {gaps.map((gap) => (
              <LearningGapCard
                key={`${gap.topic}-${gap.detected_at}`}
                gap={gap}
                practiceHref={`/assessments?topic=${encodeURIComponent(gap.topic)}`}
                practiceLabel="Practice"
              />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
