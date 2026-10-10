import type { LearningGap, TopicProgress } from "@/types/learning";

export type Recommendation = {
  topic: string;
  mastery: number;
  severity: string | null;
  reason: string;
};

function gapOrder(severity: string): number {
  if (severity === "high") {
    return 0;
  }
  if (severity === "medium") {
    return 1;
  }
  return 2;
}

/**
 * Orders topics already returned by the progress and learning-gap APIs.
 * This does not assign severity or recalculate mastery.
 */
export function buildRecommendations(gaps: LearningGap[], topics: TopicProgress[]): Recommendation[] {
  const orderedGaps = [...gaps].sort((left, right) => {
    const severityOrder = gapOrder(left.severity) - gapOrder(right.severity);
    if (severityOrder !== 0) {
      return severityOrder;
    }
    return left.mastery - right.mastery;
  });
  const covered = new Set(orderedGaps.map((gap) => gap.topic));
  const remaining = topics.filter((topic) => !covered.has(topic.topic)).sort((left, right) => left.mastery - right.mastery);
  const lowestMastery = remaining.length > 0 ? remaining[0].mastery : null;

  return [
    ...orderedGaps.map((gap) => ({
      topic: gap.topic,
      mastery: gap.mastery,
      severity: gap.severity,
      reason: gap.reason,
    })),
    ...remaining.map((topic) => ({
      topic: topic.topic,
      mastery: topic.mastery,
      severity: null,
      reason:
        topic.mastery === lowestMastery
          ? "Lowest mastery among tracked topics without an active gap."
          : "Continue practice on a tracked topic.",
    })),
  ];
}
