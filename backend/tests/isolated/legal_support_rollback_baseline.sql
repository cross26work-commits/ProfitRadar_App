-- Minimal disposable pre-migration contract used only to execute the legal/support rollback drill.
create table public.companies(id uuid primary key default gen_random_uuid());
create table public.company_billing(
  company_id uuid primary key references public.companies(id) on delete cascade,
  trial_ends_at timestamptz not null,
  status text not null,
  stripe_subscription_id text,
  paid_until timestamptz,
  updated_at timestamptz not null default now()
);
create table public.billing_webhook_events(
  event_id text primary key,
  company_id uuid not null references public.companies(id) on delete cascade
);
create function public.ensure_company_billing(p_company_id uuid)
returns setof public.company_billing language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin
 insert into public.company_billing(company_id,trial_ends_at,status)
 select id,now()+interval '14 days','trial' from public.companies where id=p_company_id on conflict do nothing;
 return query select * from public.company_billing where company_id=p_company_id;
end $$;
create function public.apply_billing_snapshot(p_company_id uuid,p_event_id text,p_subscription_id text,p_status text,p_paid_until timestamptz)
returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin return; end $$;
