"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ClipboardCheck } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ApiError } from "@/lib/api/client";
import { generateAdaptiveAssessment, generateAssessment, getAssessment, submitAssessment } from "@/lib/api/assessments";
import { saveAssessmentReview } from "@/lib/assessment-session";
import { readStoredStudentId } from "@/lib/demo-student";
import { getDemoStudentId } from "@/lib/env";
import type { Assessment, AssessmentGeneration, PublicQuestion } from "@/types/learning";

function optionEntries(options: Record<string, string>): [string, string][] {
  return Object.entries(options).sort(([left], [right]) => left.localeCompare(right));
}

function publicQuestion(value: PublicQuestion): PublicQuestion {
  return {
    id: value.id,
    question_text: value.question_text,
    question_type: value.question_type,
    topic: value.topic,
    difficulty: value.difficulty,
    options: value.options && typeof value.options === "object" ? value.options : {},
    source_document_name: value.source_document_name,
    source_page_number: value.source_page_number,
  };
}

function publicAssessment(value: Assessment): Assessment | null {
  if (!value || typeof value.id !== "string" || !Array.isArray(value.questions)) {
    return null;
  }
  return {
    id: value.id,
    title: value.title,
    description: value.description,
    topic: value.topic,
    questions: value.questions.map(publicQuestion),
  };
}

function isGeneration(value: AssessmentGeneration): boolean {
  return value?.status === "created" || value?.status === "no_context";
}

