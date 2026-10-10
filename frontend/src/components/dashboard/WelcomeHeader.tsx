"use client";

import { useSyncExternalStore } from "react";
import { brand } from "@/lib/brand";
import { greetingForHour } from "@/lib/format";
import { ButtonLink } from "@/components/ui/Button";

function subscribeToClock() {
  return () => {};
}

export function WelcomeHeader() {
  const greeting = useSyncExternalStore(
    subscribeToClock,
    () => greetingForHour(new Date().getHours(), brand.studentLabel),
    () => `Hello, ${brand.studentLabel}`,
  );

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="text-page-title text-slate-900">Dashboard</h2>
        <p className="mt-1 text-secondary text-slate-600">{greeting}</p>
        <p className="text-secondary text-slate-500">Here&apos;s your learning overview.</p>
      </div>
      <ButtonLink href="/assessments">Continue Learning</ButtonLink>
    </div>
  );
}
