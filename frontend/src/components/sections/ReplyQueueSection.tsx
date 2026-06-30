import type { Lead } from "@/types/profit-radar";
import { LeadListSection } from "./LeadListSection";

type ReplyQueueSectionProps = {
  title?: string;
  leads: Lead[];
};

export function ReplyQueueSection({ title = "返信優先案件", leads }: ReplyQueueSectionProps) {
  return <LeadListSection title={title} leads={leads} />;
}
