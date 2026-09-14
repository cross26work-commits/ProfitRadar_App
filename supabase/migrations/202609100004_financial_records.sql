begin;
-- Legacy actual_profit is NOT converted: its economic meaning is not defined.
create table public.financial_records (
 company_id uuid not null references public.companies(id), profit_event_id uuid primary key references public.profit_events(id),
 customer_id uuid not null references public.customers(id), expected_revenue bigint check(expected_revenue>=0),
 ordered_revenue bigint check(ordered_revenue>=0), paid_amount bigint check(paid_amount>=0), cost bigint check(cost>=0),
 occurred_at timestamptz not null, confirmed_at timestamptz, paid_at timestamptz,
 source text not null default 'manual' check(source='manual'), created_by uuid not null,
 version bigint not null, updated_at timestamptz not null default now(),
 check(ordered_revenue is null or confirmed_at is not null), check(paid_amount is null or paid_at is not null)
);
create table public.financial_record_history (
 id uuid primary key default gen_random_uuid(),company_id uuid not null references public.companies(id),
 profit_event_id uuid not null references public.profit_events(id), actor_id uuid not null,
 version bigint not null, previous_record jsonb, new_record jsonb not null,created_at timestamptz not null default now(),
 unique(profit_event_id,version)
);
alter table public.financial_records enable row level security;
alter table public.financial_record_history enable row level security;
revoke all on public.financial_records,public.financial_record_history from public,anon,authenticated;
grant select on public.financial_records,public.financial_record_history to service_role;
create function public.save_financial_record(p_company_id uuid,p_user_id uuid,p_event_id uuid,p_expected_version bigint,p_record jsonb)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare cid uuid; old_record public.financial_records%rowtype; new_record public.financial_records%rowtype;
begin
 if not exists(select 1 from public.profiles where user_id=p_user_id and company_id=p_company_id) then raise exception 'actor mismatch'; end if;
 select customer_id into cid from public.profit_events where id=p_event_id and company_id=p_company_id for update;
 if not found or cid is null or not exists(select 1 from public.customers where id=cid and company_id=p_company_id) then raise exception 'event mismatch'; end if;
 select * into old_record from public.financial_records where profit_event_id=p_event_id and company_id=p_company_id;
 if coalesce(old_record.version,0)<>p_expected_version then raise exception 'version conflict' using errcode='40001'; end if;
 insert into public.financial_records(company_id,profit_event_id,customer_id,expected_revenue,ordered_revenue,paid_amount,cost,occurred_at,confirmed_at,paid_at,created_by,version)
 values(p_company_id,p_event_id,cid,(p_record->>'expected_revenue')::bigint,(p_record->>'ordered_revenue')::bigint,(p_record->>'paid_amount')::bigint,(p_record->>'cost')::bigint,(p_record->>'occurred_at')::timestamptz,(p_record->>'confirmed_at')::timestamptz,(p_record->>'paid_at')::timestamptz,p_user_id,p_expected_version+1)
 on conflict(profit_event_id) do update set expected_revenue=excluded.expected_revenue,ordered_revenue=excluded.ordered_revenue,paid_amount=excluded.paid_amount,cost=excluded.cost,occurred_at=excluded.occurred_at,confirmed_at=excluded.confirmed_at,paid_at=excluded.paid_at,version=excluded.version,updated_at=now()
 returning * into new_record;
 insert into public.financial_record_history(company_id,profit_event_id,actor_id,version,previous_record,new_record)
 values(p_company_id,p_event_id,p_user_id,new_record.version,to_jsonb(old_record),to_jsonb(new_record));
 insert into public.timeline(company_id,customer_id,profit_event_id,event_type,title,metadata)
 values(p_company_id,cid,p_event_id,'financial_record_confirmed','売上・入金・原価を手動記録',jsonb_build_object('financial_version',new_record.version,'source','manual'));
 return to_jsonb(new_record);
end $$;
revoke all on function public.save_financial_record(uuid,uuid,uuid,bigint,jsonb) from public,anon,authenticated;
grant execute on function public.save_financial_record(uuid,uuid,uuid,bigint,jsonb) to service_role;
commit;
