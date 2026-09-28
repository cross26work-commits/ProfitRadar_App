-- Fact capture only, not an approval gate. One result set; no remote execution by Codex.
-- The two existing legacy relations profiles and gmail_sync_runs must exist.
-- No customer values or function bodies are returned. prosrc is raw md5 only.
-- Save the complete result as JSON without editing; retain this SQL with the capture.
WITH
target_tables(name) AS (VALUES
 ('account_deletion_audit'),('account_deletion_jobs'),('ai_budget_reservations'),
 ('ai_judgements'),('ai_usage_runs'),('billing_checkout_attempts'),('billing_runtime_config'),
 ('billing_webhook_events'),('calendar_events'),('companies'),('company_billing'),
 ('conversation_analysis_snapshots'),('customers'),('financial_payments'),
 ('financial_record_history'),('financial_records'),('gmail_company_sync_runs'),
 ('gmail_connections'),('gmail_inbound_receipts'),('gmail_send_operations'),
 ('gmail_sync_cursors'),('gmail_sync_runs'),('gmail_work_locks'),('learning_logs'),
 ('messages'),('operation_recovery_audit'),('profiles'),('profit_events'),
 ('reply_drafts'),('reply_logs'),('timeline')
),
expected_functions(name) AS (VALUES
 ('commit_gmail_inbound_page'),('recover_company_work'),('save_financial_record'),
 ('reserve_ai_budget'),('company_is_active'),('request_account_deletion'),
 ('purge_account_data'),('complete_account_deletion'),('purge_expired_deletion_audit'),
 ('prevent_deleted_user_onboarding'),('record_financial_payment'),('void_financial_payment'),
 ('resolve_provider_uncertainty'),('promote_billing_live'),('acquire_gmail_sync_lock'),
 ('apply_billing_snapshot'),('claim_gmail_work'),('create_company_and_profile'),
 ('ensure_company_billing'),('finalize_gmail_send'),('onboard_user'),
 ('release_gmail_sync_lock'),('release_gmail_work'),('reserve_ai_run'),('rls_auto_enable')
),
constraint_rows AS (
 SELECT c.relname AS table_name,con.conname,con.contype,con.convalidated,
 pg_catalog.pg_get_constraintdef(con.oid,false) AS definition
 FROM pg_catalog.pg_constraint con JOIN pg_catalog.pg_class c ON c.oid=con.conrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 JOIN target_tables t ON t.name=c.relname WHERE n.nspname='public'
),
index_rows AS (
 SELECT c.relname AS table_name,i.relname AS index_name,x.indisunique,x.indisvalid,x.indisready,
 pg_catalog.pg_get_indexdef(x.indexrelid,0,false) AS definition
 FROM pg_catalog.pg_index x JOIN pg_catalog.pg_class c ON c.oid=x.indrelid
 JOIN pg_catalog.pg_class i ON i.oid=x.indexrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 JOIN target_tables t ON t.name=c.relname WHERE n.nspname='public'
),
function_rows AS (
 SELECT e.name,p.oid IS NOT NULL AS present,
 pg_catalog.pg_get_function_identity_arguments(p.oid) AS identity_arguments,
 pg_catalog.pg_get_function_result(p.oid) AS result,
 pg_catalog.pg_get_userbyid(p.proowner) AS owner,p.prosecdef,p.proconfig,p.proargnames,
 pg_catalog.md5(p.prosrc) AS prosrc_md5,p.proacl,
 pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM expected_functions e LEFT JOIN pg_catalog.pg_proc p
 ON p.pronamespace='public'::regnamespace AND p.proname=e.name
),
event_rows AS (
 SELECT e.evtname,e.evtevent,e.evtenabled,e.evttags,
 pg_catalog.pg_get_userbyid(e.evtowner) AS trigger_owner,
 pg_catalog.format('%I.%I(%s)',n.nspname,p.proname,
 pg_catalog.pg_get_function_identity_arguments(p.oid)) AS function_signature,
 pg_catalog.format_type(p.prorettype,NULL) AS return_type,
 pg_catalog.pg_get_userbyid(p.proowner) AS function_owner,p.prosecdef,p.proconfig,p.proacl,
 pg_catalog.md5(p.prosrc) AS prosrc_md5,
 pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM pg_catalog.pg_event_trigger e JOIN pg_catalog.pg_proc p ON p.oid=e.evtfoid
 JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
 WHERE e.evtname='ensure_rls' OR (n.nspname='public' AND p.proname='rls_auto_enable')
),
view_rows AS (
 SELECT n.nspname AS schema,c.relname AS name,c.relkind AS kind,c.reloptions AS options,
 pg_catalog.pg_get_userbyid(c.relowner) AS owner
 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relkind IN ('v','m')
),
trigger_rows AS (
 SELECT c.relname AS table_name,t.tgname AS trigger_name,t.tgenabled AS enabled,
 pg_catalog.format('%I.%I(%s)',fn.nspname,p.proname,
 pg_catalog.pg_get_function_identity_arguments(p.oid)) AS function_signature,
 pg_catalog.pg_get_triggerdef(t.oid,false) AS definition
 FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 JOIN pg_catalog.pg_proc p ON p.oid=t.tgfoid
 JOIN pg_catalog.pg_namespace fn ON fn.oid=p.pronamespace
 WHERE n.nspname='public' AND NOT t.tgisinternal
),
definer_rows AS (
 SELECT pg_catalog.format('%I.%I(%s)',n.nspname,p.proname,
 pg_catalog.pg_get_function_identity_arguments(p.oid)) AS function_signature,
 pg_catalog.pg_get_userbyid(p.proowner) AS owner,p.proconfig,p.proacl,
 pg_catalog.md5(p.prosrc) AS prosrc_md5
 FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public' AND p.prosecdef
),
sync_columns AS (
 SELECT a.attnum AS ordinal_position,a.attname AS column_name,
 pg_catalog.format_type(a.atttypid,a.atttypmod) AS data_type,t.typname AS udt_name,
 NOT a.attnotnull AS is_nullable,pg_catalog.pg_get_expr(d.adbin,d.adrelid,false) AS column_default,
 a.attidentity AS identity_kind,a.attgenerated AS generated_kind
 FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_type t ON t.oid=a.atttypid
 LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid=pg_catalog.to_regclass('public.gmail_sync_runs')
 AND a.attnum>0 AND NOT a.attisdropped
),
table_rows AS (
 SELECT t.name,c.oid IS NOT NULL AS present,c.relkind AS kind,
 pg_catalog.pg_get_userbyid(c.relowner) AS owner,c.relrowsecurity,c.relforcerowsecurity
 FROM target_tables t LEFT JOIN pg_catalog.pg_class c
 ON c.oid=pg_catalog.to_regclass('public.'||t.name)
),
snapshots(oracle_name,snapshot) AS (
 SELECT 'event_trigger',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.evtname COLLATE "C"),'[]'::jsonb) FROM event_rows r
 UNION ALL
 SELECT 'constraints',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.table_name COLLATE "C",r.conname COLLATE "C"),'[]'::jsonb) FROM constraint_rows r
 UNION ALL
 SELECT 'indexes',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.table_name COLLATE "C",r.index_name COLLATE "C"),'[]'::jsonb) FROM index_rows r
 UNION ALL
 SELECT 'functions',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.name COLLATE "C",r.identity_arguments COLLATE "C" NULLS FIRST),'[]'::jsonb) FROM function_rows r
 UNION ALL
 SELECT 'views',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.schema COLLATE "C",r.name COLLATE "C"),'[]'::jsonb) FROM view_rows r
 UNION ALL
 SELECT 'triggers',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.table_name COLLATE "C",r.trigger_name COLLATE "C"),'[]'::jsonb) FROM trigger_rows r
 UNION ALL
 SELECT 'security_definers',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.function_signature COLLATE "C"),'[]'::jsonb) FROM definer_rows r
 UNION ALL
 SELECT 'billing_runtime_config',pg_catalog.jsonb_build_object('present',pg_catalog.to_regclass('public.billing_runtime_config') IS NOT NULL)
 UNION ALL
 SELECT 'gmail_sync_runs',pg_catalog.jsonb_build_object(
 'columns',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.ordinal_position),'[]'::jsonb) FROM sync_columns r),
 'constraints',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.conname COLLATE "C"),'[]'::jsonb) FROM constraint_rows r WHERE r.table_name='gmail_sync_runs'),
 'indexes',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.index_name COLLATE "C"),'[]'::jsonb) FROM index_rows r WHERE r.table_name='gmail_sync_runs'),
 'total_rows',(SELECT pg_catalog.count(*) FROM public.gmail_sync_runs))
 UNION ALL
 SELECT 'profiles_identity',pg_catalog.jsonb_build_object(
 'null_user_id_count',(SELECT pg_catalog.count(*) FROM public.profiles WHERE user_id IS NULL),
 'duplicate_user_id_groups',(SELECT pg_catalog.count(*) FROM (SELECT user_id FROM public.profiles WHERE user_id IS NOT NULL GROUP BY user_id HAVING pg_catalog.count(*)>1) d))
 UNION ALL
 SELECT 'target_tables',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.name COLLATE "C"),'[]'::jsonb) FROM table_rows r
)
SELECT oracle_name,snapshot FROM snapshots ORDER BY oracle_name COLLATE "C";
