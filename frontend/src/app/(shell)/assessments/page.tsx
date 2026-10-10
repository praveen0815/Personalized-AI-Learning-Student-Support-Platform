import type { Metadata } from "next";
import { AssessmentScreen } from "@/components/assessments/AssessmentScreen";

export const metadata: Metadata = { title: "Assessments" };

function firstParam(value: string | string[] | undefined): string | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  const trimmed = raw?.trim();
  return trimmed ? trimmed : undefined;
}

export default async function AssessmentsPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string | string[]; mode?: string | string[] }>;
}) {
  const params = await searchParams;
  const topic = firstParam(params.topic);
  const mode = firstParam(params.mode) === "adaptive" ? "adaptive" : undefined;

  return <AssessmentScreen initialTopic={topic} initialMode={mode} />;
}
