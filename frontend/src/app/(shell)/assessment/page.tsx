import { redirect } from "next/navigation";

export default async function AssessmentAliasPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string | string[]; mode?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawTopic = Array.isArray(params.topic) ? params.topic[0] : params.topic;
  const rawMode = Array.isArray(params.mode) ? params.mode[0] : params.mode;
  const topic = rawTopic?.trim() ? rawTopic.trim() : "";
  const mode = rawMode?.trim() === "adaptive" ? "adaptive" : "";
  const query = new URLSearchParams();
  if (topic) {
    query.set("topic", topic);
  }
  if (mode) {
    query.set("mode", mode);
  }
  const search = query.toString();
  redirect(search ? `/assessments?${search}` : "/assessments");
}
