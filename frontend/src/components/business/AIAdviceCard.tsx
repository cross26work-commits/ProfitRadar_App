import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

type AIAdviceCardProps = {
  title?: string;
  decision?: string;
  reason?: string;
  nextAction?: string;
  badge?: string;
  children?: React.ReactNode;
};

export function AIAdviceCard({
  title = "AI判断",
  decision,
  reason,
  nextAction,
  badge = "24時間以内に対応推奨",
  children,
}: AIAdviceCardProps) {
  return (
    <Card className="border-green-100 bg-green-50 p-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <h3 className="text-lg font-black text-slate-950">{title}</h3>
          {decision && (
            <p className="mt-2 text-2xl font-black tracking-tight text-slate-950">
              {decision}
            </p>
          )}
        </div>
        <Badge tone="green">{badge}</Badge>
      </div>

      {children ? (
        <div className="mt-4 text-sm font-medium leading-7 text-slate-700">
          {children}
        </div>
      ) : (
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-xs font-black text-slate-500">理由</p>
            <p className="mt-1 text-sm font-medium leading-6 text-slate-700">
              {reason}
            </p>
          </div>
          <div>
            <p className="text-xs font-black text-slate-500">次の行動</p>
            <p className="mt-1 text-sm font-black leading-6 text-slate-950">
              {nextAction}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
