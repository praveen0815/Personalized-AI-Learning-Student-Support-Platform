import type { Metadata } from "next";
import { TutorScreen } from "@/components/tutor/TutorScreen";

export const metadata: Metadata = { title: "AI Tutor" };

export default async function TutorPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawTopic = Array.isArray(params.topic) ? params.topic[0] : params.topic;
  const topic = rawTopic?.trim() ? rawTopic.trim() : undefined;

  return <TutorScreen topic={topic} />;
}
