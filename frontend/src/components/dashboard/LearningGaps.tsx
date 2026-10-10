import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { LearningGapCard } from "@/components/dashboard/LearningGapCard";
import type { LearningGap } from "@/types/learning";

export function LearningGaps({
  gaps,
  status,
  message,
  onRetry,
}: {
  gaps: LearningGap[];
  status: "loading" | "unconfigured" | "error" | "ready";
  message?: string;
  onRetry: () => void;
}) {
  const ordered = [...gaps].sort((left, right) => {
    if (left.severity === right.severity) {
      return left.mastery - right.mastery;
    }
    return left.severity === "high" ? -1 : 1;
  });

  return (
    <section>
      <h2 className="text-section text-slate-900">Learning Gaps</h2>
      <p className="mt-1 text-secondary text-slate-500">Active gaps returned by the learning record.</p>
      {status === "loading" ? <Skeleton className="mt-4 h-40" /> : null}
      {status === "error" && message ? (
        <div className="mt-4">
          <ErrorState message={message} onRetry={onRetry} />
        </div>
      ) : null}
      {status === "unconfigured" ? (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white px-4">
          <EmptyState
            icon={AlertTriangle}
            title="No learning gaps to show."
            message="Connect a student record to see topics that need attention."
          />
        </div>
      ) : null}
      {status === "ready" && ordered.length === 0 ? (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white px-4">
          <EmptyState icon={CheckCircle2} title="You're on track." message="No active learning gaps were detected." />
        </div>
      ) : null}
      {status === "ready" && ordered.length > 0 ? (
        <div className="mt-4 space-y-3">
          {ordered.map((gap) => (
            <LearningGapCard key={`${gap.topic}-${gap.detected_at}`} gap={gap} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
