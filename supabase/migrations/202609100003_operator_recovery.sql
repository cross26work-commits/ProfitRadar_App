begin;
create table public.operation_recovery_audit (
 id uuid primary key default gen_random_uuid(), company_id uuid not null references public.companies(id),
 owner_id uuid not null, purpose text not null, operator_ref text not null, ticket_ref text not null,
 stopped_workers_confirmed boolean not null check(stopped_workers_confirmed), recovered_at timestamptz not null default now()
);
alter table public.operation_recovery_audit enable row level security;
revoke all on public.operation_recovery_audit from public,anon,authenticated;
grant select on public.operation_recovery_audit to service_role;
create function public.recover_company_work(p_company_id uuid,p_expected_owner uuid,p_operator_ref text,p_ticket_ref text,p_workers_stopped boolean)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare work public.gmail_work_locks%rowtype;
begin
 if p_workers_stopped is distinct from true or coalesce(length(trim(p_operator_ref)),0)<3 or coalesce(length(trim(p_ticket_ref)),0)<3 then raise exception 'operator attestation required'; end if;
 select * into work from public.gmail_work_locks where company_id=p_company_id for update;
 if not found then return false; end if;
 if work.owner_id<>p_expected_owner then raise exception 'owner changed; inspect again'; end if;
 insert into public.operation_recovery_audit(company_id,owner_id,purpose,operator_ref,ticket_ref,stopped_workers_confirmed)
 values(p_company_id,work.owner_id,work.purpose,left(p_operator_ref,100),left(p_ticket_ref,100),true);
 update public.gmail_send_operations set status='unknown',updated_at=now() where company_id=p_company_id and status='sending';
 update public.gmail_company_sync_runs set status='failed',error_code='OPERATOR_RECOVERED',finished_at=now() where company_id=p_company_id and status='running';
 delete from public.gmail_work_locks where company_id=p_company_id and owner_id=p_expected_owner;
 return true;
end $$;
revoke all on function public.recover_company_work(uuid,uuid,text,text,boolean) from public,anon,authenticated;
grant execute on function public.recover_company_work(uuid,uuid,text,text,boolean) to service_role;
commit;
