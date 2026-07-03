import type { Lead } from "@/types/profit-radar";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LeadCard } from "@/components/business/LeadCard";

type LeadListSectionProps = {
  title: string;
  leads: Lead[];
};

export function LeadListSection({ title, leads }: LeadListSectionProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-black tracking-tight text-slate-950">{title}</h2>

      <div className="space-y-3">
        {leads.length === 0 ? (
          <EmptyState title="案件がありません" description="表示できる利益候補はありません。" />
        ) : (
          leads.map((lead) => (
            <LeadCard key={lead.id} lead={lead} />
          ))
        )}
      </div>
    </section>
  );
}
