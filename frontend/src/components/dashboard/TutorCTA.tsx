import { Bot } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";

export function TutorCTA() {
  return (
    <section className="flex h-full min-h-52 flex-col justify-between rounded-lg border border-indigo-200 bg-indigo-50 p-4">
      <div>
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-white text-indigo-700">
          <Bot className="h-4 w-4" aria-hidden="true" />
        </span>
        <h2 className="mt-3 text-section text-slate-900">AI Tutor</h2>
        <p className="mt-2 text-secondary text-slate-700">Need help understanding a difficult topic?</p>
        <p className="mt-1 text-secondary text-slate-600">Ask questions using your uploaded material.</p>
      </div>
      <ButtonLink href="/tutor" className="mt-4 w-full">
        Open AI Tutor
      </ButtonLink>
    </section>
  );
}
