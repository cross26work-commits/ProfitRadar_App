import { Card } from "./Card";

type ChartCardProps = {
  title: string;
  description?: string;
  children?: React.ReactNode;
};

export function ChartCard({ title, description, children }: ChartCardProps) {
  return (
    <Card className="p-5">
      <div className="mb-4">
        <h2 className="text-base font-black text-slate-900">{title}</h2>
        {description && (
          <p className="mt-1 text-sm font-medium text-slate-500">
            {description}
          </p>
        )}
      </div>
      <div className="flex min-h-64 items-center justify-center rounded-2xl bg-slate-50">
        {children ?? (
          <p className="max-w-md px-6 text-center text-sm font-medium leading-6 text-slate-600">
            まだ推移を表示できるデータがありません。売上・入金・原価を記録すると、ここに推移が表示されます。
          </p>
        )}
      </div>
    </Card>
  );
}
