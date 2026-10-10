import type { Metadata } from "next";
import { LearningGapsScreen } from "@/components/progress/LearningGapsScreen";

export const metadata: Metadata = { title: "Learning Gaps" };

export default function LearningGapsPage() {
  return <LearningGapsScreen />;
}
