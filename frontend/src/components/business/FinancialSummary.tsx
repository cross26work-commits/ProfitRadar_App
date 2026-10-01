"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
type Totals = { ordered_revenue: number | null; paid_amount: number | null; cost: number | null; gross_profit: number | null };
type Summary = { totals: Totals; customers: (Totals & {customer_id:string;customer_name:string})[]; definition: string; start: string; end: string };
type FinancialSummaryProps = { variant?: "full" | "compact" };
export function FinancialSummary({ variant = "full" }: FinancialSummaryProps) {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState(false);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [busy, setBusy] = useState(false);
  const [customPeriod, setCustomPeriod] = useState(false);
  const [validation, setValidation] = useState("");
  async function period(event?: FormEvent) {
    event?.preventDefault();
    if (busy) return;
    if (event && (!start || !end || end < start || (Date.parse(end) - Date.parse(start)) / 86400000 > 366)) {
      setValidation("開始日と終了日を367日以内で指定してください。"); return;
    }
    setValidation(""); setBusy(true); setError(false); setData(null);
    try { setData(await apiGet<Summary>(`/financials/summary${event ? `?${new URLSearchParams({start,end})}` : ''}`)); setCustomPeriod(Boolean(event)); }
    catch { setError(true); } finally { setBusy(false); }
  }
  useEffect(() => { let active = true; apiGet<Summary>("/financials/summary").then(x => { if (active) setData(x); }).catch(() => { if (active) setError(true); }); return () => { active = false; }; }, []);

  const metrics = data ? ([
    ["売上", data.totals.ordered_revenue],
    ["入金", data.totals.paid_amount],
    ["原価", data.totals.cost],
    ["粗利", data.totals.gross_profit],
  ] as const) : [];

  if (variant === "compact") {
    return <section className="rounded-3xl border border-slate-200 bg-white p-5 text-slate-900 sm:p-6" aria-labelledby="monthly-financial-summary">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
        <div><p className="text-xs font-bold tracking-wide text-slate-500">今月・日本時間（JST）</p><h2 id="monthly-financial-summary" className="mt-1 text-xl font-black tracking-tight">今月の簡易実績</h2></div>
        <Link href="/results" className="font-bold text-indigo-700 underline underline-offset-4">実績の詳細を見る</Link>
      </div>
      {error ? <p role="alert" className="mt-5 text-sm font-bold text-red-700">今月の実績を取得できません。接続状態を確認してください。</p> : !data ? <p role="status" className="mt-5 text-sm font-bold text-slate-500">今月の実績を読み込み中...</p> : <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{metrics.map(([label,value]) => <div key={label} className="min-w-0 rounded-2xl bg-slate-50 p-4"><dt className="text-sm font-bold text-slate-500">{label}</dt><dd className="mt-1 break-words text-xl font-black text-slate-950">{value === null ? "未記録・不明" : `${value.toLocaleString("ja-JP")}円`}</dd></div>)}</dl>}
    </section>;
  }

  return <section className="rounded-2xl border bg-white p-5 text-slate-900"><h2 className="text-xl font-bold">{customPeriod ? "指定期間" : "今月"}の売上・入金・原価・粗利（日本時間）</h2>
    <form onSubmit={period} className="my-4 flex flex-wrap items-end gap-3">
      <label>開始日<input aria-label="集計開始日" type="date" disabled={busy||(!data&&!error)} value={start} onChange={e=>setStart(e.target.value)} className="mt-1 block max-w-full rounded border p-2" /></label>
      <label>終了日<input aria-label="集計終了日" type="date" disabled={busy||(!data&&!error)} value={end} onChange={e=>setEnd(e.target.value)} className="mt-1 block max-w-full rounded border p-2" /></label>
      <button disabled={busy||(!data&&!error)} type="submit" className="rounded border p-2">期間を表示</button>
      <button disabled={busy||(!data&&!error)} type="button" className="rounded border p-2" onClick={()=>void period()}>今月・再取得</button>
    </form>{validation&&<p role="alert">{validation}</p>}
    {error ? <p role="alert">収益を取得できません。設定・接続状態を確認してください。</p> : !data ? <p role="status">読み込み中...</p> : <><p>{data.start} ～ {data.end}</p><dl className="my-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{metrics.map(([label,value]) => <div key={label}><dt>{label}</dt><dd className="break-words text-2xl font-bold">{value === null ? '未記録・不明' : `${value.toLocaleString('ja-JP')}円`}</dd></div>)}</dl><p className="text-sm text-slate-600">{data.definition}</p></>}
    {data&&<details className="my-4"><summary className="cursor-pointer">顧客別の集計</summary><ul className="space-y-3 pt-3">{data.customers.map(customer=><li key={customer.customer_id} className="rounded border p-3"><Link href={`/customers/${customer.customer_id}`} className="font-bold underline">{customer.customer_name}</Link><p>受注売上: {customer.ordered_revenue===null?'不明':customer.ordered_revenue.toLocaleString('ja-JP')+'円'} / 入金: {customer.paid_amount===null?'未記録':customer.paid_amount.toLocaleString('ja-JP')+'円'} / 粗利: {customer.gross_profit===null?'不明':customer.gross_profit.toLocaleString('ja-JP')+'円'}</p></li>)}</ul>{!data.customers.length&&<p>記録はありません。</p>}</details>}
    <Link href="/financials" className="mt-4 inline-block font-semibold text-indigo-700 underline">売上・入金・原価を記録する</Link></section>;
}
