import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function LeadCard({
  href = "/leads/1",
  rank,
  customer,
  subject,
  profit,
  priority,
  delay,
}: {
  href?: string;
  rank: number;
  customer: string;
  subject: string;
  profit: string;
  priority: string;
  delay: string;
}) {
  return (
    <Card className="p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-green-100 font-black text-green-700">
              {rank}
            </span>
            <div>
              <h3 className="text-lg font-black text-slate-900">{customer}</h3>
              <p className="text-sm text-slate-500">{subject}</p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge tone={priority === "高" ? "danger" : "warning"}>{priority}</Badge>
            <Badge>{delay}</Badge>
            <Badge tone="green">{profit}</Badge>
          </div>
        </div>

        <div className="flex gap-2">
          <Link href={href}>
            <Button variant="secondary">詳細</Button>
          </Link>
          <Button>返信する</Button>
        </div>
      </div>
    </Card>
  );
}
