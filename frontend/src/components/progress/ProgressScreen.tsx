"use client";

import { useCallback, useEffect, useState } from "react";
import { PageTitle } from "@/components/layout/PageTitle";
import { StatCard } from "@/components/dashboard/StatCard";
import { TopicMastery } from "@/components/dashboard/TopicMastery";
import { MasteryChart } from "@/components/progress/MasteryChart";
import { ApiError } from "@/lib/api/client";
import { getStudentProgress } from "@/lib/api/progress";
import { readStoredStudentId } from "@/lib/demo-student";
import { getDemoStudentId } from "@/lib/env";
import { averageMastery, questionsAttempted } from "@/lib/mastery";
import type { TopicProgress } from "@/types/learning";

type LoadStatus = "loading" | "unconfigured" | "error" | "ready";

export function ProgressScreen() {
  const envStudentId = getDemoStudentId();
  const [studentId, setStudentId] = useState<string | null>(envStudentId);
  const [status, setStatus] = useState<LoadStatus>(envStudentId ? "loading" : "unconfigured");
  const [message, setMessage] = useState("");
  const [topics, setTopics] = useState<TopicProgress[]>([]);

  const load = useCallback(async (id: string) => {
    setStatus("loading");
    try {
      const response = await getStudentProgress(id);
      setTopics(Array.isArray(response.topics) ? response.topics : []);
      setStatus("ready");
    } catch (error) {
      setTopics([]);
      setStatus("error");
      setMessage(error instanceof ApiError ? error.message : "Unable to load learning progress.");
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

  const mastery = averageMastery(topics);
  const correct = topics.reduce((sum, topic) => sum + topic.questions_correct, 0);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
      <PageTitle title="Progress" />
      <div>
        <h2 className="text-page-title text-slate-900">Progress</h2>
        <p className="mt-1 text-secondary text-slate-500">Topic mastery from the learner record.</p>
        {studentId ? <p className="mt-1 break-all font-mono text-meta text-slate-500">Student {studentId}</p> : null}
      </div>

      {status === "ready" && topics.length > 0 ? (
        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Progress summary">
          <StatCard
            label="Overall mastery"
            value={mastery === null ? "—" : `${mastery}%`}
            supporting="Average of topic scores returned by the API"
          />
          <StatCard label="Topics tracked" value={String(topics.length)} supporting="Topics in the progress response" />
          <StatCard
            label="Questions attempted"
            value={String(questionsAttempted(topics))}
            supporting="Sum of topic attempt counts"
          />
          <StatCard label="Questions correct" value={String(correct)} supporting="Sum of topic correct counts" />
        </section>
      ) : null}

      {status === "ready" && topics.length > 0 ? <MasteryChart topics={topics} /> : null}

      <TopicMastery
        topics={topics}
        status={status}
        message={message}
        onRetry={() => {
          if (studentId) {
            void load(studentId);
          }
        }}
        showPractice
      />
    </div>
  );
}
