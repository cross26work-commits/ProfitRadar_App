import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

export function AIAdviceCard({
  title = "AI判断",
  children,
  badge = "24時間以内に対応推奨",
}: {
  title?: string;
  children: React.ReactNode;
  badge?: string;
}) {
  return (
    <Card className="bg-green-50 p-6">
      <h3 className="text-xl font-black text-slate-900">{title}</h3>
      <div className="mt-3 leading-7 text-slate-700">{children}</div>
      <div className="mt-4">
        <Badge tone="green">{badge}</Badge>
      </div>
    </Card>
  );
}
