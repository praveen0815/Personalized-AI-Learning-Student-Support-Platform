"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "@/components/ui/Card";
import type { TopicProgress } from "@/types/learning";

export function MasteryChart({ topics }: { topics: TopicProgress[] }) {
  const height = Math.min(320, Math.max(160, topics.length * 36));

  return (
    <Card>
      <h2 className="text-section text-slate-900">Mastery by topic</h2>
      <p className="mt-1 text-secondary text-slate-500">Latest mastery returned for each topic.</p>
      <div className="mt-3" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topics} layout="vertical" margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <XAxis type="number" domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="topic"
              width={128}
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6 }} />
            <Bar dataKey="mastery" fill="#4338ca" radius={[0, 4, 4, 0]} barSize={10} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
