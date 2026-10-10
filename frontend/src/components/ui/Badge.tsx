import { cn } from "@/lib/format";
import type { MasteryBand } from "@/lib/mastery";

const tones = {
  strong: "bg-emerald-50 text-emerald-800",
  improving: "bg-amber-50 text-amber-800",
  attention: "bg-rose-50 text-rose-800",
  neutral: "bg-slate-100 text-slate-700",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: MasteryBand | "neutral";
}) {
  return (
    <span className={cn("inline-flex h-6 items-center rounded px-2 text-status uppercase", tones[tone])}>
      {children}
    </span>
  );
}
