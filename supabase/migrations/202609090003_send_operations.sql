-- Review/apply only to isolated schema first. Never automatically resend unknown.
begin;
create table public.gmail_send_operations (
  company_id uuid not null references public.companies(id),
  profit_event_id uuid not null references public.profit_events(id),
  customer_id uuid not null references public.customers(id),
  operation_id text not null,
  request_hash text not null,
  status text not null check(status in ('sending','unknown','sent')),
  recipient text not null,
  subject text not null,
  body text not null,
  gmail_message_id text,
  gmail_thread_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(company_id,operation_id)
);
create unique index gmail_send_one_unresolved_event on public.gmail_send_operations(company_id,profit_event_id) where status in ('sending','unknown');
alter table public.gmail_send_operations enable row level security;
revoke all on public.gmail_send_operations from public,anon,authenticated;
grant select,insert,update on public.gmail_send_operations to service_role;

create function public.finalize_gmail_send(p_company_id uuid,p_operation_id text,p_message_id text,p_thread_id text)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare op public.gmail_send_operations%rowtype; cid uuid;
begin
  select * into strict op from public.gmail_send_operations
    where company_id=p_company_id and operation_id=p_operation_id for update;
  if op.status='sent' then
    if op.gmail_message_id<>p_message_id then raise exception 'provider identity conflict'; end if;
    return true;
  end if;
  if coalesce(p_message_id,'')='' or coalesce(p_thread_id,'')='' then raise exception 'provider identity missing'; end if;
  select customer_id into strict cid from public.profit_events where id=op.profit_event_id and company_id=p_company_id;
  if cid<>op.customer_id then raise exception 'event customer changed; reconciliation required'; end if;
  if not exists(select 1 from public.customers where id=cid and company_id=p_company_id) then raise exception 'tenant mismatch'; end if;
  insert into public.reply_logs(company_id,customer_id,profit_event_id,channel,reply_body,gmail_message_id,gmail_thread_id,external_id,thread_id)
    values(p_company_id,cid,op.profit_event_id,'gmail',op.body,p_message_id,p_thread_id,p_message_id,p_thread_id);
  insert into public.timeline(company_id,customer_id,profit_event_id,event_type,channel,title,description,metadata)
    values(p_company_id,cid,op.profit_event_id,'reply_sent_gmail','gmail','Gmail返信を送信',left(op.body,500),jsonb_build_object('gmail_message_id',p_message_id,'gmail_thread_id',p_thread_id,'operation_id',p_operation_id));
  update public.profit_events set gmail_thread_id=p_thread_id,last_gmail_message_id=p_message_id where company_id=p_company_id and id=op.profit_event_id;
  update public.gmail_send_operations set status='sent',gmail_message_id=p_message_id,gmail_thread_id=p_thread_id,updated_at=now() where company_id=p_company_id and operation_id=p_operation_id;
  return true;
end $$;
revoke all on function public.finalize_gmail_send(uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.finalize_gmail_send(uuid,text,text,text) to service_role;
commit;
