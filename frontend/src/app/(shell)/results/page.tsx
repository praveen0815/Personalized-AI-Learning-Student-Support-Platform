import type { Metadata } from "next";
import { ResultsScreen } from "@/components/assessments/ResultsScreen";

export const metadata: Metadata = { title: "Results" };

export default function ResultsPage() {
  return <ResultsScreen />;
}
