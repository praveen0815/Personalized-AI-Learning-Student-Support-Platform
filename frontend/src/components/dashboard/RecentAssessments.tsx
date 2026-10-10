import { ClipboardList } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import type { AssessmentHistoryItem } from "@/types/learning";

export function RecentAssessments({
  items,
  historyAvailable,
}: {
  items: AssessmentHistoryItem[];
  historyAvailable: boolean;
}) {
  return (
    <Card>
      <h2 className="text-section text-slate-900">Recent Assessments</h2>
      {!historyAvailable ? (
        <EmptyState
          icon={ClipboardList}
          title="No assessment history available yet."
          message="The learning API does not return past assessments."
        />
      ) : items.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No assessments completed yet."
          message="Take your first assessment to start tracking progress."
        />
      ) : (
        <ul className="mt-4 divide-y divide-slate-100">
          {items.map((item) => (
            <li key={item.id} className="flex items-center justify-between gap-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-body font-medium text-slate-900">{item.title}</p>
                <p className="text-secondary text-slate-500">{item.topic}</p>
              </div>
              <p className="text-secondary font-medium text-slate-900">{Math.round(item.percentage)}%</p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
