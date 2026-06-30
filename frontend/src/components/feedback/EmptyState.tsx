import { Button } from "@/components/ui/Button";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
      <div className="mx-auto mb-4 h-12 w-12 rounded-2xl bg-green-50" />
      <h3 className="text-lg font-black text-slate-900">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
      {action ? (
        <div className="mt-5">
          <Button>{action}</Button>
        </div>
      ) : null}
    </div>
  );
}
