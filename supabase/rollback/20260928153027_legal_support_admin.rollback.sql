-- PRE-PRODUCTION / DISPOSABLE rollback only. This aborts if any support or
-- consent evidence exists. Never use it to delete Production customer data.
begin;
do $$
begin
  if exists(select 1 from public.support_requests)
    or exists(select 1 from public.company_business_consents)
    or exists(select 1 from public.billing_checkout_consents) then
    raise exception 'rollback refused: legal/support evidence exists';
  end if;
end $$;

create or replace function public.ensure_company_billing(p_company_id uuid)
returns setof public.company_billing language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin
 insert into public.company_billing(company_id,trial_ends_at)
 select id,created_at+interval '14 days' from public.companies where id=p_company_id on conflict do nothing;
 return query select * from public.company_billing where company_id=p_company_id;
end $$;

create or replace function public.apply_billing_snapshot(p_company_id uuid,p_event_id text,p_subscription_id text,p_status text,p_paid_until timestamptz)
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

drop function public.purge_expired_support_records(integer);
drop function public.finalize_support_reply(uuid,text,text,text,uuid);
drop function public.reserve_support_reply(uuid,text,text,uuid,text);
drop function public.add_support_note_admin(uuid,text,uuid);
drop function public.update_support_request_admin(uuid,text,text,uuid);
drop function public.create_support_request(text,uuid,uuid,text,text,text,text,text,text,text);
drop trigger support_requests_touch on public.support_requests;
drop function public.support_request_touch();
drop table public.support_audit_logs;
drop table public.support_internal_notes;
drop table public.support_messages;
drop table public.support_requests;
drop table public.billing_checkout_consents;
drop table public.company_business_consents;
commit;
