import type { Metadata } from "next";
import { Settings } from "lucide-react";
import { ApiHealthNote } from "@/components/settings/ApiHealthNote";
import { PlaceholderPage } from "@/components/pages/PlaceholderPage";
import { getDemoStudentId } from "@/lib/env";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  const connected = getDemoStudentId() !== null;

  return (
    <PlaceholderPage
      title="Settings"
      description="Sign-in is not part of this version. The dashboard reads one development student id from the environment."
      icon={Settings}
    >
      <p className="mt-3 text-secondary text-slate-700">
        Development student: {connected ? "configured in the environment" : "not set in the environment"}.
      </p>
      {connected ? (
        <p className="mt-2 font-mono text-meta text-slate-500">{getDemoStudentId()}</p>
      ) : null}
      <ApiHealthNote />
    </PlaceholderPage>
  );
}
