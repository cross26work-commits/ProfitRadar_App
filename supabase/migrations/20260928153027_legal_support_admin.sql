begin;

create table public.company_business_consents (
  company_id uuid primary key references public.companies(id) on delete cascade,
  user_id uuid not null,
  terms_version text not null,
  accepted_at timestamptz not null default now()
);

create table public.billing_checkout_consents (
  company_id uuid primary key references public.companies(id) on delete cascade,
  user_id uuid not null,
  terms_version text not null,
  business_use_confirmed boolean not null check (business_use_confirmed),
  automatic_renewal_confirmed boolean not null check (automatic_renewal_confirmed),
  refund_policy_confirmed boolean not null check (refund_policy_confirmed),
  trial_days integer not null check (trial_days = 7),
  monthly_price_jpy integer not null check (monthly_price_jpy = 19800),
  accepted_at timestamptz not null default now()
);

create table public.support_requests (
  id uuid primary key default gen_random_uuid(),
  public_request_id text not null unique check (public_request_id ~ '^PR-[0-9]{8}-[A-F0-9]{12}$'),
  requester_user_id uuid,
  company_id uuid references public.companies(id) on delete set null,
  requester_name text not null check (char_length(requester_name) between 1 and 100),
  requester_email text not null check (char_length(requester_email) between 3 and 320),
  company_name text check (company_name is null or char_length(company_name) <= 200),
  category text not null check (category in (
    'general','technical','billing','cancellation','refund',
    'commercial_disclosure','privacy_deletion','other'
  )),
  subject text not null check (char_length(subject) between 1 and 200),
  body text not null check (char_length(body) between 10 and 5000),
  status text not null default 'unhandled' check (status in ('unhandled','in_progress','completed')),
  priority text not null default 'normal' check (priority in ('low','normal','high','urgent')),
  abuse_key text not null check (char_length(abuse_key) = 64),
  legal_disclosure boolean generated always as (category = 'commercial_disclosure') stored,
  started_at timestamptz,
  answered_at timestamptz,
  last_admin_actor uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.support_messages (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null references public.support_requests(id) on delete cascade,
  direction text not null check (direction in ('requester','admin','system')),
  subject text not null check (char_length(subject) between 1 and 200),
  body text not null check (char_length(body) between 1 and 10000),
  recipient_email text check (recipient_email is null or char_length(recipient_email) between 3 and 320),
  thread_reference text,
  sent_at timestamptz,
  delivery_status text not null check (delivery_status in ('received','sending','sent','suppressed','unknown','failed')),
  provider_message_id text,
  failure_reason text,
  idempotency_key text unique,
  admin_actor uuid,
  created_at timestamptz not null default now()
);

create table public.support_internal_notes (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null references public.support_requests(id) on delete cascade,
  body text not null check (char_length(body) between 1 and 5000),
  admin_actor uuid not null,
  created_at timestamptz not null default now()
);

create table public.support_audit_logs (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null references public.support_requests(id) on delete cascade,
  action text not null check (char_length(action) between 1 and 100),
  admin_actor uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index support_requests_status_created_idx on public.support_requests(status, created_at desc);
create index support_requests_category_created_idx on public.support_requests(category, created_at desc);
create index support_requests_abuse_created_idx on public.support_requests(abuse_key, created_at desc);
create index support_messages_request_created_idx on public.support_messages(request_id, created_at);
create index support_notes_request_created_idx on public.support_internal_notes(request_id, created_at);
create index support_audit_request_created_idx on public.support_audit_logs(request_id, created_at);

alter table public.company_business_consents enable row level security;
alter table public.billing_checkout_consents enable row level security;
alter table public.support_requests enable row level security;
alter table public.support_messages enable row level security;
alter table public.support_internal_notes enable row level security;
alter table public.support_audit_logs enable row level security;

revoke all on public.company_business_consents, public.billing_checkout_consents,
  public.support_requests, public.support_messages, public.support_internal_notes,
  public.support_audit_logs from public, anon, authenticated, service_role;
grant select, insert, update on public.company_business_consents, public.billing_checkout_consents to service_role;
grant select, insert, update on public.support_requests, public.support_messages to service_role;
grant select, insert on public.support_internal_notes, public.support_audit_logs to service_role;

create function public.support_request_touch()
returns trigger language plpgsql set search_path=pg_catalog,pg_temp as $$
begin
  new.updated_at := now();
  if new.status = 'in_progress' and old.status is distinct from new.status then
    new.started_at := coalesce(new.started_at, now());
  end if;
  if new.status = 'completed' and old.status is distinct from new.status then
    new.answered_at := coalesce(new.answered_at, now());
  end if;
  return new;
end $$;
revoke all on function public.support_request_touch() from public, anon, authenticated, service_role;
create trigger support_requests_touch before update on public.support_requests
for each row execute function public.support_request_touch();

create function public.create_support_request(
  p_public_request_id text, p_requester_user_id uuid, p_company_id uuid,
  p_requester_name text, p_requester_email text, p_company_name text,
  p_category text, p_subject text, p_body text, p_abuse_key text
)
returns table(id uuid, public_request_id text, created_at timestamptz)
language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare created public.support_requests%rowtype;
begin
  if p_public_request_id !~ '^PR-[0-9]{8}-[A-F0-9]{12}$'
    or char_length(p_abuse_key) <> 64 then
    raise exception 'invalid request metadata';
  end if;
  perform pg_advisory_xact_lock(hashtextextended(p_abuse_key, 0));
  if (select count(*) from public.support_requests
      where abuse_key = p_abuse_key and created_at >= now() - interval '1 hour') >= 5 then
    raise exception 'rate limit exceeded' using errcode = 'P0001';
  end if;
  insert into public.support_requests(
    public_request_id, requester_user_id, company_id, requester_name,
    requester_email, company_name, category, subject, body, abuse_key
  ) values (
    p_public_request_id, p_requester_user_id, p_company_id, trim(p_requester_name),
    lower(trim(p_requester_email)), nullif(trim(p_company_name), ''),
    p_category, trim(p_subject), trim(p_body), p_abuse_key
  ) returning * into created;
  insert into public.support_messages(request_id, direction, subject, body, delivery_status)
  values(created.id, 'requester', created.subject, created.body, 'received');
  insert into public.support_audit_logs(request_id, action, metadata)
  values(created.id, 'request_created', jsonb_build_object('category', created.category));
  return query select created.id, created.public_request_id, created.created_at;
end $$;

create function public.update_support_request_admin(
  p_request_id uuid, p_status text, p_priority text, p_actor uuid
)
returns setof public.support_requests
language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare before_status text; before_priority text;
begin
  select status, priority into strict before_status, before_priority
  from public.support_requests where id = p_request_id for update;
  update public.support_requests set status=p_status, priority=p_priority, last_admin_actor=p_actor
  where id=p_request_id;
  insert into public.support_audit_logs(request_id, action, admin_actor, metadata)
  values(p_request_id, 'request_updated', p_actor,
    jsonb_build_object('from_status',before_status,'to_status',p_status,
                       'from_priority',before_priority,'to_priority',p_priority));
  return query select * from public.support_requests where id=p_request_id;
end $$;

create function public.add_support_note_admin(p_request_id uuid, p_body text, p_actor uuid)
returns uuid language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare note_id uuid;
begin
  if not exists(select 1 from public.support_requests where id=p_request_id) then
    raise exception 'support request not found';
  end if;
  insert into public.support_internal_notes(request_id,body,admin_actor)
  values(p_request_id,trim(p_body),p_actor) returning id into note_id;
  insert into public.support_audit_logs(request_id,action,admin_actor)
  values(p_request_id,'internal_note_added',p_actor);
  return note_id;
end $$;

create function public.reserve_support_reply(
  p_request_id uuid, p_subject text, p_body text, p_actor uuid, p_idempotency_key text
)
returns table(message_id uuid, created boolean, recipient_email text, delivery_status text, thread_reference text)
language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare existing public.support_messages%rowtype; req public.support_requests%rowtype; message_uuid uuid; thread_id text;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_idempotency_key, 0));
  select * into existing from public.support_messages where idempotency_key=p_idempotency_key;
  if found then
    return query select existing.id,false,existing.recipient_email,existing.delivery_status,existing.thread_reference;
    return;
  end if;
  select * into strict req from public.support_requests where id=p_request_id for update;
  select provider_message_id into thread_id from public.support_messages
  where request_id=p_request_id and provider_message_id is not null
  order by created_at desc limit 1;
  insert into public.support_messages(request_id,direction,subject,body,recipient_email,
    thread_reference,delivery_status,idempotency_key,admin_actor)
  values(p_request_id,'admin',trim(p_subject),trim(p_body),req.requester_email,
    thread_id,'sending',p_idempotency_key,p_actor) returning id into message_uuid;
  insert into public.support_audit_logs(request_id,action,admin_actor)
  values(p_request_id,'reply_reserved',p_actor);
  return query select message_uuid,true,req.requester_email,'sending'::text,thread_id;
