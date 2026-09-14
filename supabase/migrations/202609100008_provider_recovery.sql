begin;
-- Administrative recovery only. No HTTP endpoint; callers must stop workers
-- and review the provider before attesting. Never refund a budget reservation.
create function public.resolve_provider_uncertainty(p_company_id uuid,p_expected_id uuid,p_kind text,p_operator_ref text,p_ticket_ref text,p_workers_stopped boolean,p_provider_reviewed boolean)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare current_status text;
begin
 if p_workers_stopped is distinct from true or p_provider_reviewed is distinct from true
 or coalesce(length(trim(p_operator_ref)),0)<3 or coalesce(length(trim(p_ticket_ref)),0)<3 then
  raise exception 'operator and provider review required';
 end if;
 if p_kind not in ('ai','gmail-revoke') or p_kind is null then raise exception 'invalid recovery kind'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_company_id::text,48));
 -- This is not a stale-lock takeover. Recover that lock separately after review.
 if exists(select 1 from public.gmail_work_locks where company_id=p_company_id) then raise exception 'company work unresolved'; end if;
 if p_kind='ai' then
  select status into current_status from public.ai_budget_reservations where id=p_expected_id and company_id=p_company_id for update;
  if not found or current_status<>'reserved' then return false; end if;
  update public.ai_budget_reservations set status='reviewed_unknown' where id=p_expected_id and company_id=p_company_id;
 else
  -- Human must verify removal in Google account permissions, not infer it from
  -- a generic HTTP 400. Exact row/status fence prevents touching a reconnect.
  select status into current_status from public.gmail_connections where id=p_expected_id and company_id=p_company_id for update;
  if not found then return false; end if;
  if current_status<>'revocation_pending' then raise exception 'connection changed'; end if;
  delete from public.gmail_connections where id=p_expected_id and company_id=p_company_id and status='revocation_pending';
 end if;
 insert into public.operation_recovery_audit(company_id,owner_id,purpose,operator_ref,ticket_ref,stopped_workers_confirmed)
 values(p_company_id,p_expected_id,p_kind,left(p_operator_ref,100),left(p_ticket_ref,100),true);
 return true;
end $$;
revoke all on function public.resolve_provider_uncertainty(uuid,uuid,text,text,text,boolean,boolean) from public,anon,authenticated;
grant execute on function public.resolve_provider_uncertainty(uuid,uuid,text,text,text,boolean,boolean) to service_role;
commit;
