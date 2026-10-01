/* Test bundle only: no production imports of this file, no external transport. */
import React from 'react';
export const state=new URLSearchParams(location.search).get('state')||'normal';
export const usePathname=()=>new URLSearchParams(location.search).get('page')||'/dashboard';
export const useSearchParams=()=>new URLSearchParams(location.search);
export const href=(path)=>{const target=new URL(path,'http://fixture.invalid');const params=new URLSearchParams({page:target.pathname,state});for(const [key,value] of target.searchParams)params.set(key,value);return `/?${params}`;};
export const useRouter=()=>({push:p=>location.assign(href(p)),replace:p=>location.assign(href(p)),refresh:()=>location.reload()});
export default function Link({href:target,children,...props}){return <a href={href(target)} {...props}>{children}</a>;}
export const useAuth=()=>({loading:false,profile:state==='unauthenticated'?null:{name:'検証担当（架空）',companyName:'UI検証株式会社（架空）',plan:'trial'},session:state==='unauthenticated'?null:{user:{email:'fixture@example.invalid',user_metadata:{}}}});
export const supabase={auth:{signOut:async()=>({error:null})}};
export const deleteCurrentAccount=async()=>{throw new Error('Fixture: deletion disabled');};
export class ApiError extends Error{constructor(status){super(status===429?'利用上限に達しました。':status===402?'試用・契約期間をご確認ください。':'一時的に利用できません。');this.status=status;}}
const event='00000000-0000-4000-8000-000000000001',customer='00000000-0000-4000-8000-000000000002';
const action={event_id:event,customer_id:customer,company_id:'fixture',title:'E2E専用・見積相談',customer_name:'架空のテスト顧客',estimated_profit:0,recoverable_profit:0,risk_level:'medium',category:'follow_up',priority_score:1,reason:'根拠メールを確認してください',next_action:'内容を確認して返信',created_at:'2026-09-10T00:00:00Z'};
const draft=()=>({customer:{id:customer,name:action.customer_name,email:'recipient@example.invalid'},event:{title:action.title,customer_id:customer},subject:'Re: E2E専用・見積相談',draft:sessionStorage.getItem('fixture-draft')||'お問い合わせありがとうございます。条件を確認し、改めてご連絡いたします。',send_status:state==='unknown'?'unknown':sessionStorage.getItem('fixture-send')||'',draft_provider:'保存済みfixture',analysis:{amount:null,reason:'架空メールの表示確認',next_action:'条件を確認',confidence:'low'}});
const totals={ordered_revenue:100000,paid_amount:30000,cost:40000,gross_profit:60000,confirmed_count:1};
export async function apiGet(path){
 if(state==='loading')return new Promise(()=>{});
 if(state==='error')throw new ApiError(503);
 const empty=state==='empty',items=empty?[]:[action];
 if(path==='/dashboard/home')return {summary:{top_action_count:items.length,total_estimated_profit:0,total_recoverable_profit:0,high_risk_count:0},top_actions:items,reply_queue:items,risks:[],recent_timeline:[],ai_message:'fixture'};
 if(path==='/results/summary')return {actual_profit:0,estimated_profit:0,action_count:0,recovery_rate:0,message:'架空の表示確認'};
 if(path==='/results/insights')return {items:[]};
 if(path==='/sales-forecast/summary')return {forecast:{conservative:0,standard:0,aggressive:0},message:'参考値・fixture'};
 if(path==='/self-evaluation/summary')return {count:0,success_count:0,avg_accuracy:0,message:'fixture'};
 if(path==='/customers')return {items:empty?[]:[{id:customer,name:action.customer_name,leads:1,profit:0,last:'未確定',href:`/customers/${customer}`}]};
 if(path==='/leads')return {items:empty?[]:[{id:event,customer:action.customer_name,subject:action.title,priority:'medium',status:'open',estimated_profit:0,recoverable_profit:0,delay_days:0,href:`/leads/${event}`}]};
 if(path.startsWith('/financials/summary'))return {start:'2026-09-10',end:'2026-09-10',totals:empty?{ordered_revenue:null,paid_amount:null,cost:null,gross_profit:null}:totals,customers:empty?[]:[{customer_id:customer,customer_name:action.customer_name,...totals}]};
 if(path.startsWith('/financials/'))return JSON.parse(sessionStorage.getItem(`fixture:${path}`)||'null')||{version:0,payments:[],...totals,confirmed_at:'2026-09-10T00:00:00+09:00',paid_at:'2026-09-10T00:00:00+09:00'};
 if(path.startsWith('/gmail/replies'))return {count:items.length,items:empty?[]:[{id:'fixture',profit_event_id:event,customer_id:customer,customer_name:action.customer_name,customer_email:'recipient@example.invalid',subject:action.title,body:'E2E専用の架空メールです。',received_at:action.created_at,event_title:action.title,next_action:'条件を確認',estimated_profit:0,risk_level:'medium'}]};
 if(path.startsWith('/reply/'))return draft();
 if(path==='/gmail/status')return {connected:state!=='disconnected',connection:state==='disconnected'?null:{email:'fixture@example.invalid',created_at:action.created_at},sync:{mode:'delta',last_successful_sync:action.created_at},last_run:{status:state==='sync-failure'?'failed':'succeeded'}};
 if(path==='/billing/status'){const status=state==='expired'?'trial_expired':state==='payment-failed'?'past_due':state==='trialing'?'trialing':'trial_pending';return {status,allowed:status==='trialing',trial_ends_at:'2026-09-24T00:00:00Z',paid_until:null,test_mode:true,trial_days:7,monthly_price_jpy:19800,today_due_jpy:0,first_billing_at:'2026-09-24T00:00:00Z',automatic_trial_charge:true,automatic_renewal:true};}
 throw new Error(`Unimplemented fixture GET: ${path}`);
}
export async function apiPost(path,body){
 if(state==='limit')throw new ApiError(429);
 if(state==='expired'||state==='payment-failed')throw new ApiError(402);
 if(path.endsWith('/reconcile'))return {status:'unknown',message:'照合fixture：不明を維持。送信なし'};
 if(path.endsWith('/draft')){if(typeof body.body!=='string')throw new Error('Fixture body contract mismatch');sessionStorage.setItem('fixture-draft',body.body);return {saved:true};}
 if(path.endsWith('/generate'))return draft();
 if(path.endsWith('/send')){sessionStorage.setItem('fixture-send','sent');return {sent:true,status:'sent'};}
 if(path==='/gmail/check-replies'){if(state==='sync-failure')throw new ApiError(503);return {count:0,checked:true};}
 throw new Error('Fixture: side effect blocked');
}
export const apiPut=async(path,body)=>{if(!path.startsWith('/financials/'))throw new Error('Fixture write blocked');if(state==='expired')throw new ApiError(402);sessionStorage.setItem(`fixture:${path}`,JSON.stringify({...body,version:body.expected_version+1,payments:[]}));return {version:body.expected_version+1};};
export const apiDelete=async()=>{throw new Error('Fixture: deletion blocked');};
