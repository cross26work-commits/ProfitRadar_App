begin;
create table public.ai_budget_reservations (
 id uuid primary key default gen_random_uuid(), company_id uuid not null references public.companies(id),
 model text not null, reserved_tokens bigint not null check(reserved_tokens>0),
 reserved_cost_micro_usd bigint not null check(reserved_cost_micro_usd>0),
 token_limit bigint not null, cost_limit_micro_usd bigint not null,
 status text not null default 'reserved' check(status in ('reserved','succeeded','reviewed_unknown')),
 actual_input_tokens bigint, actual_output_tokens bigint, created_at timestamptz not null default now()
);
create index ai_budget_company_month on public.ai_budget_reservations(company_id,created_at);
alter table public.ai_budget_reservations enable row level security;
revoke all on public.ai_budget_reservations from public,anon,authenticated;
grant select on public.ai_budget_reservations to service_role;
grant update(status,actual_input_tokens,actual_output_tokens) on public.ai_budget_reservations to service_role;
create function public.reserve_ai_budget(p_company_id uuid,p_model text,p_tokens bigint,p_cost_micro_usd bigint,p_token_limit bigint,p_cost_limit_micro_usd bigint)
returns uuid language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare result uuid; used_tokens bigint; used_cost bigint; token_cap bigint; cost_cap bigint;
begin
 if p_tokens is null or p_tokens<1 or p_cost_micro_usd is null or p_cost_micro_usd<1
  or p_token_limit is null or p_token_limit<1 or p_cost_limit_micro_usd is null or p_cost_limit_micro_usd<1
  or coalesce(length(p_model),0)<1 then raise exception 'invalid budget'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_company_id::text,48));
 -- A worker crash remains locked for paid generation until explicit operator review.
 if exists(select 1 from public.ai_budget_reservations where company_id=p_company_id and status='reserved') then return null; end if;
 select coalesce(sum(reserved_tokens),0),coalesce(sum(reserved_cost_micro_usd),0),
  least(p_token_limit,coalesce(min(token_limit),p_token_limit)),
  least(p_cost_limit_micro_usd,coalesce(min(cost_limit_micro_usd),p_cost_limit_micro_usd))
 into used_tokens,used_cost,token_cap,cost_cap from public.ai_budget_reservations
 where company_id=p_company_id and created_at >= date_trunc('month',now() at time zone 'UTC') at time zone 'UTC';
 -- Limits cannot silently increase mid-month after a configuration change.
 if used_tokens+p_tokens>token_cap or used_cost+p_cost_micro_usd>cost_cap then return null; end if;
 insert into public.ai_budget_reservations(company_id,model,reserved_tokens,reserved_cost_micro_usd,token_limit,cost_limit_micro_usd)
 values(p_company_id,p_model,p_tokens,p_cost_micro_usd,token_cap,cost_cap) returning id into result;
 return result;
end $$;
revoke all on function public.reserve_ai_budget(uuid,text,bigint,bigint,bigint,bigint) from public,anon,authenticated;
grant execute on function public.reserve_ai_budget(uuid,text,bigint,bigint,bigint,bigint) to service_role;
commit;
