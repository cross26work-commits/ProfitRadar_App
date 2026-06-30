import Link from "next/link";
import type { Lead } from "@/types/profit-radar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function LeadCard({ lead }: { lead: Lead }) {
  return (
    <Card className="p-5 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-green-100 text-sm font-black text-green-700">
              {lead.rank}
            </div>
            <div className="min-w-0">
              <p className="truncate text-lg font-black text-slate-950">{lead.customer}</p>
              <p className="mt-1 truncate text-sm font-medium text-slate-500">{lead.subject}</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Badge tone="green">{lead.profit}</Badge>
            <Badge tone="warning">{lead.priority}</Badge>
            <Badge>{lead.delay}</Badge>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <Link href={lead.href ?? "/leads/1"}>
            <Button variant="secondary">詳細</Button>
          </Link>
          <Link href="/reply">
            <Button>返信する</Button>
          </Link>
        </div>
      </div>
    </Card>
  );
}
