import { TimelineItem } from "@/components/business/TimelineItem";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/feedback/EmptyState";

type Timeline = {
  type: string;
  title: string;
  body: string;
  time: string;
};

type TimelineSectionProps = {
  title: string;
  items: Timeline[];
};

export function TimelineSection({ title, items }: TimelineSectionProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-base font-black text-slate-900">{title}</h2>

      <Card className="p-5">
        {items.length === 0 ? (
          <EmptyState title="履歴がありません" description="メール・SMS・対応履歴はまだありません。" />
        ) : (
          <div className="space-y-5">
            {items.map((item, index) => (
              <TimelineItem key={`${item.type}-${item.title}-${item.time}-${index}`} {...item} />
            ))}
          </div>
        )}
      </Card>
    </section>
  );
}
