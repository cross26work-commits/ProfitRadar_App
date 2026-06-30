import type { Timeline } from "@/types/profit-radar";
import { TimelineSection } from "./TimelineSection";

type RecentActivitySectionProps = {
  title?: string;
  items: Timeline[];
};

export function RecentActivitySection({ title = "最近の動き", items }: RecentActivitySectionProps) {
  return <TimelineSection title={title} items={items} />;
}
