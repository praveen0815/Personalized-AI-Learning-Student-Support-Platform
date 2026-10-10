export function StatCard({
  label,
  value,
  supporting,
}: {
  label: string;
  value: string;
  supporting: string;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-label text-slate-500 uppercase">{label}</p>
      <p className="mt-2 text-kpi text-slate-900">{value}</p>
      <p className="mt-1 text-secondary text-slate-500">{supporting}</p>
    </section>
  );
}
