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
  badge = "AI分析",
  children,
}: AIAdviceCardProps) {
  return (
    <Card className="border-emerald-100 bg-emerald-50 p-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <h3 className="text-lg font-bold text-slate-950">
            {title}
          </h3>

          {decision ? (
            <p className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
              {decision}
            </p>
          ) : null}
        </div>

        <Badge tone="green">
          {badge}
        </Badge>
      </div>

      {children ? (
        <div className="mt-4 text-sm font-medium leading-7 text-slate-700">
          {children}
        </div>
      ) : (
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-xs font-bold text-slate-500">
              理由
            </p>

            <p className="mt-1 text-sm font-medium leading-6 text-slate-700">
              {reason || "分析中"}
            </p>
          </div>

          <div>
            <p className="text-xs font-bold text-slate-500">
              次の行動
            </p>

            <p className="mt-1 text-sm font-bold leading-6 text-slate-950">
              {nextAction || "まだ提案はありません"}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
