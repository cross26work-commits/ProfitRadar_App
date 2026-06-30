import { Card } from "./Card";

type StatCardProps = {
  label: string;
  value: string;
  sub?: string;
  valueClass?: string;
};

export function StatCard({
  label,
  value,
  sub,
  valueClass = "text-slate-950",
}: StatCardProps) {
  return (
    <Card className="min-h-[132px] p-5">
      <p className="max-w-[9rem] text-sm font-black leading-5 text-slate-700">
        {label}
      </p>
      <p className={`mt-3 whitespace-nowrap text-3xl font-black tracking-tight ${valueClass}`}>
        {value}
      </p>
      {sub && <p className="mt-2 text-sm font-medium text-slate-500">{sub}</p>}
    </Card>
  );
}
