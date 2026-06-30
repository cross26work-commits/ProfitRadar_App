import { Card } from "../ui/Card";

type ProfitSummaryProps = {
  todayProfit: string;
  recoverableProfit: string;
  nextAction: string;
};

export function ProfitSummary({
  todayProfit,
  recoverableProfit,
  nextAction,
}: ProfitSummaryProps) {
  return (
    <Card className="p-6">
      <p className="text-sm font-bold text-slate-500">今日の利益</p>
      <p className="mt-3 text-4xl font-black tracking-tight text-slate-900">
        {todayProfit}
      </p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl bg-green-50 p-4">
          <p className="text-sm font-bold text-green-700">回収可能利益</p>
          <p className="mt-2 text-2xl font-black text-green-700">
            {recoverableProfit}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-bold text-slate-500">今日やること</p>
          <p className="mt-2 font-black text-slate-900">{nextAction}</p>
        </div>
      </div>
    </Card>
  );
}
