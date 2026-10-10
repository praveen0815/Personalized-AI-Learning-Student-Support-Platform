import type { LucideIcon } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function PlaceholderPage({
  title,
  description,
  icon: Icon,
  actionHref,
  actionLabel,
  children,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
  actionHref?: string;
  actionLabel?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-5xl">
      <PageTitle title={title} />
      <Card>
        <Icon className="h-5 w-5 text-indigo-700" aria-hidden="true" />
        <h2 className="mt-3 text-page-title text-slate-900">{title}</h2>
        <p className="mt-1 max-w-2xl text-secondary text-slate-500">{description}</p>
        {actionHref && actionLabel ? (
          <ButtonLink className="mt-4" href={actionHref} variant="secondary">
            {actionLabel}
          </ButtonLink>
        ) : null}
        {children}
      </Card>
    </div>
  );
}
