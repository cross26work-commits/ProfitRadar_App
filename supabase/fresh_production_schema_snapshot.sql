select jsonb_build_object(
  'tables', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'name', c.relname, 'rls', c.relrowsecurity, 'force_rls', c.relforcerowsecurity,
      'owner', pg_get_userbyid(c.relowner)
    ) order by c.relname), '[]'::jsonb)
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public' and c.relkind in ('r','p')
  ),
  'columns', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'table', c.relname, 'name', a.attname, 'type', pg_catalog.format_type(a.atttypid,a.atttypmod),
      'not_null', a.attnotnull, 'identity', a.attidentity, 'generated', a.attgenerated,
      'default', pg_catalog.pg_get_expr(d.adbin,d.adrelid)
    ) order by c.relname,a.attnum), '[]'::jsonb)
    from pg_catalog.pg_attribute a
    join pg_catalog.pg_class c on c.oid=a.attrelid
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    left join pg_catalog.pg_attrdef d on d.adrelid=a.attrelid and d.adnum=a.attnum
    where n.nspname='public' and c.relkind in ('r','p') and a.attnum>0 and not a.attisdropped
  ),
  'constraints', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'table', c.relname, 'name', x.conname, 'type', x.contype,
      'validated', x.convalidated, 'definition', pg_catalog.pg_get_constraintdef(x.oid,true)
    ) order by c.relname,x.conname), '[]'::jsonb)
    from pg_catalog.pg_constraint x
    join pg_catalog.pg_class c on c.oid=x.conrelid
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public'
  ),
  'indexes', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'table', t.relname, 'name', i.relname, 'unique', x.indisunique,
      'valid', x.indisvalid, 'ready', x.indisready, 'definition', pg_catalog.pg_get_indexdef(i.oid)
    ) order by t.relname,i.relname), '[]'::jsonb)
    from pg_catalog.pg_index x
    join pg_catalog.pg_class t on t.oid=x.indrelid
    join pg_catalog.pg_class i on i.oid=x.indexrelid
    join pg_catalog.pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public'
  ),
  'policies', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'table', tablename, 'name', policyname, 'permissive', permissive,
      'roles', roles, 'command', cmd, 'using', qual, 'check', with_check
    ) order by tablename,policyname), '[]'::jsonb)
    from pg_catalog.pg_policies where schemaname='public'
  ),
  'functions', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'identity', p.proname||'('||pg_catalog.pg_get_function_identity_arguments(p.oid)||')',
      'result', pg_catalog.pg_get_function_result(p.oid), 'owner', pg_get_userbyid(p.proowner),
      'security_definer', p.prosecdef, 'config', p.proconfig, 'acl', p.proacl,
      'body_md5', md5(p.prosrc)
    ) order by p.proname,pg_catalog.pg_get_function_identity_arguments(p.oid)), '[]'::jsonb)
    from pg_catalog.pg_proc p join pg_catalog.pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
  ),
  'triggers', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'table', c.relname, 'name', t.tgname, 'enabled', t.tgenabled,
      'definition', pg_catalog.pg_get_triggerdef(t.oid,true)
    ) order by c.relname,t.tgname), '[]'::jsonb)
    from pg_catalog.pg_trigger t
    join pg_catalog.pg_class c on c.oid=t.tgrelid
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public' and not t.tgisinternal
  ),
  'browser_table_grants', (
    select coalesce(jsonb_agg(jsonb_build_object(
      'grantee', grantee, 'table', table_name, 'privilege', privilege_type
    ) order by grantee,table_name,privilege_type), '[]'::jsonb)
    from information_schema.role_table_grants
    where table_schema='public' and grantee in ('anon','authenticated')
  )
)::text;
