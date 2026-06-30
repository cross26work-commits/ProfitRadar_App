import { Card } from "./Card";

export function StatCard({
  label,
  value,
  sub,
  tone = "neutral",
}: {
  label: string;
  value: string;
  sub: string;
  tone?: string;
}) {
  const valueClass =
    tone === "danger" ? "text-red-600" : tone === "green" ? "text-green-600" : "text-slate-900";

  return (
    <Card className="p-5">
      <p className="text-sm font-bold text-slate-700">{label}</p>
      <p className={`mt-3 text-3xl font-black tracking-tight ${valueClass}`}>{value}</p>
      <p className="mt-2 text-sm text-slate-500">{sub}</p>
    </Card>
  );
}
