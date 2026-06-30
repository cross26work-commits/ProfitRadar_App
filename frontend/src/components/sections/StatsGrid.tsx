import type { StatItem } from "@/types/profit-radar";
import { StatCard } from "@/components/ui/StatCard";

type StatsGridProps = {
  items: StatItem[];
};

export function StatsGrid({ items }: StatsGridProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
      {items.map((item) => (
        <StatCard key={item.label} {...item} />
      ))}
    </section>
  );
}
