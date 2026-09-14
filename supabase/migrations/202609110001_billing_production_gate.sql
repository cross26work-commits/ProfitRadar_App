begin;
create table public.billing_runtime_config (
 singleton boolean primary key default true check(singleton),
 mode text not null default 'test' check(mode in ('test','live')),
 approval_ref text,
 approved_at timestamptz
);
insert into public.billing_runtime_config(singleton) values(true);
alter table public.billing_runtime_config enable row level security;
revoke all on public.billing_runtime_config from public,anon,authenticated,service_role;
grant select on public.billing_runtime_config to service_role;
-- This is an operator-only, one-way promotion, NOT invoked by any HTTP route.
-- Stop every old/new API and worker before calling, after explicit approval.
create function public.promote_billing_live(p_approval_ref text,p_workers_stopped boolean)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare current_row public.billing_runtime_config%rowtype;
begin
 if p_workers_stopped is distinct from true or p_approval_ref is null
 or p_approval_ref !~ '^[A-Za-z0-9_-]{3,100}$' then raise exception 'approval and stopped workers required'; end if;
 lock table public.company_billing,public.billing_checkout_attempts,public.billing_webhook_events in share row exclusive mode;
 select * into strict current_row from public.billing_runtime_config where singleton for update;
 if current_row.mode='live' then
  if current_row.approval_ref<>p_approval_ref then raise exception 'approval mismatch'; end if;
  return false;
 end if;
 -- Never turn test subscriptions, unknown checkout attempts or paid access into live entitlements.
 if exists(select 1 from public.company_billing where stripe_subscription_id is not null or paid_until is not null or status not in ('trial','trial_expired'))
 or exists(select 1 from public.billing_checkout_attempts)
 or exists(select 1 from public.billing_webhook_events) then raise exception 'test billing history exists; use a separate reviewed production database'; end if;
 update public.billing_runtime_config set mode='live',approval_ref=p_approval_ref,approved_at=now() where singleton;
 return true;
end $$;
revoke all on function public.promote_billing_live(text,boolean) from public,anon,authenticated;
grant execute on function public.promote_billing_live(text,boolean) to service_role;
commit;
