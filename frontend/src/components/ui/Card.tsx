import { cn } from "@/lib/format";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section className={cn("rounded-lg border border-slate-200 bg-white p-4", className)}>
      {children}
    </section>
  );
}
