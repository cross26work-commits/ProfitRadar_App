-- P0 tenant hardening. Review release_readonly_tenant_audit.sql output first.
begin;
do $$
declare t text;
begin
  foreach t in array array['companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections'] loop
    if to_regclass('public.' || t) is null then raise exception 'required table public.% does not exist', t; end if;
  end loop;
  if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='profiles' and column_name='user_id')
     or not exists (select 1 from information_schema.columns where table_schema='public' and table_name='profiles' and column_name='company_id')
     or not exists (select 1 from information_schema.columns where table_schema='public' and table_name='profiles' and column_name='full_name') then
    raise exception 'expected profiles(user_id, company_id, full_name) is missing; stop and reconcile schema';
  end if;
  if exists (select 1 from public.profiles where user_id is null) then raise exception 'profiles.user_id contains NULL'; end if;
  if exists (select user_id from public.profiles group by user_id having count(*) > 1) then raise exception 'profiles.user_id duplicates exist'; end if;
end $$;
-- A same-name index is not proof of the required uniqueness guarantee.
do $$
begin
  if to_regclass('public.uq_profiles_user_id') is not null and not exists (
    select 1 from pg_catalog.pg_index i
    join pg_catalog.pg_attribute a on a.attrelid=i.indrelid and a.attname='user_id'
    where i.indexrelid=to_regclass('public.uq_profiles_user_id')
      and i.indrelid='public.profiles'::regclass and i.indisunique
      and i.indisvalid and i.indisready and i.indnkeyatts=1 and i.indnatts=1
      and i.indkey[0]=a.attnum and i.indpred is null and i.indexprs is null
  ) then raise exception 'uq_profiles_user_id has unexpected definition; review before applying'; end if;
end $$;
create unique index if not exists uq_profiles_user_id on public.profiles(user_id);
alter table public.companies enable row level security; alter table public.profiles enable row level security;
alter table public.customers enable row level security; alter table public.messages enable row level security;
alter table public.profit_events enable row level security; alter table public.timeline enable row level security;
alter table public.reply_logs enable row level security; alter table public.ai_judgements enable row level security;
alter table public.learning_logs enable row level security; alter table public.calendar_events enable row level security;
alter table public.gmail_connections enable row level security;
-- Explicit list only: unrelated public tables and sequences are not changed.
revoke all on table public.companies, public.profiles, public.customers, public.messages, public.profit_events, public.timeline, public.reply_logs, public.ai_judgements, public.learning_logs, public.calendar_events, public.gmail_connections from public, anon, authenticated;
-- Table REVOKE does not remove column ACLs. Scope both to the exact app tables.
do $$
declare t text; cols text;
begin
  foreach t in array array['companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections'] loop
    select string_agg(quote_ident(attname), ',') into cols from pg_attribute
      where attrelid=to_regclass('public.'||t) and attnum>0 and not attisdropped;
    execute format('revoke select (%s), insert (%s), update (%s), references (%s) on table public.%I from public, anon, authenticated', cols,cols,cols,cols,t);
    if has_table_privilege('authenticated', 'public.'||t, 'SELECT,INSERT,UPDATE,DELETE')
       or has_table_privilege('anon', 'public.'||t, 'SELECT,INSERT,UPDATE,DELETE')
       or has_any_column_privilege('authenticated', 'public.'||t, 'SELECT,INSERT,UPDATE,REFERENCES')
       or has_any_column_privilege('anon', 'public.'||t, 'SELECT,INSERT,UPDATE,REFERENCES') then
      raise exception 'inherited privilege remains on %; inspect role membership before applying',t;
    end if;
  end loop;
end $$;
grant usage on schema public to service_role;
grant select, insert, update, delete on table public.companies, public.profiles, public.customers, public.messages, public.profit_events, public.timeline, public.reply_logs, public.ai_judgements, public.learning_logs, public.calendar_events, public.gmail_connections to service_role;
grant select on table public.profiles to authenticated;
-- Existing profileService embeds companies(name,plan); preserve this legitimate path.
grant select on table public.companies to authenticated;
create policy companies_own_read on public.companies for select to authenticated
using (id in (select company_id from public.profiles where user_id=auth.uid()));
create policy companies_self_boundary on public.companies as restrictive for select to authenticated
using (id in (select company_id from public.profiles where user_id=auth.uid()));
-- Only known legacy onboarding policies are removed. Unknown policies are retained for audit review.
drop policy if exists profiles_insert_own on public.profiles;
drop policy if exists companies_insert_authenticated on public.companies;
drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles for select to authenticated using (user_id = auth.uid());
-- Restrictive policy intersects any retained permissive SELECT/ALL policy.
create policy profiles_self_boundary on public.profiles as restrictive for select to authenticated using (user_id = auth.uid());
-- CREATE OR REPLACE cannot rename input arguments or change the return type.
-- Unknown overloads are a stop condition, not silently left exposed or dropped.
do $$
declare f record;
begin
  for f in select p.* from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname='onboard_user' loop
    if f.oid <> coalesce(to_regprocedure('public.onboard_user(uuid,text,text,text)')::oid,0)
       or pg_get_function_result(f.oid) <> 'TABLE(created boolean, company_id uuid, profile_id uuid)'
       or f.proargnames[1:4] <> array['p_user_id','p_company_name','p_name','p_email'] then
      raise exception 'onboard_user incompatible signature; capture definition and plan explicit transition';
    end if;
  end loop;
end $$;
create or replace function public.onboard_user(p_user_id uuid, p_company_name text, p_name text, p_email text)
returns table(created boolean, company_id uuid, profile_id uuid)
language plpgsql security definer set search_path = pg_catalog, pg_temp
as $$
declare v_company_id uuid; v_profile_id uuid;
begin
  if p_user_id is null or coalesce(trim(p_company_name), '') = '' or coalesce(trim(p_name), '') = '' then raise exception 'invalid onboarding input'; end if;
  if not exists (select 1 from auth.users where id=p_user_id) then raise exception 'unknown authenticated user'; end if;
  perform pg_advisory_xact_lock(hashtextextended(p_user_id::text, 0));
  select p.company_id, p.id into v_company_id, v_profile_id from public.profiles p where p.user_id = p_user_id;
  if found then return query select false, v_company_id, v_profile_id; return; end if;
  insert into public.companies(name) values (trim(p_company_name)) returning id into v_company_id;
  if exists(select 1 from information_schema.columns where table_schema='public' and table_name='profiles' and column_name='name') then
    insert into public.profiles(user_id, company_id, email, full_name, name, role) values (p_user_id, v_company_id, coalesce(p_email,''), trim(p_name), trim(p_name), 'owner') returning id into v_profile_id;
  else
    insert into public.profiles(user_id, company_id, email, full_name, role) values (p_user_id, v_company_id, coalesce(p_email,''), trim(p_name), 'owner') returning id into v_profile_id;
  end if;
  return query select true, v_company_id, v_profile_id;
end;
$$;
revoke all on function public.onboard_user(uuid, text, text, text) from public, anon, authenticated;
grant execute on function public.onboard_user(uuid, text, text, text) to service_role;
commit;
