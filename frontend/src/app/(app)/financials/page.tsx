"use client";
import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPut } from "@/lib/api";
import { FinancialSummary } from "@/components/business/FinancialSummary";
import { PaymentEntries } from "@/components/business/PaymentEntries";
const fields = [['expected_revenue','見込売上'],['ordered_revenue','受注売上'],['paid_amount','入金額'],['cost','原価']] as const;
export default function FinancialsPage() {
  const [events,setEvents]=useState<{id:string;title?:string;subject?:string}[]>([]);
  const [event,setEvent]=useState(''); const [version,setVersion]=useState(0);
  const [occurredAt,setOccurredAt]=useState<string|null>(null);
  const [values,setValues]=useState<Record<string,string>>({}); const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState(''); const [refresh,setRefresh]=useState(0);
  useEffect(()=>{apiGet<{items:{id:string;title?:string;subject?:string}[]}>("/leads").then(x=>{setEvents(x.items);const requested=new URLSearchParams(window.location.search).get('event_id');if(requested)void choose(requested);}).catch(()=>setMessage('案件を取得できません。再読み込みしてください。'));},[]);
  async function choose(id:string) {
    setEvent(id);setValues({});setOccurredAt(null);setBusy(true);setMessage('');
    try { const row=await apiGet<Record<string,unknown>>(`/financials/${encodeURIComponent(id)}`);setEvents(previous=>previous.some(item=>item.id===id)?previous:[{id},...previous]);setVersion(Number(row.version));setOccurredAt(typeof row.occurred_at==='string'?row.occurred_at:null);const next:Record<string,string>={};for(const [key] of fields)next[key]=row[key]==null?'':String(row[key]);for(const key of ['confirmed_at','paid_at'])next[key]=row[key]?new Date(String(row[key])).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'}):'';setValues(next); }
    catch {setEvent('');setMessage('記録を取得できません。再度選択してください。');}finally{setBusy(false);}
  }
  async function save(e:FormEvent) {
    e.preventDefault();if(!event||busy)return;setBusy(true);setMessage('');
    const payload:Record<string,unknown>={expected_version:version,occurred_at:occurredAt||new Date().toISOString()};
    for(const [key] of fields)payload[key]=values[key]?.trim()?Number(values[key]):null;
    for(const key of ['confirmed_at','paid_at'])payload[key]=values[key]?`${values[key]}T00:00:00+09:00`:null;
    try {const row=await apiPut<{version:number}>(`/financials/${encodeURIComponent(event)}`,payload);setVersion(row.version);setOccurredAt(String(payload.occurred_at));setMessage('保存しました。');setRefresh(x=>x+1);}catch{setMessage('保存を確認できません。再読込して記録を確認してください。競合時は再選択してください。');}finally{setBusy(false);}
  }
  return <main className="space-y-6"><h1 className="text-2xl font-bold">売上・入金・原価の記録</h1><FinancialSummary key={refresh}/><p>空欄は不明です。旧「実利益」の値は自動移行しません。受注日と入金日を区別して入力してください。</p>
    <label className="block">対象案件<select className="mt-2 block w-full rounded border p-3" value={event} disabled={busy} onChange={e=>{if(e.target.value)void choose(e.target.value);else setEvent('');}}><option value="">選択してください</option>{events.map(x=><option key={x.id} value={x.id}>{x.subject||x.title||x.id}</option>)}</select></label>
    {!events.length&&<p>案件がない場合は、同期状態とLeadsを確認してください。</p>}
    {event&&<PaymentEntries key={event} eventId={event} onSaved={()=>setRefresh(x=>x+1)}/>}
    <form onSubmit={save} className="grid gap-4 rounded-2xl border bg-white p-5 sm:grid-cols-2">{fields.map(([key,label])=><label key={key}>{label}（円）<input type="number" min="0" max="1000000000000" step="1" className="mt-1 block w-full rounded border p-3" disabled={busy||!event} value={values[key]||''} onChange={e=>setValues(v=>({...v,[key]:e.target.value}))}/></label>)}{([['confirmed_at','受注確定日'],['paid_at','入金日']] as const).map(([key,label])=><label key={key}>{label}<input type="date" className="mt-1 block w-full min-w-0 rounded border p-3" disabled={busy||!event} value={values[key]||''} onChange={e=>setValues(v=>({...v,[key]:e.target.value}))}/></label>)}<button disabled={busy||!event} className="rounded bg-indigo-700 p-3 font-bold text-white disabled:opacity-50">{busy?'処理中...':'確認した金額を保存'}</button></form><p role="status">{message}</p></main>;
}
