import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function CustomerCard({
  href = "/customers/1",
  name,
  leads,
  profit,
  last,
}: {
  href?: string;
  name: string;
  leads: number;
  profit: string;
  last: string;
}) {
  return (
    <Card className="p-5">
      <h3 className="text-lg font-black text-slate-900">{name}</h3>
      <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-slate-500">案件数</p>
          <p className="mt-1 font-black">{leads}</p>
        </div>
        <div>
          <p className="text-slate-500">見込利益</p>
          <p className="mt-1 font-black text-green-600">{profit}</p>
        </div>
        <div>
          <p className="text-slate-500">最終連絡</p>
          <p className="mt-1 font-black">{last}</p>
        </div>
      </div>
      <div className="mt-5">
        <Link href={href}>
          <Button variant="secondary">顧客詳細を見る</Button>
        </Link>
      </div>
    </Card>
  );
}
