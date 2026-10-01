import type { StatItem, Task } from "@/types/profit-radar";
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
    <section className="space-y-6">
      <StatsGrid items={stats} />
      <TaskListSection title="今日やること" tasks={tasks} />
    </section>
  );
}
