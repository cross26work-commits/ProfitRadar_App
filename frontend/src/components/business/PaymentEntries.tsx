"use client";
import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPost, ApiError } from "@/lib/api";
type Payment = { id: string; amount: number; paid_at: string; voided_at: string | null };
export function PaymentEntries({eventId,onSaved}:{eventId:string;onSaved:()=>void}) {
  const [rows,setRows]=useState<Payment[]>([]),[busy,setBusy]=useState(true),[error,setError]=useState("");
  const [amount,setAmount]=useState(""),[date,setDate]=useState("");
  const storageKey=`payment-operation:${eventId}`;
  async function reload() {
    const value=await apiGet<{payments:Payment[]}>(`/financials/${encodeURIComponent(eventId)}`);
    setRows(value.payments);
    if(value.payments.some(row=>row.id===sessionStorage.getItem(storageKey)))sessionStorage.removeItem(storageKey);
  }
  useEffect(()=>{let active=true;apiGet<{payments:Payment[]}>(`/financials/${encodeURIComponent(eventId)}`).then(value=>{
    if(active){setRows(value.payments);if(value.payments.some(row=>row.id===sessionStorage.getItem(storageKey)))sessionStorage.removeItem(storageKey);}
  }).catch(()=>{if(active)setError("入金明細を取得できません。");}).finally(()=>{if(active)setBusy(false);});return()=>{active=false;};},[eventId,storageKey]);
  async function add(event:FormEvent) {
    event.preventDefault();if(busy)return;setBusy(true);setError("");
    try {
      const operation=sessionStorage.getItem(storageKey)||crypto.randomUUID();
      sessionStorage.setItem(storageKey,operation); // UUID only, never financial input or secrets.
      await apiPost(`/financials/${encodeURIComponent(eventId)}/payments`,{operation_id:operation,amount:Number(amount),paid_at:`${date}T00:00:00+09:00`});
      sessionStorage.removeItem(storageKey);setAmount("");setDate("");await reload();onSaved();
    }catch(e){setError(e instanceof ApiError?e.message:"保存結果を確認できません。同じ内容で再試行してください。操作IDは保持しています。");}finally{setBusy(false);}
  }
  async function voidEntry(id:string) {
    const reason=window.prompt("取消理由（200文字以内）。元明細と操作履歴は残ります。");
    if(!reason?.trim()||reason.length>200||busy)return;setBusy(true);setError("");
    try{await apiPost(`/financials/payments/${id}/void`,{reason});await reload();onSaved();}
    catch{setError("取消結果を確認できません。再読み込みで確認してください。");}finally{setBusy(false);}
  }
  return <section className="space-y-4 rounded-2xl border bg-white p-5"><h2 className="text-xl font-bold">追加入金・分割入金</h2>
    <p className="text-sm">単一入金とは別の追加入金です。同じ入金を両方に登録しないでください。</p>
    {error&&<p role="alert">{error}</p>}{busy&&<p role="status">処理中...</p>}
    <form onSubmit={add} className="flex flex-wrap items-end gap-3">
      <label>追加入金額（円）<input required type="number" min="1" max="1000000000000" step="1" value={amount} disabled={busy} onChange={e=>setAmount(e.target.value)} className="block w-full rounded border p-2"/></label>
      <label>追加入金日<input required type="date" value={date} disabled={busy} onChange={e=>setDate(e.target.value)} className="block max-w-full rounded border p-2"/></label>
      <button disabled={busy} className="rounded border p-3">入金明細を追加</button>
    </form>
    {!busy&&!rows.length&&<p>追加入金明細はありません。</p>}
    <ul className="space-y-2">{rows.map(row=><li key={row.id} className="flex flex-wrap items-center justify-between gap-2 border-b py-2"><span>{new Date(row.paid_at).toLocaleDateString("ja-JP",{timeZone:"Asia/Tokyo"})} / {row.amount.toLocaleString("ja-JP")}円 {row.voided_at?"（取消済み）":""}</span>{!row.voided_at&&<button disabled={busy} onClick={()=>void voidEntry(row.id)} className="rounded border p-2">明細を取消</button>}</li>)}</ul>
  </section>;
}
