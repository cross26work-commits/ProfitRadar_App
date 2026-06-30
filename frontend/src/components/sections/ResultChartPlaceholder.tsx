import { Card } from "@/components/ui/Card";

type ResultChartPlaceholderProps = {
  title: string;
  description?: string;
};

export function ResultChartPlaceholder({ title, description }: ResultChartPlaceholderProps) {
  return (
    <Card className="p-5">
      <div className="mb-4">
        <h2 className="text-base font-black text-slate-900">{title}</h2>
        {description && (
          <p className="mt-1 text-sm font-medium text-slate-500">{description}</p>
        )}
      </div>

      <div className="flex h-64 items-center justify-center rounded-2xl bg-green-50 text-sm font-bold text-green-700">
        Chart Placeholder
      </div>
    </Card>
  );
}
