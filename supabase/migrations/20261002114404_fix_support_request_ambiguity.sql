begin;

do $$
declare p pg_catalog.pg_proc%rowtype;
begin
  select * into p from pg_catalog.pg_proc
  where oid=to_regprocedure('public.create_support_request(text,uuid,uuid,text,text,text,text,text,text,text)');
  if not found
     or pg_catalog.pg_get_function_result(p.oid) <> 'TABLE(id uuid, public_request_id text, created_at timestamp with time zone)'
     or not p.prosecdef
     or p.proconfig is distinct from array['search_path=pg_catalog, pg_temp']::text[] then
    raise exception 'SUPPORT_FIX: create_support_request contract mismatch';
  end if;
end
$$;

create or replace function public.create_support_request(
  p_public_request_id text, p_requester_user_id uuid, p_company_id uuid,
  p_requester_name text, p_requester_email text, p_company_name text,
  p_category text, p_subject text, p_body text, p_abuse_key text
)
returns table(id uuid, public_request_id text, created_at timestamptz)
language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare created public.support_requests%rowtype;
begin
  if p_public_request_id !~ '^PR-[0-9]{8}-[A-F0-9]{12}$'
    or char_length(p_abuse_key) <> 64 then
    raise exception 'invalid request metadata';
  end if;
  perform pg_advisory_xact_lock(hashtextextended(p_abuse_key, 0));
  if (select count(*) from public.support_requests sr
      where sr.abuse_key = p_abuse_key
        and sr.created_at >= now() - interval '1 hour') >= 5 then
    raise exception 'rate limit exceeded' using errcode = 'P0001';
  end if;
  insert into public.support_requests(
    public_request_id, requester_user_id, company_id, requester_name,
    requester_email, company_name, category, subject, body, abuse_key
  ) values (
    p_public_request_id, p_requester_user_id, p_company_id, trim(p_requester_name),
    lower(trim(p_requester_email)), nullif(trim(p_company_name), ''),
    p_category, trim(p_subject), trim(p_body), p_abuse_key
  ) returning * into created;
  insert into public.support_messages(request_id, direction, subject, body, delivery_status)
  values(created.id, 'requester', created.subject, created.body, 'received');
  insert into public.support_audit_logs(request_id, action, metadata)
  values(created.id, 'request_created', jsonb_build_object('category', created.category));
  return query select created.id, created.public_request_id, created.created_at;
end $$;

revoke all on function public.create_support_request(text,uuid,uuid,text,text,text,text,text,text,text)
  from public,anon,authenticated;
grant execute on function public.create_support_request(text,uuid,uuid,text,text,text,text,text,text,text)
  to service_role;

commit;
