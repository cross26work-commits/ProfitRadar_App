import { StatCard } from "@/components/ui/StatCard";

type StatItem = {
  label: string;
  value: string;
  sub: string;
  tone?: string;
};

type StatsGridProps = {
  items: StatItem[];
};

export function StatsGrid({ items }: StatsGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <StatCard
          key={item.label}
          label={item.label}
          value={item.value}
          sub={item.sub}
          tone={item.tone}
        />
      ))}
    </div>
  );
}