export function AssessmentScreen({
  initialTopic,
  initialMode,
}: {
  initialTopic?: string;
  initialMode?: "adaptive";
}) {
  const router = useRouter();
  const [studentId, setStudentId] = useState<string | null>(getDemoStudentId());
  const [topic, setTopic] = useState(initialTopic ?? "");
  const [count, setCount] = useState(5);
  const [phase, setPhase] = useState<"idle" | "generating" | "ready" | "empty" | "submitting" | "error">("idle");
  const [message, setMessage] = useState("");
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const adaptiveStarted = useRef(false);

  useEffect(() => {
    if (getDemoStudentId()) {
      return;
    }
    const stored = readStoredStudentId();
    const timer = window.setTimeout(() => {
      if (stored) {
        setStudentId(stored);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function loadPublicAssessment(assessmentId: string) {
    const loaded = publicAssessment(await getAssessment(assessmentId));
    if (!loaded || loaded.questions.length === 0) {
      throw new ApiError("The assessment did not include any questions.", 200);
    }
    setAssessment(loaded);
    setSelections({});
    setPhase("ready");
  }

  const start = useCallback(async (mode: "generate" | "adaptive") => {
    const cleaned = topic.trim();
    if (!studentId || !cleaned || phase === "generating" || phase === "submitting") {
      return;
    }
    const questionCount = Math.min(10, Math.max(1, Number.isFinite(count) ? count : 5));
    setPhase("generating");
    setMessage("");
    setAssessment(null);
    setSelections({});
    try {
      const response =
        mode === "adaptive"
          ? await generateAdaptiveAssessment(studentId, cleaned, questionCount)
          : await generateAssessment(studentId, cleaned, questionCount);
      if (!isGeneration(response)) {
        throw new ApiError("The learning API returned an unexpected assessment response.", 200);
      }
      if (response.status === "no_context" || !response.assessment) {
        setPhase("empty");
        setMessage(response.message ?? "No assessment was created from the uploaded material.");
        return;
      }
      await loadPublicAssessment(response.assessment.id);
    } catch (error) {
      setPhase("error");
      setMessage(error instanceof ApiError ? error.message : "The assessment could not be created.");
    }
  }, [count, phase, studentId, topic]);

  useEffect(() => {
    if (adaptiveStarted.current || initialMode !== "adaptive" || !initialTopic || !studentId) {
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      if (cancelled || adaptiveStarted.current) {
        return;
      }
      adaptiveStarted.current = true;
      void start("adaptive");
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [initialMode, initialTopic, studentId, start]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assessment || !studentId || phase === "submitting") {
      return;
    }
    const answers = assessment.questions.map((question) => ({
      question_id: question.id,
      selected_option: selections[question.id] ?? "",
    }));
    if (answers.some((answer) => answer.selected_option.length === 0)) {
      return;
    }
    setPhase("submitting");
    setMessage("");
    try {
      const result = await submitAssessment(assessment.id, studentId, answers);
      saveAssessmentReview({
        result,
        title: assessment.title,
        topic: assessment.topic,
        answers: assessment.questions.map((question) => {
          const selected = selections[question.id] ?? "";
          return {
            question_id: question.id,
            question_text: question.question_text,
            selected_option: selected,
            option_text: question.options[selected] ?? "",
          };
        }),
      });
      router.push("/results");
    } catch (error) {
      setPhase("ready");
      setMessage(error instanceof ApiError ? error.message : "The assessment could not be submitted.");
    }
  }

  const busy = phase === "generating" || phase === "submitting";
  const complete =
    assessment !== null && assessment.questions.every((question) => Boolean(selections[question.id]));

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
      <PageTitle title="Assessments" />
      <div>
        <h2 className="text-page-title text-slate-900">Assessments</h2>
        <p className="mt-1 text-secondary text-slate-500">
          Questions are created from your uploaded learning material.
        </p>
        {studentId ? (
          <p className="mt-1 break-all font-mono text-meta text-slate-500">Student {studentId}</p>
        ) : (
          <p className="mt-2 text-secondary text-rose-700" role="alert">
            Set a development student id before starting an assessment.
          </p>
        )}
      </div>

      <Card>
        <form
          className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_6rem_auto_auto] sm:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            void start("generate");
          }}
        >
          <div>
            <label htmlFor="assessment-topic" className="text-label text-slate-500 uppercase">
              Topic
            </label>
            <input
              id="assessment-topic"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              disabled={busy || !studentId}
              placeholder="Bayes theorem"
              className="mt-1 h-9 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-body text-slate-900 placeholder:text-secondary placeholder:text-slate-400 focus-visible:border-indigo-600 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 disabled:opacity-60"
            />
          </div>
          <div>
            <label htmlFor="assessment-count" className="text-label text-slate-500 uppercase">
              Questions
            </label>
            <input
              id="assessment-count"
              type="number"
              min={1}
              max={10}
              value={count}
              onChange={(event) => setCount(Number(event.target.value))}
              disabled={busy || !studentId}
              className="mt-1 h-9 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-body text-slate-900 focus-visible:border-indigo-600 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 disabled:opacity-60"
            />
          </div>
          <Button type="submit" disabled={busy || !studentId || topic.trim().length === 0}>
            {phase === "generating" ? "Generating" : "Generate"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={busy || !studentId || topic.trim().length === 0}
            onClick={() => void start("adaptive")}
          >
            Adaptive
          </Button>
        </form>
        {phase === "generating" ? (
          <p className="mt-3 text-secondary text-slate-500" role="status">
            Generating the assessment…
          </p>
        ) : null}
        {phase === "empty" ? (
          <EmptyState icon={ClipboardCheck} title="No assessment created" message={message} />
        ) : null}
        {phase === "error" ? (
          <p className="mt-3 text-secondary text-rose-700" role="alert">
            {message}
          </p>
        ) : null}
      </Card>

      {assessment && (phase === "ready" || phase === "submitting") ? (
        <form onSubmit={(event) => void onSubmit(event)}>
          <Card>
            <h3 className="text-section text-slate-900">{assessment.title}</h3>
            {assessment.description ? (
              <p className="mt-1 text-secondary text-slate-500">{assessment.description}</p>
            ) : null}
            <p className="mt-1 font-mono text-meta text-slate-500">
              {assessment.topic} · {assessment.questions.length} questions
            </p>
            <ol className="mt-4 space-y-4">
              {assessment.questions.map((question, index) => (
                <li key={question.id} className="border-t border-slate-100 pt-3">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-card-title text-slate-900">
                      {index + 1}. {question.question_text}
                    </p>
                    <Badge>{question.difficulty}</Badge>
                  </div>
                  {question.source_document_name ? (
                    <p className="mt-1 font-mono text-meta text-slate-400">
                      {question.source_document_name}
                      {question.source_page_number ? ` · page ${question.source_page_number}` : ""}
                    </p>
                  ) : null}
                  <fieldset className="mt-2 space-y-1">
                    <legend className="sr-only">Options for question {index + 1}</legend>
                    {optionEntries(question.options).map(([key, text]) => (
                      <label
                        key={key}
                        className="flex cursor-pointer items-start gap-2 rounded-md px-2 py-1 hover:bg-slate-50"
                      >
                        <input
                          type="radio"
                          name={question.id}
                          value={key}
                          checked={selections[question.id] === key}
                          onChange={() => setSelections((current) => ({ ...current, [question.id]: key }))}
                          disabled={phase === "submitting"}
                          className="mt-1"
                        />
                        <span className="font-mono text-meta text-slate-500">{key}</span>
                        <span className="text-body text-slate-800">{text}</span>
                      </label>
                    ))}
                  </fieldset>
                </li>
              ))}
            </ol>
            {message && phase === "ready" ? (
              <p className="mt-3 text-secondary text-rose-700" role="alert">
                {message}
              </p>
            ) : null}
            <div className="mt-4 flex items-center justify-between gap-3">
              <p className="text-meta text-slate-500">Select one option for every question.</p>
              <Button type="submit" disabled={!complete || phase === "submitting"}>
                {phase === "submitting" ? "Submitting" : "Submit"}
              </Button>
            </div>
            {phase === "submitting" ? (
              <p className="mt-2 text-secondary text-slate-500" role="status">
                Scoring the assessment…
              </p>
            ) : null}
          </Card>
        </form>
      ) : null}
    </div>
  );
}
