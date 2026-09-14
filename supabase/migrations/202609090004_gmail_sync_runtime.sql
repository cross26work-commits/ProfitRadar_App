-- Unapplied. Durable locks fail closed after worker crash; see release runbook.
begin;
create table public.gmail_work_locks (
 company_id uuid primary key references public.companies(id), owner_id uuid not null,
 purpose text not null, acquired_at timestamptz not null default now()
);
create table public.gmail_sync_runs (
 id uuid primary key default gen_random_uuid(), company_id uuid not null references public.companies(id),
 status text not null check(status in ('running','succeeded','failed','busy')),
 started_at timestamptz not null default now(), finished_at timestamptz,
 error_code text, detected_count integer not null default 0
);
create index gmail_sync_runs_company_time on public.gmail_sync_runs(company_id,started_at desc);
alter table public.gmail_work_locks enable row level security;
alter table public.gmail_sync_runs enable row level security;
revoke all on public.gmail_work_locks,public.gmail_sync_runs from public,anon,authenticated;
grant select,insert,update on public.gmail_sync_runs to service_role;
grant select on public.gmail_work_locks to service_role;
create function public.claim_gmail_work(p_company_id uuid,p_owner_id uuid,p_purpose text)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare n integer;
begin
 insert into public.gmail_work_locks(company_id,owner_id,purpose) values(p_company_id,p_owner_id,p_purpose) on conflict do nothing;
 get diagnostics n=row_count;
 return n=1;
end $$;
create function public.release_gmail_work(p_company_id uuid,p_owner_id uuid)
returns void language sql security definer set search_path=pg_catalog,pg_temp as $$
 delete from public.gmail_work_locks where company_id=p_company_id and owner_id=p_owner_id;
$$;
revoke all on function public.claim_gmail_work(uuid,uuid,text),public.release_gmail_work(uuid,uuid) from public,anon,authenticated;
grant execute on function public.claim_gmail_work(uuid,uuid,text),public.release_gmail_work(uuid,uuid) to service_role;
commit;
