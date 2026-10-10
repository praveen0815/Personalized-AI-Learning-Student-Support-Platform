"use client";

import { useEffect, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { readAssessmentReview, type StoredAssessmentReview } from "@/lib/assessment-session";
import { formatMastery, severityLabel } from "@/lib/mastery";

export function ResultsScreen() {
  const [review, setReview] = useState<StoredAssessmentReview | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setReview(readAssessmentReview());
      setReady(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
      <PageTitle title="Results" />
      <div>
        <h2 className="text-page-title text-slate-900">Results</h2>
        <p className="mt-1 text-secondary text-slate-500">Scores come from the submitted assessment.</p>
      </div>

      {!ready ? <Card><p className="text-secondary text-slate-500">Loading the result…</p></Card> : null}

      {ready && !review ? (
        <Card>
          <EmptyState
            icon={ClipboardCheck}
            title="No assessment result"
            message="Submit an assessment to see the score returned by the learning API."
          />
          <ButtonLink href="/assessments" variant="secondary">
            Go to assessments
          </ButtonLink>
        </Card>
      ) : null}

      {review ? (
        <>
          <Card>
            <h3 className="text-section text-slate-900">{review.title}</h3>
            <p className="mt-1 font-mono text-meta text-slate-500">{review.topic}</p>
            <p className="mt-3 text-kpi text-slate-900">
              {review.result.score}/{review.result.total_questions}
            </p>
            <p className="font-mono text-secondary text-slate-600">{formatMastery(review.result.percentage)}%</p>
            <p className="mt-1 break-all font-mono text-meta text-slate-400">Attempt {review.result.attempt_id}</p>
          </Card>

          <Card>
            <h3 className="text-section text-slate-900">Topic performance</h3>
            {review.result.topic_results.length === 0 ? (
              <p className="mt-2 text-secondary text-slate-500">No topic scores were returned.</p>
            ) : (
              <ul className="mt-3 divide-y divide-slate-100">
                {review.result.topic_results.map((topic) => (
                  <li key={topic.topic} className="flex items-center justify-between gap-3 py-2">
                    <p className="text-body font-medium text-slate-900">{topic.topic}</p>
                    <p className="font-mono text-meta text-slate-500">
                      {topic.correct} correct · {topic.attempted - topic.correct} incorrect · {topic.attempted} attempted · mastery{" "}
                      {formatMastery(topic.mastery)}%
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <h3 className="text-section text-slate-900">Your answers</h3>
            <p className="mt-1 text-secondary text-slate-500">
              The result does not include answer keys or explanations.
            </p>
            {review.answers.length === 0 ? (
              <p className="mt-2 text-secondary text-slate-500">No selected answers were stored for this result.</p>
            ) : (
              <ol className="mt-3 space-y-3">
                {review.answers.map((answer, index) => (
                  <li key={answer.question_id} className="border-t border-slate-100 pt-2">
                    <p className="text-body text-slate-900">
                      {index + 1}. {answer.question_text}
                    </p>
                    <p className="mt-1 font-mono text-meta text-slate-500">
                      Selected {answer.selected_option}
                      {answer.option_text ? ` · ${answer.option_text}` : ""}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </Card>

          <Card>
            <h3 className="text-section text-slate-900">Learning gaps</h3>
            {review.result.learning_gaps.length === 0 ? (
              <p className="mt-2 text-secondary text-slate-500">No learning gaps were returned for this result.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {review.result.learning_gaps.map((gap) => (
                  <li key={`${gap.topic}-${gap.detected_at}`} className="border-t border-slate-100 pt-2">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-card-title text-slate-900">{gap.topic}</p>
                      <Badge tone={gap.severity === "high" ? "attention" : "improving"}>{severityLabel(gap.severity)}</Badge>
                    </div>
                    <p className="mt-1 font-mono text-meta text-slate-500">
                      Mastery {formatMastery(gap.mastery)}% · {gap.status}
                    </p>
                    <p className="mt-1 text-secondary text-slate-700">{gap.reason}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
