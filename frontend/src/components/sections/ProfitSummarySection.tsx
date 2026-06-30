import type { StatItem } from "@/types/profit-radar";
import { StatsGrid } from "./StatsGrid";

type ProfitSummarySectionProps = {
  items: StatItem[];
};

export function ProfitSummarySection({ items }: ProfitSummarySectionProps) {
  return <StatsGrid items={items} />;
}
