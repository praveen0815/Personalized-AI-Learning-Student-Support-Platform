import type { TopicProgress } from "@/types/learning";

export type MasteryBand = "strong" | "improving" | "attention";

export function masteryBand(mastery: number): { label: string; band: MasteryBand } {
  if (mastery >= 70) {
    return { label: "Strong", band: "strong" };
  }
  if (mastery >= 50) {
    return { label: "Improving", band: "improving" };
  }
  return { label: "Needs attention", band: "attention" };
}

/** Presents the backend severity. This does not assign a new severity. */
export function severityLabel(severity: string): string {
  if (severity === "high") {
    return "High";
  }
  if (severity === "medium") {
    return "Medium";
  }
  if (severity === "low") {
    return "Low";
  }
  return severity;
}

export function formatMastery(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }
  return String(Math.round(value * 100) / 100);
}

/**
 * Display-only average of the topic mastery scores returned by the progress API.
 * The learner model itself stays on the backend and is not recalculated here.
 */
export function averageMastery(topics: TopicProgress[]): number | null {
  if (topics.length === 0) {
    return null;
  }
  const total = topics.reduce((sum, topic) => sum + topic.mastery, 0);
  return Math.round(total / topics.length);
}

/** Sum of the per-topic attempt counts returned by the progress API. */
export function questionsAttempted(topics: TopicProgress[]): number {
  return topics.reduce((sum, topic) => sum + topic.questions_attempted, 0);
}