end $$;

create function public.finalize_support_reply(
  p_message_id uuid, p_status text, p_provider_message_id text,
  p_failure_reason text, p_actor uuid
)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare request_uuid uuid; changed integer;
begin
  if p_status not in ('sent','suppressed','unknown','failed') then
    raise exception 'invalid delivery status';
  end if;
  update public.support_messages set delivery_status=p_status,
    provider_message_id=nullif(p_provider_message_id,''), failure_reason=nullif(p_failure_reason,''),
    sent_at=case when p_status in ('sent','suppressed') then now() else null end
  where id=p_message_id and delivery_status='sending'
  returning request_id into request_uuid;
  get diagnostics changed=row_count;
  if changed=0 then return false; end if;
  insert into public.support_audit_logs(request_id,action,admin_actor,metadata)
  values(request_uuid,'reply_'||p_status,p_actor,jsonb_build_object('delivery_status',p_status));
  return true;
end $$;

create function public.purge_expired_support_records(p_retention_days integer)
returns integer language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare removed integer;
begin
  if p_retention_days < 1 or p_retention_days > 3650 then raise exception 'invalid retention'; end if;
  delete from public.support_requests where status='completed'
    and coalesce(answered_at,updated_at) < now() - make_interval(days => p_retention_days);
  get diagnostics removed=row_count;
  return removed;
