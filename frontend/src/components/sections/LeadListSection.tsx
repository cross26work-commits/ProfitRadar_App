import { LeadCard } from "@/components/business/LeadCard";
import { EmptyState } from "@/components/feedback/EmptyState";

type Lead = {
  href?: string;
  rank: number;
  customer: string;
  subject: string;
  profit: string;
  priority: string;
  delay: string;
};

type LeadListSectionProps = {
  title: string;
  leads: Lead[];
};

export function LeadListSection({ title, leads }: LeadListSectionProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-base font-black text-slate-900">{title}</h2>

      {leads.length === 0 ? (
        <EmptyState title="案件がありません" description="表示できる利益候補はまだありません。" />
      ) : (
        <div className="space-y-3">
          {leads.map((lead) => (
            <LeadCard key={`${lead.rank}-${lead.customer}`} {...lead} />
          ))}
        </div>
      )}
    </section>
  );
}
