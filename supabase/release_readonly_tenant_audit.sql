-- READ ONLY: run each numbered query separately. No customer rows or token values are selected.
-- 01 Expected table names and existence.
select expected_table, to_regclass('public.'||expected_table) is not null as exists
from unnest(array['companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections']) expected_table;
-- 02 Required column names/types/nullability/defaults.
select table_name,column_name,data_type,udt_name,is_nullable,column_default from information_schema.columns
where table_schema='public' and table_name in ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections') order by table_name,ordinal_position;
-- 03 PK, unique, FK and indexes.
select tc.table_name,tc.constraint_name,tc.constraint_type,string_agg(kcu.column_name,', ' order by kcu.ordinal_position) columns,ccu.table_name referenced_table
from information_schema.table_constraints tc left join information_schema.key_column_usage kcu on(tc.constraint_name=kcu.constraint_name and tc.table_schema=kcu.table_schema)
left join information_schema.constraint_column_usage ccu on(tc.constraint_name=ccu.constraint_name and tc.table_schema=ccu.table_schema)
where tc.table_schema='public' and tc.table_name in ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections')
group by tc.table_name,tc.constraint_name,tc.constraint_type,ccu.table_name order by tc.table_name,tc.constraint_type;
select tablename,indexname,indexdef from pg_indexes where schemaname='public' and tablename in ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections') order by tablename,indexname;
-- 04 Profile integrity counts only; no user IDs are returned.
select (select count(*) from public.profiles where user_id is null) null_user_id_count,
       (select count(*) from (select user_id from public.profiles where user_id is not null group by user_id having count(*)>1) d) duplicate_user_id_group_count;
-- 05 RLS and policy USING/WITH CHECK.
select c.relname table_name,c.relrowsecurity rls_enabled,c.relforcerowsecurity force_rls from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections') order by c.relname;
select schemaname,tablename,policyname,roles,cmd,qual,with_check from pg_policies where schemaname='public' order by tablename,policyname;
-- 06 Table/column/schema role privileges and role inheritance.
select grantee,table_name,privilege_type from information_schema.role_table_grants where table_schema='public' and grantee in('PUBLIC','anon','authenticated','service_role') order by table_name,grantee,privilege_type;
select grantee,table_name,column_name,privilege_type from information_schema.column_privileges where table_schema='public' and grantee in('PUBLIC','anon','authenticated','service_role') order by table_name,column_name,grantee;
select grantee,privilege_type from information_schema.role_usage_grants where object_schema='public' and grantee in('PUBLIC','anon','authenticated','service_role') order by grantee;
select rolname,rolinherit from pg_roles where rolname in('anon','authenticated','service_role','public') order by rolname;
-- PUBLIC is an ACL pseudo-role (OID 0), not a pg_roles name.
select exists(select 1 from pg_namespace n cross join lateral aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a where n.nspname='public' and a.grantee=0 and a.privilege_type='CREATE') public_can_create_in_public;
-- 07 Views, triggers, SECURITY DEFINER functions that may bypass direct table policy.
select table_name from information_schema.views where table_schema='public' order by table_name;
select event_object_table table_name,trigger_name,event_manipulation from information_schema.triggers where event_object_schema='public' order by event_object_table,trigger_name;
select p.oid::regprocedure signature,p.prosecdef security_definer,pg_get_userbyid(p.proowner) owner,p.proconfig,
exists(select 1 from aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a where a.grantee=0 and a.privilege_type='EXECUTE') public_execute
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.prosecdef order by signature;

-- 09 Effective privileges include PUBLIC and inherited grants; column grants
-- are reported independently from table-wide rights. These are metadata only.
select c.relname, r.rolname, op,
has_table_privilege(r.oid,c.oid,op) allowed
from pg_class c join pg_namespace n on n.oid=c.relnamespace
cross join pg_roles r cross join unnest(array['SELECT','INSERT','UPDATE','DELETE']) op
where n.nspname='public' and c.relkind in ('r','v','m','p')
and r.rolname in ('anon','authenticated','service_role') order by c.relname,r.rolname,op;
select c.relname,a.attname,r.rolname,op,has_column_privilege(r.oid,c.oid,a.attnum,op) allowed
from pg_class c join pg_namespace n on n.oid=c.relnamespace
join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
cross join pg_roles r cross join unnest(array['SELECT','INSERT','UPDATE','REFERENCES']) op
where n.nspname='public' and c.relkind in ('r','v','p') and r.rolname in ('anon','authenticated')
order by c.relname,a.attnum,r.rolname,op;
select member::regrole member,roleid::regrole inherited_role,admin_option from pg_auth_members order by member,roleid;
-- 10 Index validity, readiness, key columns, predicate and expression.
select i.indexrelid::regclass index_name,i.indrelid::regclass table_name,
i.indisunique,i.indisvalid,i.indisready,i.indkey,
pg_get_indexdef(i.indexrelid) definition,pg_get_expr(i.indpred,i.indrelid) predicate
from pg_index i join pg_class c on c.oid=i.indrelid join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' order by table_name,index_name;
-- 08 All onboard_user overloads, definitions and grants.
select p.oid::regprocedure signature,pg_get_function_identity_arguments(p.oid) arguments,pg_get_function_result(p.oid) returns,p.prosecdef security_definer,pg_get_userbyid(p.proowner) owner,p.proconfig,pg_get_functiondef(p.oid) function_definition from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='onboard_user' order by signature;
select routine_name,specific_name,grantee,privilege_type from information_schema.routine_privileges where routine_schema='public' and routine_name='onboard_user' order by specific_name,grantee;
