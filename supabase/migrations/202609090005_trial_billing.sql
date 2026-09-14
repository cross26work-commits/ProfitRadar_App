begin;
create table public.company_billing (
 company_id uuid primary key references public.companies(id),
 trial_ends_at timestamptz not null, status text not null default 'trial',
 stripe_subscription_id text unique, paid_until timestamptz,
 updated_at timestamptz not null default now()
);
create table public.billing_webhook_events (
 event_id text primary key, company_id uuid not null references public.companies(id),
 processed_at timestamptz not null default now()
);
alter table public.company_billing enable row level security;
alter table public.billing_webhook_events enable row level security;
revoke all on public.company_billing,public.billing_webhook_events from public,anon,authenticated;
grant select,insert,update on public.company_billing to service_role;
grant select,insert on public.billing_webhook_events to service_role;
create function public.ensure_company_billing(p_company_id uuid)
returns setof public.company_billing language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin
 insert into public.company_billing(company_id,trial_ends_at)
 select id,created_at+interval '14 days' from public.companies where id=p_company_id on conflict do nothing;
 return query select * from public.company_billing where company_id=p_company_id;
end $$;
create function public.apply_billing_snapshot(p_company_id uuid,p_event_id text,p_subscription_id text,p_status text,p_paid_until timestamptz)
returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare n integer;
begin
 perform public.ensure_company_billing(p_company_id);
 insert into public.billing_webhook_events(event_id,company_id) values(p_event_id,p_company_id) on conflict do nothing;
 get diagnostics n=row_count;
 if n=0 then return; end if;
 update public.company_billing set stripe_subscription_id=p_subscription_id,status=p_status,paid_until=p_paid_until,updated_at=now() where company_id=p_company_id;
 if not found then raise exception 'company missing'; end if;
end $$;
revoke all on function public.ensure_company_billing(uuid),public.apply_billing_snapshot(uuid,text,text,text,timestamptz) from public,anon,authenticated;
grant execute on function public.ensure_company_billing(uuid),public.apply_billing_snapshot(uuid,text,text,text,timestamptz) to service_role;
commit;
