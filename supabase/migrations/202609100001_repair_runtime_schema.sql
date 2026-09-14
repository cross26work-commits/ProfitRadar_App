begin;

-- =========================================================
-- PRECONDITIONS
-- Base Profit Radar schema must already exist.
-- If a prerequisite is missing, abort the whole transaction.
-- =========================================================

do $$
begin
  if to_regclass('public.companies') is null then
    raise exception 'PRECONDITION: public.companies is missing';
  end if;

  if to_regclass('public.customers') is null then
    raise exception 'PRECONDITION: public.customers is missing';
  end if;

  if to_regclass('public.profit_events') is null then
    raise exception 'PRECONDITION: public.profit_events is missing';
  end if;

  if to_regclass('public.reply_logs') is null then
    raise exception 'PRECONDITION: public.reply_logs is missing';
  end if;

  if to_regclass('public.timeline') is null then
    raise exception 'PRECONDITION: public.timeline is missing';
  end if;

  if not exists (
    select 1
    from information_schema.columns
    where table_schema='public'
      and table_name='companies'
      and column_name='created_at'
  ) then
    raise exception 'PRECONDITION: companies.created_at is missing';
  end if;
end
$$;


-- =========================================================
-- CONVERSATION ANALYSIS SNAPSHOTS
-- =========================================================

create table if not exists public.conversation_analysis_snapshots (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null
    references public.companies(id)
    on delete cascade,
  profit_event_id uuid not null
    references public.profit_events(id)
    on delete cascade,
  analysis_version text not null
    default 'conversation-v1',
  payload jsonb not null
    default '{}'::jsonb,
  provider text,
  model text,
  created_at timestamptz not null
    default now()
);

create index if not exists
  idx_conversation_analysis_snapshots_company_event_created
on public.conversation_analysis_snapshots(
  company_id,
  profit_event_id,
  created_at desc
);

alter table public.conversation_analysis_snapshots
  enable row level security;

revoke all
on public.conversation_analysis_snapshots
from public, anon, authenticated;

grant select, insert
on public.conversation_analysis_snapshots
to service_role;


-- Existing duplicate Gmail IDs would make this fail and rollback,
-- which is intentional.
create unique index if not exists
  uq_reply_logs_company_gmail_message
on public.reply_logs(company_id, gmail_message_id)
where gmail_message_id is not null;


-- =========================================================
-- GMAIL SEND OPERATIONS
-- =========================================================

create table if not exists public.gmail_send_operations (
  company_id uuid not null
    references public.companies(id),
  profit_event_id uuid not null
    references public.profit_events(id),
  customer_id uuid not null
    references public.customers(id),
  operation_id text not null,
  request_hash text not null,
  status text not null
    check(status in ('sending','unknown','sent')),
  recipient text not null,
  subject text not null,
  body text not null,
  gmail_message_id text,
  gmail_thread_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(company_id, operation_id)
);

create unique index if not exists
  gmail_send_one_unresolved_event
on public.gmail_send_operations(
  company_id,
  profit_event_id
)
where status in ('sending','unknown');

alter table public.gmail_send_operations
  enable row level security;

revoke all
on public.gmail_send_operations
from public, anon, authenticated;

grant select, insert, update
on public.gmail_send_operations
to service_role;


create or replace function public.finalize_gmail_send(
  p_company_id uuid,
  p_operation_id text,
  p_message_id text,
  p_thread_id text
)
returns boolean
language plpgsql
security definer
set search_path=pg_catalog,pg_temp
as $$
declare
  op public.gmail_send_operations%rowtype;
  cid uuid;
