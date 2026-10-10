import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4" role="alert">
      <AlertCircle className="h-4 w-4 text-rose-700" aria-hidden="true" />
      <h2 className="mt-2 text-card-title text-slate-900">{message}</h2>
      <p className="mt-1 text-secondary text-slate-500">Check that the learning API is running, then try again.</p>
      <Button className="mt-3" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}
