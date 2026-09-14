-- Forward-only, isolated verification required. Existing data is not rewritten.
begin;
create table public.gmail_sync_cursors (
 company_id uuid primary key references public.companies(id), mailbox text not null,
 version bigint not null, mode text not null check(mode in ('full','delta')),
 history_id text not null, page_token text, initial_since bigint not null,
 pending_ids jsonb, pending_page jsonb,
 last_page_at timestamptz not null default now(), last_successful_sync timestamptz
);
create table public.gmail_inbound_receipts (
 company_id uuid not null references public.companies(id), mailbox text not null,
 gmail_message_id text not null, profit_event_id uuid references public.profit_events(id),
 outcome text not null, created_at timestamptz not null default now(),
 primary key(company_id,mailbox,gmail_message_id)
);
alter table public.gmail_sync_cursors enable row level security;
alter table public.gmail_inbound_receipts enable row level security;
revoke all on public.gmail_sync_cursors,public.gmail_inbound_receipts from public,anon,authenticated;
grant select on public.gmail_sync_cursors,public.gmail_inbound_receipts to service_role;

create function public.commit_gmail_inbound_page(p_company_id uuid,p_owner_id uuid,p_connection_id uuid,p_mailbox text,p_expected_version bigint,p_state jsonb,p_records jsonb)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare r jsonb; cid uuid; eid uuid; mid uuid; n integer:=0; current_version bigint; outgoing boolean;
begin
 perform 1 from public.gmail_work_locks where company_id=p_company_id and owner_id=p_owner_id and purpose='sync' for update;
 if not found then raise exception 'sync owner mismatch'; end if;
 perform 1 from public.gmail_connections where id=p_connection_id and company_id=p_company_id and lower(email)=p_mailbox and status='connected' for update;
 if not found then raise exception 'connection changed'; end if;
 select version into current_version from public.gmail_sync_cursors where company_id=p_company_id for update;
 if coalesce(current_version,0)<>p_expected_version then raise exception 'cursor version conflict'; end if;
 if jsonb_typeof(p_records)<>'array' or jsonb_array_length(p_records)>1000 then raise exception 'invalid page'; end if;
 for r in select value from jsonb_array_elements(p_records) loop
  cid:=null; eid:=null; mid:=null;
  outgoing:=coalesce(r->>'direction','incoming')='outgoing';
  if coalesce(r->>'message_id','')='' or coalesce(r->>'thread_id','')='' or coalesce(r->>'sender','')='' then raise exception 'invalid message'; end if;
  if exists(select 1 from public.gmail_inbound_receipts where company_id=p_company_id and mailbox=p_mailbox and gmail_message_id=r->>'message_id' and outcome='imported') then continue; end if;
  -- Prefer an already imported legacy message relationship before thread lookup.
  select e.id,c.id into eid,cid from public.reply_logs l
   join public.profit_events e on e.id=l.profit_event_id and e.company_id=l.company_id
   join public.customers c on c.id=e.customer_id and c.company_id=e.company_id
   where l.company_id=p_company_id and (l.gmail_message_id=r->>'message_id' or l.external_id=r->>'message_id')
    and lower(c.email)=r->>'sender' order by l.reply_at,l.id limit 1;
  -- Same-company thread AND sender. Never reassign an existing event to an unrelated sender.
  if eid is null then
  select e.id,e.customer_id into eid,cid from public.profit_events e join public.customers c on c.id=e.customer_id and c.company_id=e.company_id
   where e.company_id=p_company_id and e.gmail_thread_id=r->>'thread_id' and lower(c.email)=r->>'sender' order by e.created_at,e.id limit 1;
  end if;
  if eid is null and not coalesce((r->>'candidate')::boolean,false) then
   insert into public.gmail_inbound_receipts values(p_company_id,p_mailbox,r->>'message_id',null,'not_target',now()) on conflict do nothing; continue;
  end if;
  -- Serialize address-based find/create with all pages for this company; retain existing duplicates for audit.
  perform pg_advisory_xact_lock(hashtextextended(p_company_id::text||':'||(r->>'sender'),73));
  if cid is null then
   select id into cid from public.customers where company_id=p_company_id and lower(email)=r->>'sender' order by created_at,id limit 1;
   if cid is null then insert into public.customers(company_id,name,email) values(p_company_id,left(r->>'sender_name',200),r->>'sender') returning id into cid; end if;
  end if;
  select id into mid from public.messages where company_id=p_company_id and customer_id=cid
   and channel='gmail' and direction=case when outgoing then 'outgoing' else 'incoming' end and external_id=r->>'message_id'
   and lower(sender)=case when outgoing then p_mailbox else r->>'sender' end order by received_at,id limit 1;
  if mid is null then
   insert into public.messages(company_id,customer_id,direction,channel,sender,recipient,subject,body,external_id,thread_id,received_at)
   values(p_company_id,cid,case when outgoing then 'outgoing' else 'incoming' end,'gmail',case when outgoing then p_mailbox else r->>'sender' end,case when outgoing then r->>'sender' else p_mailbox end,r->>'subject',left(r->>'body',30000),r->>'message_id',r->>'thread_id',(r->>'received_at')::timestamptz) returning id into mid;
  end if;
  if eid is null then
   insert into public.profit_events(company_id,customer_id,source_message_id,title,gmail_thread_id,next_action,category)
    values(p_company_id,cid,mid,coalesce(nullif(r->>'subject',''),'新規問い合わせ'),r->>'thread_id','元メールを確認して返信要否を判断','inquiry') returning id into eid;
  end if;
  -- Legacy receipt might already exist; repair its missing timeline rather than duplicating it.
  if not outgoing and not exists(select 1 from public.reply_logs where company_id=p_company_id and (gmail_message_id=r->>'message_id' or external_id=r->>'message_id')) then
   insert into public.reply_logs(company_id,customer_id,profit_event_id,message_id,channel,reply_body,reply_at,external_id,thread_id,gmail_message_id,gmail_thread_id)
    values(p_company_id,cid,eid,mid,'gmail',left(r->>'body',30000),(r->>'received_at')::timestamptz,r->>'message_id',r->>'thread_id',r->>'message_id',r->>'thread_id');
  end if;
  if not exists(select 1 from public.timeline where company_id=p_company_id and event_type=case when outgoing then 'gmail_sent_imported' else 'gmail_reply_detected' end and metadata->>'gmail_message_id'=r->>'message_id') then
   insert into public.timeline(company_id,customer_id,profit_event_id,event_type,channel,title,description,occurred_at,metadata)
    values(p_company_id,cid,eid,case when outgoing then 'gmail_sent_imported' else 'gmail_reply_detected' end,'gmail',case when outgoing then 'Gmail送信済み商談・要確認' else 'Gmail受信・要確認' end,left(r->>'body',500),(r->>'received_at')::timestamptz,jsonb_build_object('gmail_message_id',r->>'message_id','gmail_thread_id',r->>'thread_id','from_email',case when outgoing then p_mailbox else r->>'sender' end,'subject',r->>'subject','reason',r->>'reason','suppressed',r->'suppressed'));
  end if;
  update public.profit_events set last_gmail_message_id=case when outgoing then last_gmail_message_id else r->>'message_id' end,next_action=case when coalesce((r->>'suppressed')::boolean,false) then '連絡停止・受信内容を確認（自動追客禁止）' when outgoing then '送信済み・返信待ち。元メールと経過日数を確認' else '元メールを確認して返信要否を判断' end
   where id=eid and company_id=p_company_id and not exists(
    select 1 from public.messages m where m.company_id=p_company_id and m.customer_id=cid
     and m.thread_id=r->>'thread_id' and m.direction in ('incoming','outgoing') and m.received_at>(r->>'received_at')::timestamptz)
    and not (outgoing and next_action like '連絡停止%');
  insert into public.gmail_inbound_receipts values(p_company_id,p_mailbox,r->>'message_id',eid,'imported',now())
   on conflict(company_id,mailbox,gmail_message_id) do update set profit_event_id=excluded.profit_event_id,outcome='imported';
  n:=n+1;
 end loop;
 insert into public.gmail_sync_cursors(company_id,mailbox,version,mode,history_id,page_token,initial_since,last_successful_sync)
 values(p_company_id,p_mailbox,p_expected_version+1,p_state->>'mode',p_state->>'history_id',p_state->>'page_token',(p_state->>'initial_since')::bigint,
  case when coalesce((p_state->>'caught_up')::boolean,false) then now() end)
 on conflict(company_id) do update set mailbox=excluded.mailbox,version=excluded.version,mode=excluded.mode,history_id=excluded.history_id,page_token=excluded.page_token,initial_since=excluded.initial_since,last_page_at=now(),last_successful_sync=case when public.gmail_sync_cursors.mailbox<>excluded.mailbox then excluded.last_successful_sync else coalesce(excluded.last_successful_sync,public.gmail_sync_cursors.last_successful_sync) end;
 update public.gmail_sync_cursors set pending_ids=nullif(p_state->'pending_ids','null'::jsonb),pending_page=nullif(p_state->'pending_page','null'::jsonb) where company_id=p_company_id;
 return jsonb_build_object('inserted',n,'version',p_expected_version+1);
end $$;
revoke all on function public.commit_gmail_inbound_page(uuid,uuid,uuid,text,bigint,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.commit_gmail_inbound_page(uuid,uuid,uuid,text,bigint,jsonb,jsonb) to service_role;
commit;
