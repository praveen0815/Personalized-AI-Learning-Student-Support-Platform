import { ClipboardCheck } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { buildRecommendations } from "@/lib/recommendations";
import { formatMastery, severityLabel } from "@/lib/mastery";
import type { LearningGap, TopicProgress } from "@/types/learning";

type SectionStatus = "loading" | "unconfigured" | "error" | "ready";

export function RecommendedActions({
  gaps,
  topics,
  progressStatus,
  gapsStatus,
  progressMessage,
  gapsMessage,
  onRetry,
}: {
  gaps: LearningGap[];
  topics: TopicProgress[];
  progressStatus: SectionStatus;
  gapsStatus: SectionStatus;
  progressMessage?: string;
  gapsMessage?: string;
  onRetry: () => void;
}) {
  const loading = progressStatus === "loading" || gapsStatus === "loading";
  const recommendations =
    progressStatus === "ready" || gapsStatus === "ready"
      ? buildRecommendations(gapsStatus === "ready" ? gaps : [], progressStatus === "ready" ? topics : [])
      : [];
  const errorMessages = [
    progressStatus === "error" ? progressMessage : undefined,
    gapsStatus === "error" ? gapsMessage : undefined,
  ].filter((message): message is string => Boolean(message));

  return (
    <section>
      <h2 className="text-section text-slate-900">Recommended Next</h2>
      <p className="mt-1 text-secondary text-slate-500">
        Ordered from active gaps, then the lowest-mastery topics in the progress record.
      </p>
      {loading ? <Skeleton className="mt-3 h-24" /> : null}
      {!loading && errorMessages.length > 0 ? (
        <div className="mt-3">
          <ErrorState message={errorMessages[0]} onRetry={onRetry} />
          {errorMessages.slice(1).map((message) => (
            <p key={message} className="mt-2 text-secondary text-rose-700" role="alert">
              {message}
            </p>
          ))}
        </div>
      ) : null}
      {!loading && progressStatus === "unconfigured" && gapsStatus === "unconfigured" ? (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white px-4">
          <EmptyState
            icon={ClipboardCheck}
            title="No recommendations yet."
            message="Connect a student record to see the next topic to practice."
          />
        </div>
      ) : null}
      {!loading &&
      errorMessages.length === 0 &&
      (progressStatus === "ready" || gapsStatus === "ready") &&
      recommendations.length === 0 ? (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white px-4">
          <EmptyState
            icon={ClipboardCheck}
            title="No recommendations yet."
            message="No learning gaps or tracked topics were returned. Complete an assessment to build a learner record."
          />
        </div>
      ) : null}
      {!loading && recommendations.length > 0 ? (
        <ul className="mt-3 grid gap-3 md:grid-cols-2">
          {recommendations.map((item) => (
            <li key={item.topic} className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-card-title text-slate-900">{item.topic}</h3>
                {item.severity ? (
                  <Badge tone={item.severity === "high" ? "attention" : item.severity === "medium" ? "improving" : "neutral"}>
                    {severityLabel(item.severity)}
                  </Badge>
                ) : null}
              </div>
              <p className="mt-1 font-mono text-meta text-slate-500">Mastery {formatMastery(item.mastery)}%</p>
              <p className="mt-2 text-secondary text-slate-700">{item.reason}</p>
              <ButtonLink
                className="mt-3"
                href={`/assessments?topic=${encodeURIComponent(item.topic)}&mode=adaptive`}
                variant="secondary"
              >
                Practice
              </ButtonLink>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