begin
  select *
  into strict op
  from public.gmail_send_operations
  where company_id=p_company_id
    and operation_id=p_operation_id
  for update;

  if op.status='sent' then
    if op.gmail_message_id<>p_message_id then
      raise exception 'provider identity conflict';
    end if;
    return true;
  end if;

  if coalesce(p_message_id,'')=''
     or coalesce(p_thread_id,'')='' then
    raise exception 'provider identity missing';
  end if;

  select customer_id
  into strict cid
  from public.profit_events
  where id=op.profit_event_id
    and company_id=p_company_id;

  if cid<>op.customer_id then
    raise exception
      'event customer changed; reconciliation required';
  end if;

  if not exists (
    select 1
    from public.customers
    where id=cid
      and company_id=p_company_id
  ) then
    raise exception 'tenant mismatch';
  end if;

  insert into public.reply_logs(
    company_id,
    customer_id,
    profit_event_id,
    channel,
    reply_body,
    gmail_message_id,
    gmail_thread_id,
    external_id,
    thread_id
  )
  values(
    p_company_id,
    cid,
    op.profit_event_id,
    'gmail',
    op.body,
    p_message_id,
    p_thread_id,
    p_message_id,
    p_thread_id
  );

  insert into public.timeline(
    company_id,
    customer_id,
    profit_event_id,
    event_type,
    channel,
    title,
    description,
    metadata
  )
  values(
    p_company_id,
    cid,
    op.profit_event_id,
    'reply_sent_gmail',
    'gmail',
    'Gmail返信を送信',
    left(op.body,500),
    jsonb_build_object(
      'gmail_message_id',p_message_id,
      'gmail_thread_id',p_thread_id,
      'operation_id',p_operation_id
    )
  );

  update public.profit_events
  set gmail_thread_id=p_thread_id,
      last_gmail_message_id=p_message_id
  where company_id=p_company_id
    and id=op.profit_event_id;

  update public.gmail_send_operations
  set status='sent',
      gmail_message_id=p_message_id,
      gmail_thread_id=p_thread_id,
      updated_at=now()
  where company_id=p_company_id
    and operation_id=p_operation_id;

  return true;
end
$$;

revoke all
on function public.finalize_gmail_send(
  uuid,text,text,text
)
from public, anon, authenticated;

grant execute
on function public.finalize_gmail_send(
  uuid,text,text,text
)
to service_role;


-- =========================================================
-- GMAIL SYNC RUNTIME
-- =========================================================

create table if not exists public.gmail_work_locks (
  company_id uuid primary key
    references public.companies(id),
  owner_id uuid not null,
  purpose text not null,
  acquired_at timestamptz not null
    default now()
);

create table if not exists public.gmail_company_sync_runs (
  id uuid primary key
    default gen_random_uuid(),
  company_id uuid not null
    references public.companies(id),
  status text not null
    check(status in (
      'running',
      'succeeded',
      'failed',
      'busy'
    )),
  started_at timestamptz not null
    default now(),
  finished_at timestamptz,
  error_code text,
  detected_count integer not null
    default 0
);

create index if not exists
  gmail_company_sync_runs_company_time
on public.gmail_company_sync_runs(
  company_id,
  started_at desc
);

alter table public.gmail_work_locks
  enable row level security;

alter table public.gmail_company_sync_runs
  enable row level security;

revoke all
on public.gmail_work_locks,
   public.gmail_company_sync_runs
from public, anon, authenticated;

grant select,insert,update
on public.gmail_company_sync_runs
to service_role;

grant select
on public.gmail_work_locks
to service_role;


create or replace function public.claim_gmail_work(
  p_company_id uuid,
  p_owner_id uuid,
  p_purpose text
)
returns boolean
language plpgsql
security definer
set search_path=pg_catalog,pg_temp
as $$
declare
  n integer;
begin
  insert into public.gmail_work_locks(
    company_id,
    owner_id,
    purpose
  )
  values(
    p_company_id,
    p_owner_id,
    p_purpose
  )
  on conflict do nothing;

  get diagnostics n=row_count;

  return n=1;
end
$$;


create or replace function public.release_gmail_work(
  p_company_id uuid,
  p_owner_id uuid
)
returns void
language sql
security definer
set search_path=pg_catalog,pg_temp
as $$
  delete
  from public.gmail_work_locks
  where company_id=p_company_id
    and owner_id=p_owner_id;
$$;

revoke all
on function public.claim_gmail_work(
  uuid,uuid,text
),
public.release_gmail_work(
  uuid,uuid
)
from public, anon, authenticated;

grant execute
on function public.claim_gmail_work(
  uuid,uuid,text
),
public.release_gmail_work(
  uuid,uuid
)
to service_role;


