"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { LineChart as LineChartIcon } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import type { MasteryPoint } from "@/types/learning";

export function LearningProgressChart({
  points,
  emptyMessage,
}: {
  points: MasteryPoint[];
  emptyMessage: string;
}) {
  return (
    <Card className="flex h-full min-h-52 flex-col">
      <h2 className="text-section text-slate-900">Learning Progress</h2>
      <p className="mt-1 text-secondary text-slate-500">Track how your mastery changes over time.</p>
      {points.length === 0 ? (
        <EmptyState
          icon={LineChartIcon}
          title="Complete more assessments to see your mastery trend."
          message={emptyMessage}
        />
      ) : (
        <div className="mt-4 h-52">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Line type="monotone" dataKey="mastery" stroke="#4338ca" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
