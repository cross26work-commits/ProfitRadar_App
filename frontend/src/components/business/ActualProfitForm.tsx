import Link from "next/link";

/** Legacy import compatibility; confirmed figures now live in financial_records. */
export function ActualProfitForm({ eventId }: { eventId: string | number; defaultValue?: number }) {
  return <div className="space-y-3 rounded-xl border bg-white p-4">
    <p>確定した売上・入金・原価は、案件の財務記録で区別して保存します。旧「実利益」欄には保存しません。</p>
    <Link href={`/financials?event_id=${encodeURIComponent(String(eventId))}`} className="inline-block rounded bg-indigo-700 px-4 py-2 font-semibold text-white">
      この案件の財務記録を開く
    </Link>
  </div>;
}
