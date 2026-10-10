import type { Metadata } from "next";
import { KnowledgeScreen } from "@/components/knowledge/KnowledgeScreen";

export const metadata: Metadata = { title: "Knowledge Base" };

export default function KnowledgePage() {
  return <KnowledgeScreen />;
}
