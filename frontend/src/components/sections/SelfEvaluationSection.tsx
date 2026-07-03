import { Card } from "@/components/ui/Card";

type SelfEvaluation = {
  count: number;
  success_count: number;
  avg_accuracy: number;
  message: string;
};

export function SelfEvaluationSection({
  evaluation,
}: {
  evaluation: SelfEvaluation | null;
}) {
  if (!evaluation) return null;

  return (
    <Card className="p-5">
      <div>
        <h2 className="text-base font-black text-slate-900">AI自己評価</h2>
        <p className="mt-1 text-sm font-medium text-slate-500">
          {evaluation.message}
        </p>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-bold text-slate-500">評価件数</p>
          <p className="mt-2 text-2xl font-black text-slate-950">
            {evaluation.count}件
          </p>
        </div>

        <div className="rounded-2xl bg-green-50 p-4">
          <p className="text-sm font-bold text-slate-500">成功件数</p>
          <p className="mt-2 text-2xl font-black text-green-700">
            {evaluation.success_count}件
          </p>
        </div>

        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-bold text-slate-500">平均精度</p>
          <p className="mt-2 text-2xl font-black text-slate-950">
            {evaluation.avg_accuracy}%
          </p>
        </div>
      </div>
    </Card>
  );
}
