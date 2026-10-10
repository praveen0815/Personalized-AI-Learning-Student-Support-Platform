import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  message,
}: {
  icon: LucideIcon;
  title: string;
  message: string;
}) {
  return (
    <div className="flex flex-col items-start gap-1 py-3">
      <Icon className="h-4 w-4 text-slate-400" aria-hidden="true" />
      <p className="text-card-title text-slate-900">{title}</p>
      <p className="max-w-xl text-secondary text-slate-500">{message}</p>
    </div>
  );
}
