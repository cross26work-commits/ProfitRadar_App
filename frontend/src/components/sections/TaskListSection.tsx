import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/feedback/EmptyState";

type Task = {
  id?: string | number;
  title: string;
  description: string;
};

type TaskListSectionProps = {
  title: string;
  tasks: Task[];
};

export function TaskListSection({ title, tasks }: TaskListSectionProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-base font-black text-slate-900">{title}</h2>

      <Card className="space-y-3 p-5">
        {tasks.length === 0 ? (
          <EmptyState title="タスクがありません" description="今日対応すべき項目はありません。" />
        ) : (
          tasks.map((task, index) => (
            <div key={task.id ?? task.title} className="flex gap-3 rounded-2xl bg-slate-50 p-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-100 text-sm font-black text-green-700">
                {index + 1}
              </div>
              <div>
                <p className="font-black text-slate-900">{task.title}</p>
                <p className="mt-1 text-sm font-medium leading-6 text-slate-500">
                  {task.description}
                </p>
              </div>
            </div>
          ))
        )}
      </Card>
    </section>
  );
}
