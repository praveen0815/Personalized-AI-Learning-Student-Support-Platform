import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { formatMastery, severityLabel } from "@/lib/mastery";
import type { LearningGap } from "@/types/learning";

export function LearningGapCard({
  gap,
  practiceHref = `/tutor?topic=${encodeURIComponent(gap.topic)}`,
  practiceLabel = "Practice Topic",
}: {
  gap: LearningGap;
  practiceHref?: string;
  practiceLabel?: string;
}) {
  const high = gap.severity === "high";
  return (
    <Card className={high ? "border-rose-200" : "border-amber-200"}>
      <p className="text-label text-slate-500 uppercase">Learning gap</p>
      <div className="mt-2 flex items-start justify-between gap-3">
        <h3 className="text-card-title text-slate-900">{gap.topic}</h3>
        <Badge tone={high ? "attention" : "improving"}>{severityLabel(gap.severity)}</Badge>
      </div>
      <p className="mt-1 font-mono text-meta text-slate-600">
        Mastery {formatMastery(gap.mastery)}% · {gap.status}
      </p>
      <p className="mt-2 text-secondary text-slate-700">{gap.reason}</p>
      <ButtonLink className="mt-3" href={practiceHref} variant="secondary">
        {practiceLabel}
      </ButtonLink>
    </Card>
  );
}
