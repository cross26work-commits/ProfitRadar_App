begin;
create table public.financial_payments (
 id uuid primary key, company_id uuid not null references public.companies(id),
 profit_event_id uuid not null references public.profit_events(id), customer_id uuid not null references public.customers(id),
 amount bigint not null check(amount>0 and amount<=1000000000000), paid_at timestamptz not null,
 created_by uuid not null, created_at timestamptz not null default now(),
 voided_at timestamptz, voided_by uuid, void_reason text
);
create index financial_payments_company_date on public.financial_payments(company_id,paid_at);
alter table public.financial_payments enable row level security;
revoke all on public.financial_payments from public,anon,authenticated;
grant select on public.financial_payments to service_role;
create function public.record_financial_payment(p_company_id uuid,p_user_id uuid,p_event_id uuid,p_operation_id uuid,p_amount bigint,p_paid_at timestamptz)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare cid uuid; result public.financial_payments%rowtype;
begin
 if not public.company_is_active(p_company_id) or not exists(select 1 from public.profiles where user_id=p_user_id and company_id=p_company_id) then raise exception 'actor mismatch'; end if;
 select customer_id into cid from public.profit_events where id=p_event_id and company_id=p_company_id for update;
 if not found or cid is null or not exists(select 1 from public.customers where id=cid and company_id=p_company_id) then raise exception 'event mismatch'; end if;
 select * into result from public.financial_payments where id=p_operation_id;
 if found then
  if result.company_id<>p_company_id or result.profit_event_id<>p_event_id or result.amount<>p_amount or result.paid_at<>p_paid_at then raise exception 'operation conflict' using errcode='40001'; end if;
  return to_jsonb(result);
 end if;
 insert into public.financial_payments(id,company_id,profit_event_id,customer_id,amount,paid_at,created_by)
 values(p_operation_id,p_company_id,p_event_id,cid,p_amount,p_paid_at,p_user_id) returning * into result;
 insert into public.timeline(company_id,customer_id,profit_event_id,event_type,title,metadata)
 values(p_company_id,cid,p_event_id,'payment_recorded','入金明細を手動記録',jsonb_build_object('payment_id',p_operation_id,'actor_id',p_user_id));
 return to_jsonb(result);
end $$;
create function public.void_financial_payment(p_company_id uuid,p_user_id uuid,p_payment_id uuid,p_reason text)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare result public.financial_payments%rowtype;
begin
 if not public.company_is_active(p_company_id) or not exists(select 1 from public.profiles where user_id=p_user_id and company_id=p_company_id) then raise exception 'actor mismatch'; end if;
 if coalesce(length(trim(p_reason)),0)<1 or length(p_reason)>200 then raise exception 'reason required'; end if;
 select * into result from public.financial_payments where id=p_payment_id and company_id=p_company_id for update;
 if not found then raise exception 'payment missing'; end if;
 if result.voided_at is not null then return to_jsonb(result); end if;
 update public.financial_payments set voided_at=now(),voided_by=p_user_id,void_reason=p_reason where id=p_payment_id returning * into result;
 insert into public.timeline(company_id,customer_id,profit_event_id,event_type,title,metadata)
 values(p_company_id,result.customer_id,result.profit_event_id,'payment_voided','入金明細を取消（元明細を保持）',jsonb_build_object('payment_id',p_payment_id,'actor_id',p_user_id));
 return to_jsonb(result);
end $$;
revoke all on function public.record_financial_payment(uuid,uuid,uuid,uuid,bigint,timestamptz),public.void_financial_payment(uuid,uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.record_financial_payment(uuid,uuid,uuid,uuid,bigint,timestamptz),public.void_financial_payment(uuid,uuid,uuid,text) to service_role;
commit;
