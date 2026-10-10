import { cn } from "@/lib/format";
import type { MasteryBand } from "@/lib/mastery";

const fills: Record<MasteryBand, string> = {
  strong: "bg-emerald-600",
  improving: "bg-amber-500",
  attention: "bg-rose-600",
};

export function ProgressBar({
  value,
  label,
  band,
}: {
  value: number;
  label: string;
  band: MasteryBand;
}) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div
      className="h-1.5 overflow-hidden rounded-full bg-slate-100"
      role="progressbar"
      aria-valuenow={Math.round(width)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div
        className={cn("h-full rounded-full transition-[width] duration-500", fills[band])}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}
