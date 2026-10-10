import { BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatMastery, masteryBand } from "@/lib/mastery";
import type { TopicProgress } from "@/types/learning";

export function TopicMastery({
  topics,
  status,
  message,
  onRetry,
  showPractice = false,
}: {
  topics: TopicProgress[];
  status: "loading" | "unconfigured" | "error" | "ready";
  message?: string;
  onRetry: () => void;
  showPractice?: boolean;
}) {
  return (
    <Card>
      <h2 className="text-section text-slate-900">Topic Mastery</h2>
      <p className="mt-1 text-secondary text-slate-500">Scores come from the learner record. The labels are for display only.</p>
      {status === "loading" ? <Skeleton className="mt-5 h-28" /> : null}
      {status === "error" && message ? <ErrorState message={message} onRetry={onRetry} /> : null}
      {status === "unconfigured" ? (
        <EmptyState icon={BookOpen} title="No learning progress yet." message="Connect a student record to load topic mastery." />
      ) : null}
      {status === "ready" && topics.length === 0 ? (
        <div>
          <EmptyState
            icon={BookOpen}
            title="No learning progress yet."
            message="Complete an assessment to start building your learner profile."
          />
          <ButtonLink href="/assessments" variant="secondary">
            Take Assessment
          </ButtonLink>
        </div>
      ) : null}
      {status === "ready" && topics.length > 0 ? (
        <ul className="mt-3 space-y-3">
          {topics.map((topic) => {
            const band = masteryBand(topic.mastery);
            return (
              <li key={topic.topic}>
                <div className="mb-1 flex items-center justify-between gap-3">
                  <p className="min-w-0 truncate text-body font-medium text-slate-900">{topic.topic}</p>
                  <div className="flex items-center gap-2">
                    <Badge tone={band.band}>{band.label}</Badge>
                    <span className="text-secondary font-medium text-slate-700">{formatMastery(topic.mastery)}%</span>
                  </div>
                </div>
                <ProgressBar value={topic.mastery} band={band.band} label={`${topic.topic} mastery`} />
                <p className="mt-1 font-mono text-meta text-slate-500">
                  {topic.questions_attempted} attempted · {topic.questions_correct} correct
                </p>
                {showPractice ? (
                  <ButtonLink
                    className="mt-2"
                    href={`/assessments?topic=${encodeURIComponent(topic.topic)}`}
                    variant="secondary"
                  >
                    Practice
                  </ButtonLink>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}
    </Card>
  );
}
