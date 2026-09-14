begin;
alter table public.conversation_analysis_snapshots enable row level security;
revoke all on public.conversation_analysis_snapshots from public,anon,authenticated;
grant select,insert on public.conversation_analysis_snapshots to service_role;
create table public.ai_usage_runs (
 id uuid primary key default gen_random_uuid(),company_id uuid not null references public.companies(id),
 status text not null default 'reserved',created_at timestamptz not null default now(),
 elapsed_ms integer,input_tokens integer,output_tokens integer,cost_usd numeric
);
alter table public.ai_usage_runs enable row level security;
revoke all on public.ai_usage_runs from public,anon,authenticated;
grant select,update on public.ai_usage_runs to service_role;
create function public.reserve_ai_run(p_company_id uuid,p_monthly_limit integer)
returns uuid language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare result uuid;
begin
 perform pg_advisory_xact_lock(hashtextextended(p_company_id::text,47));
 if p_monthly_limit<1 or p_monthly_limit>10000 then raise exception 'invalid cap'; end if;
 if (select count(*) from public.ai_usage_runs where company_id=p_company_id and created_at>=date_trunc('month',now() at time zone 'UTC') at time zone 'UTC')>=p_monthly_limit then return null; end if;
 insert into public.ai_usage_runs(company_id) values(p_company_id) returning id into result;
 return result;
end $$;
revoke all on function public.reserve_ai_run(uuid,integer) from public,anon,authenticated;
grant execute on function public.reserve_ai_run(uuid,integer) to service_role;
commit;
