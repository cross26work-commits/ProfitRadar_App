import { Card } from "@/components/ui/Card";

type SalesForecast = {
  actual_profit: number;
  estimated_profit: number;
  open_profit: number;
  closed_profit: number;
  hot_open_profit: number;
  forecast: {
    conservative: number;
    standard: number;
    aggressive: number;
  };
  message: string;
};

function yen(value: number) {
  return `¥${Number(value || 0).toLocaleString("ja-JP")}`;
}

export function SalesForecastSection({
  forecast,
}: {
  forecast: SalesForecast | null;
}) {
  if (!forecast) return null;

  return (
    <Card className="p-5">
      <div>
        <h2 className="text-base font-black text-slate-900">AI売上予測</h2>
        <p className="mt-1 text-sm font-medium text-slate-500">
          {forecast.message}
        </p>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-bold text-slate-500">保守予測</p>
          <p className="mt-2 text-2xl font-black text-slate-950">
            {yen(forecast.forecast.conservative)}
          </p>
        </div>

        <div className="rounded-2xl bg-green-50 p-4">
          <p className="text-sm font-bold text-slate-500">標準予測</p>
          <p className="mt-2 text-2xl font-black text-green-700">
            {yen(forecast.forecast.standard)}
          </p>
        </div>

        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-bold text-slate-500">強気予測</p>
          <p className="mt-2 text-2xl font-black text-slate-950">
            {yen(forecast.forecast.aggressive)}
          </p>
        </div>
      </div>
    </Card>
  );
}
