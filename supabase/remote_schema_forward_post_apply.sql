-- READ ONLY post-apply metadata and aggregate verification for v2.
-- Run only AFTER a separately approved transaction commits. No customer row values.
-- Compare business counts with the saved pre-apply counts; this query has no old counts.
WITH new_tables(name) AS (VALUES
 ('billing_checkout_attempts'),('gmail_sync_cursors'),('gmail_inbound_receipts'),
 ('operation_recovery_audit'),('financial_records'),('financial_record_history'),
 ('ai_budget_reservations'),('account_deletion_jobs'),('account_deletion_audit'),
 ('financial_payments'),('billing_runtime_config')
),
new_functions(name) AS (VALUES
 ('commit_gmail_inbound_page'),('recover_company_work'),('save_financial_record'),
 ('reserve_ai_budget'),('company_is_active'),('request_account_deletion'),
 ('purge_account_data'),('complete_account_deletion'),('purge_expired_deletion_audit'),
 ('prevent_deleted_user_onboarding'),('record_financial_payment'),('void_financial_payment'),
 ('resolve_provider_uncertainty'),('promote_billing_live')
),
checks(gate,ok,detail) AS (
 SELECT 'new_table_'||t.name,
 c.oid IS NOT NULL AND c.relkind='r' AND c.relrowsecurity AND NOT c.relforcerowsecurity
 AND pg_catalog.has_table_privilege('service_role',c.oid,'SELECT')
 AND NOT pg_catalog.has_table_privilege('anon',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
 AND NOT pg_catalog.has_table_privilege('authenticated',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
 AND NOT pg_catalog.has_any_column_privilege('anon',c.oid,'SELECT,INSERT,UPDATE,REFERENCES')
 AND NOT pg_catalog.has_any_column_privilege('authenticated',c.oid,'SELECT,INSERT,UPDATE,REFERENCES'),
 'table, RLS, effective table and column ACL'
 FROM new_tables t LEFT JOIN pg_catalog.pg_class c ON c.oid=pg_catalog.to_regclass('public.'||t.name)
 UNION ALL
 SELECT 'new_rpc_'||f.name,
 pg_catalog.count(p.oid)=1 AND pg_catalog.bool_and(p.prosecdef
 AND pg_catalog.pg_get_userbyid(p.proowner) IN ('postgres','supabase_admin')
 AND CASE WHEN f.name='prevent_deleted_user_onboarding' THEN
  NOT pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE')
  AND EXISTS(SELECT 1 FROM pg_catalog.pg_trigger t
   WHERE t.tgfoid=p.oid AND t.tgname='prevent_deleted_user_onboarding'
   AND t.tgrelid='public.profiles'::regclass AND t.tgenabled='O')
  ELSE pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE') END
 AND NOT pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE')
 AND NOT pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')),
 'single internal function; onboarding protection uses a trigger, not a service RPC'
 FROM new_functions f LEFT JOIN pg_catalog.pg_proc p
 ON p.pronamespace='public'::regnamespace AND p.proname=f.name GROUP BY f.name
 UNION ALL
 SELECT 'onboard_user',
 pg_catalog.count(p.oid)=1 AND pg_catalog.bool_and(p.proconfig=ARRAY['search_path=pg_catalog, pg_temp']
 AND pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE')
 AND NOT pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE')
 AND NOT pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')),
 'legacy RPC hardened; check exact signature/body against saved capture'
 FROM pg_catalog.pg_proc p WHERE p.pronamespace='public'::regnamespace AND p.proname='onboard_user'
 UNION ALL
 SELECT 'canonical_registration',
 pg_catalog.count(p.oid)=1 AND pg_catalog.bool_and(p.proconfig=ARRAY['search_path=pg_catalog, public']
 AND pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')
 AND NOT pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE')
 AND NOT pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE')),
 'canonical ACL/config; compare body with saved capture'
 FROM pg_catalog.pg_proc p WHERE p.pronamespace='public'::regnamespace
 AND p.proname='create_company_and_profile'
 UNION ALL
 SELECT 'legacy_browser_acl', NOT EXISTS (
  SELECT 1 FROM (VALUES ('companies'),('profiles'),('customers'),('messages'),
   ('profit_events'),('timeline'),('reply_logs'),('ai_judgements'),('learning_logs'),
   ('calendar_events'),('gmail_connections')) t(name)
  CROSS JOIN (VALUES ('anon'),('authenticated')) r(role)
  CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),
   ('REFERENCES'),('TRIGGER')) a(privilege)
  WHERE pg_catalog.has_table_privilege(r.role,pg_catalog.to_regclass('public.'||t.name),a.privilege)
  IS DISTINCT FROM (r.role='authenticated' AND t.name IN ('companies','profiles') AND a.privilege='SELECT')
 ) AND NOT EXISTS (
  SELECT 1 FROM (VALUES ('companies'),('profiles'),('customers'),('messages'),
   ('profit_events'),('timeline'),('reply_logs'),('ai_judgements'),('learning_logs'),
   ('calendar_events'),('gmail_connections')) t(name)
  WHERE pg_catalog.has_any_column_privilege('anon',pg_catalog.to_regclass('public.'||t.name),
   'SELECT,INSERT,UPDATE,REFERENCES')
  OR pg_catalog.has_any_column_privilege('authenticated',pg_catalog.to_regclass('public.'||t.name),
   'INSERT,UPDATE,REFERENCES')
  OR (t.name NOT IN ('companies','profiles') AND pg_catalog.has_any_column_privilege(
   'authenticated',pg_catalog.to_regclass('public.'||t.name),'SELECT'))
 ), 'browser effective table/column privileges; compare four-policy oracle separately'
 UNION ALL
 SELECT 'legacy_global_sync_unchanged',
 (SELECT pg_catalog.count(*)=0 FROM public.gmail_sync_runs)
 AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_attribute WHERE attrelid='public.gmail_sync_runs'::regclass
 AND attname='company_id' AND attnum>0 AND NOT attisdropped),
 'global aggregate remains empty and has no tenant column'
 UNION ALL
 SELECT 'billing_test',
 (SELECT pg_catalog.count(*)=1 AND pg_catalog.bool_and(mode='test') FROM public.billing_runtime_config),
 'production billing not enabled'
),
results AS (SELECT gate,CASE WHEN ok IS TRUE THEN 'PASS' ELSE 'STOP' END AS status,detail FROM checks)
SELECT gate,status,detail FROM (
 SELECT 0 AS ordering,gate,status,detail FROM results
 UNION ALL
 SELECT 1,'FINAL',CASE WHEN EXISTS(SELECT 1 FROM results WHERE status='STOP') THEN 'STOP' ELSE 'PASS' END,
 'SQL metadata checks only; compare stored pre-apply counts and run authenticated E2E separately'
) output ORDER BY ordering,gate;
