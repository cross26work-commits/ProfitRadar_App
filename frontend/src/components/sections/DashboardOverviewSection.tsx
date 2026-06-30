import Link from "next/link";
import type { StatItem, Task } from "@/types/profit-radar";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatsGrid } from "./StatsGrid";
import { TaskListSection } from "./TaskListSection";

type DashboardOverviewSectionProps = {
  stats: StatItem[];
  tasks: Task[];
};

export function DashboardOverviewSection({
  stats,
  tasks,
}: DashboardOverviewSectionProps) {
  return (
    <section className="grid items-start gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <div className="space-y-5">
        <StatsGrid items={stats} />

        <Card className="p-6">
          <p className="text-sm font-black text-slate-500">次に押すボタン</p>
          <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950">
            利益に直結する返信から処理
          </h2>
          <p className="mt-2 text-sm font-medium leading-6 text-slate-500">
            高利益・長期放置・見積/契約に近い案件を優先して確認します。
          </p>
          <div className="mt-5">
            <Link href="/reply">
              <Button>今すぐ返信へ</Button>
            </Link>
          </div>
        </Card>
      </div>

      <TaskListSection title="今日やること" tasks={tasks} />
    </section>
  );
}