end $$;

create or replace function public.ensure_company_billing(p_company_id uuid)
returns setof public.company_billing language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin
 insert into public.company_billing(company_id,trial_ends_at,status)
 select id,now()+interval '7 days','trial_pending' from public.companies where id=p_company_id on conflict do nothing;
 return query select * from public.company_billing where company_id=p_company_id;
end $$;

create or replace function public.apply_billing_snapshot(p_company_id uuid,p_event_id text,p_subscription_id text,p_status text,p_paid_until timestamptz)
returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare n integer;
begin
 perform public.ensure_company_billing(p_company_id);
 insert into public.billing_webhook_events(event_id,company_id) values(p_event_id,p_company_id) on conflict do nothing;
 get diagnostics n=row_count;
 if n=0 then return; end if;
 update public.company_billing set stripe_subscription_id=p_subscription_id,status=p_status,
  paid_until=p_paid_until,
  trial_ends_at=case when p_status='trialing' and p_paid_until is not null then p_paid_until else trial_ends_at end,
  updated_at=now() where company_id=p_company_id;
 if not found then raise exception 'company missing'; end if;
end $$;

revoke all on function public.create_support_request(text,uuid,uuid,text,text,text,text,text,text,text),
  public.update_support_request_admin(uuid,text,text,uuid),
  public.add_support_note_admin(uuid,text,uuid),
  public.reserve_support_reply(uuid,text,text,uuid,text),
  public.finalize_support_reply(uuid,text,text,text,uuid),
  public.purge_expired_support_records(integer)
from public,anon,authenticated,service_role;
grant execute on function public.create_support_request(text,uuid,uuid,text,text,text,text,text,text,text),
  public.update_support_request_admin(uuid,text,text,uuid),
  public.add_support_note_admin(uuid,text,uuid),
  public.reserve_support_reply(uuid,text,text,uuid,text),
  public.finalize_support_reply(uuid,text,text,text,uuid),
  public.purge_expired_support_records(integer)
to service_role;

-- Replacing these functions preserves their existing ACL; assert the expected service-only contract.
revoke all on function public.ensure_company_billing(uuid),
  public.apply_billing_snapshot(uuid,text,text,text,timestamptz)
from public,anon,authenticated;
grant execute on function public.ensure_company_billing(uuid),
  public.apply_billing_snapshot(uuid,text,text,text,timestamptz)
to service_role;

commit;