-- =========================================================
-- TRIAL BILLING
-- =========================================================

create table if not exists public.company_billing (
  company_id uuid primary key
    references public.companies(id),
  trial_ends_at timestamptz not null,
  status text not null
    default 'trial',
  stripe_subscription_id text unique,
  paid_until timestamptz,
  updated_at timestamptz not null
    default now()
);

create table if not exists public.billing_webhook_events (
  event_id text primary key,
  company_id uuid not null
    references public.companies(id),
  processed_at timestamptz not null
    default now()
);

alter table public.company_billing
  enable row level security;

alter table public.billing_webhook_events
  enable row level security;

revoke all
on public.company_billing,
   public.billing_webhook_events
from public, anon, authenticated;

grant select,insert,update
on public.company_billing
to service_role;

grant select,insert
on public.billing_webhook_events
to service_role;


create or replace function public.ensure_company_billing(
  p_company_id uuid
)
returns setof public.company_billing
language plpgsql
security definer
set search_path=pg_catalog,pg_temp
as $$
begin
  insert into public.company_billing(
    company_id,
    trial_ends_at
  )
  select
    id,
    created_at + interval '14 days'
  from public.companies
  where id=p_company_id
  on conflict do nothing;

  return query
  select *
  from public.company_billing
  where company_id=p_company_id;
end
$$;


create or replace function public.apply_billing_snapshot(
  p_company_id uuid,
  p_event_id text,
  p_subscription_id text,
  p_status text,
  p_paid_until timestamptz
)
returns void
language plpgsql
security definer
set search_path=pg_catalog,pg_temp
as $$
declare
  n integer;
begin
  perform public.ensure_company_billing(
    p_company_id
  );

  insert into public.billing_webhook_events(
    event_id,
    company_id
  )
  values(
    p_event_id,
    p_company_id
  )
  on conflict do nothing;

  get diagnostics n=row_count;

  if n=0 then
    return;
  end if;

  update public.company_billing
  set stripe_subscription_id=p_subscription_id,
      status=p_status,
      paid_until=p_paid_until,
      updated_at=now()
  where company_id=p_company_id;

  if not found then
    raise exception 'company missing';
  end if;
end
$$;

revoke all
on function public.ensure_company_billing(uuid),
public.apply_billing_snapshot(
  uuid,text,text,text,timestamptz
)
from public, anon, authenticated;

grant execute
on function public.ensure_company_billing(uuid),
public.apply_billing_snapshot(
  uuid,text,text,text,timestamptz
)
to service_role;


-- =========================================================
-- AI USAGE
-- =========================================================

create table if not exists public.ai_usage_runs (
  id uuid primary key
    default gen_random_uuid(),
  company_id uuid not null
    references public.companies(id),
  status text not null
    default 'reserved',
  created_at timestamptz not null
    default now(),
  elapsed_ms integer,
  input_tokens integer,
  output_tokens integer,
  cost_usd numeric
);

alter table public.ai_usage_runs
  enable row level security;

revoke all
on public.ai_usage_runs
from public, anon, authenticated;

grant select,update
on public.ai_usage_runs
to service_role;


create or replace function public.reserve_ai_run(
  p_company_id uuid,
  p_monthly_limit integer
)
returns uuid
language plpgsql
security definer
set search_path=pg_catalog,pg_temp
as $$
declare
  result uuid;
begin
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_company_id::text,
      47
    )
  );

  if p_monthly_limit < 1
     or p_monthly_limit > 10000 then
    raise exception 'invalid cap';
  end if;

  if (
    select count(*)
    from public.ai_usage_runs
    where company_id=p_company_id
      and created_at >=
        date_trunc(
          'month',
          now() at time zone 'UTC'
        ) at time zone 'UTC'
  ) >= p_monthly_limit then
    return null;
  end if;

  insert into public.ai_usage_runs(
    company_id
  )
  values(
    p_company_id
  )
  returning id into result;

  return result;
end
$$;

revoke all
on function public.reserve_ai_run(
  uuid,integer
)
from public, anon, authenticated;

grant execute
on function public.reserve_ai_run(
  uuid,integer
)
to service_role;


commit;
