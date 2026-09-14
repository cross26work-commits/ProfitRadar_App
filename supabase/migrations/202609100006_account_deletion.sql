-- No deletion runs on migration. Destruction requires verified-user job + worker.
begin;
create table public.account_deletion_jobs (
 id uuid primary key default gen_random_uuid(), company_id uuid not null unique, user_id uuid not null unique,
 status text not null default 'providers' check(status in ('providers','data','auth','completed')),
 gmail_done boolean not null default false, billing_done boolean not null default false,
 billing_reference text, last_error_code text, requested_at timestamptz not null default now(),
 completed_at timestamptz, purge_after timestamptz not null
);
create table public.account_deletion_audit (
 id uuid primary key default gen_random_uuid(), job_id uuid not null references public.account_deletion_jobs(id) on delete cascade,
 stage text not null, created_at timestamptz not null default now(), unique(job_id,stage)
);
alter table public.account_deletion_jobs enable row level security;
alter table public.account_deletion_audit enable row level security;
revoke all on public.account_deletion_jobs,public.account_deletion_audit from public,anon,authenticated;
grant select on public.account_deletion_jobs,public.account_deletion_audit to service_role;
grant update(gmail_done,billing_done,billing_reference,last_error_code) on public.account_deletion_jobs to service_role;
create function public.company_is_active(p_company_id uuid) returns boolean language sql stable security definer set search_path=pg_catalog,pg_temp as $$
 select exists(select 1 from public.companies where id=p_company_id) and not exists(select 1 from public.account_deletion_jobs where company_id=p_company_id)
$$;
create function public.request_account_deletion(p_user_id uuid,p_retention_days integer) returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare profile public.profiles%rowtype; job public.account_deletion_jobs%rowtype;
begin
 if p_retention_days is null or p_retention_days<1 or p_retention_days>3650 then raise exception 'retention configuration required'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_user_id::text,0));
 select * into job from public.account_deletion_jobs where user_id=p_user_id;
 if found then return to_jsonb(job); end if;
 select * into profile from public.profiles where user_id=p_user_id for update;
 if not found or profile.role<>'owner' then raise exception 'owner required'; end if;
 if (select count(*) from public.profiles where company_id=profile.company_id)<>1 then raise exception 'single-user company required'; end if;
 insert into public.account_deletion_jobs(company_id,user_id,purge_after)
 values(profile.company_id,p_user_id,now()+make_interval(days=>p_retention_days)) returning * into job;
 insert into public.account_deletion_audit(job_id,stage) values(job.id,'requested');
 return to_jsonb(job);
end $$;
create function public.purge_account_data(p_job_id uuid) returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare job public.account_deletion_jobs%rowtype; t text;
begin
 select * into job from public.account_deletion_jobs where id=p_job_id for update;
 if not found then raise exception 'job missing'; end if;
 if job.status in ('auth','completed') then return; end if;
 if not job.gmail_done or not job.billing_done then raise exception 'provider cleanup pending'; end if;
 if exists(select 1 from public.gmail_connections where company_id=job.company_id) then raise exception 'credential cleanup pending'; end if;
 if exists(select 1 from public.gmail_send_operations where company_id=job.company_id and status in ('sending','unknown')) then raise exception 'send reconciliation required'; end if;
 if exists(select 1 from public.ai_budget_reservations where company_id=job.company_id and status='reserved') then raise exception 'AI reconciliation required'; end if;
 -- Explicit known children only. Unexpected foreign keys fail and roll back all DB deletion.
 foreach t in array array['financial_payments','financial_record_history','financial_records','gmail_inbound_receipts','gmail_sync_cursors',
  'reply_drafts','gmail_send_operations','conversation_analysis_snapshots','ai_budget_reservations','ai_usage_runs',
  'gmail_company_sync_runs','gmail_sync_runs','operation_recovery_audit','billing_webhook_events','billing_checkout_attempts',
  'company_billing','timeline','learning_logs','ai_judgements','calendar_events','reply_logs','profit_events','messages','customers','profiles','gmail_work_locks'] loop
  execute format('delete from public.%I where company_id=$1',t) using job.company_id;
 end loop;
 delete from public.companies where id=job.company_id;
 update public.account_deletion_jobs set status='auth',last_error_code=null where id=job.id;
 insert into public.account_deletion_audit(job_id,stage) values(job.id,'data_deleted') on conflict do nothing;
end $$;
create function public.complete_account_deletion(p_job_id uuid) returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare job public.account_deletion_jobs%rowtype;
begin
 select * into job from public.account_deletion_jobs where id=p_job_id for update;
 if not found then raise exception 'job missing'; end if;
 if job.status='completed' then return; end if;
 if job.status<>'auth' or exists(select 1 from auth.users where id=job.user_id) then raise exception 'auth cleanup pending'; end if;
 -- Count the approved retention interval from completion, not from an earlier
 -- request that may have spent weeks awaiting provider recovery.
 update public.account_deletion_jobs set status='completed',completed_at=now(),
  purge_after=now()+(job.purge_after-job.requested_at),last_error_code=null where id=job.id;
 insert into public.account_deletion_audit(job_id,stage) values(job.id,'completed') on conflict do nothing;
end $$;
create function public.purge_expired_deletion_audit() returns bigint language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare n bigint;
begin
 delete from public.account_deletion_jobs where status='completed' and purge_after<now();
 get diagnostics n=row_count; return n;
end $$;
create function public.prevent_deleted_user_onboarding() returns trigger language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin
 perform pg_advisory_xact_lock(hashtextextended(new.user_id::text,0));
 if exists(select 1 from public.account_deletion_jobs where user_id=new.user_id) then raise exception 'deletion requested'; end if;
 return new;
end $$;
create trigger prevent_deleted_user_onboarding before insert on public.profiles for each row execute function public.prevent_deleted_user_onboarding();
revoke all on function public.prevent_deleted_user_onboarding() from public,anon,authenticated;
revoke all on function public.company_is_active(uuid),public.request_account_deletion(uuid,integer),public.purge_account_data(uuid),public.complete_account_deletion(uuid),public.purge_expired_deletion_audit() from public,anon,authenticated;
grant execute on function public.company_is_active(uuid),public.request_account_deletion(uuid,integer),public.purge_account_data(uuid),public.complete_account_deletion(uuid),public.purge_expired_deletion_audit() to service_role;
commit;
