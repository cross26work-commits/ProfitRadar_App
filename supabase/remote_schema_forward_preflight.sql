-- READ ONLY. Remote execution is for a human-reviewed later step; NOT run by this task.
-- Each numbered SELECT can be run individually in SQL Editor.
-- No customer/mail/token rows or function bodies are returned.
-- Retain full schema/ACL/function backup separately: these summaries are NOT a rollback backup.

-- V2-0. Legacy onboarding prerequisite: never create/guess this remote column.
-- User-provided read-only evidence, 2026-09-15: uuid, nullable YES,
-- default auth.uid(), identity NO, generated NEVER. Not remotely re-read by agent.
SELECT 'companies.owner_user_id' AS prerequisite,
 CASE WHEN a.atttypid='uuid'::regtype THEN 'COMPATIBLE' ELSE 'MISSING_OR_INCOMPATIBLE' END AS status,
 format_type(a.atttypid,a.atttypmod) AS actual_type,a.attnotnull,
 pg_get_expr(d.adbin,d.adrelid) AS column_default,a.attidentity,a.attgenerated
 FROM (SELECT to_regclass('public.companies') oid) t
 LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname='owner_user_id' AND NOT a.attisdropped
 LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum;

-- V2-A. Checkout structural compatibility; ACL is reported separately because
-- the approved forward normalizes legacy service-role default privileges.
WITH target AS (SELECT to_regclass('public.billing_checkout_attempts') AS oid),
expected(name,type_name,required,default_expr) AS (VALUES
 ('company_id','uuid',true,NULL::text),('attempt_id','uuid',true,NULL::text),
 ('session_id','text',false,NULL::text),('created_at','timestamptz',true,'now()'))
SELECT CASE WHEN t.oid IS NULL THEN 'MISSING'
 WHEN (SELECT relkind FROM pg_class WHERE oid=t.oid)<>'r'
 OR (SELECT count(*) FROM pg_attribute WHERE attrelid=t.oid AND attnum>0 AND NOT attisdropped)<>4
 OR EXISTS(SELECT 1 FROM expected e LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname=e.name AND NOT a.attisdropped
   LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
   WHERE a.attnum IS NULL OR a.atttypid IS DISTINCT FROM to_regtype('pg_catalog.'||e.type_name)::oid
   OR a.attnotnull IS DISTINCT FROM e.required OR pg_get_expr(d.adbin,d.adrelid) IS DISTINCT FROM e.default_expr)
 OR (SELECT count(*) FROM pg_constraint WHERE conrelid=t.oid)<>2
 OR NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid=t.oid AND contype='p' AND convalidated
   AND conkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid=t.oid AND attname='company_id')]::smallint[])
 OR NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid=t.oid AND contype='f' AND convalidated
   AND confrelid=to_regclass('public.companies') AND confdeltype='a' AND confupdtype='a'
   AND conkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid=t.oid AND attname='company_id')]::smallint[]
   AND confkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid=to_regclass('public.companies') AND attname='id')]::smallint[])
 OR (SELECT count(*) FROM pg_index WHERE indrelid=t.oid)<>1
 OR EXISTS(SELECT 1 FROM pg_index WHERE indrelid=t.oid AND (NOT indisvalid OR NOT indisready OR NOT indisunique OR NOT indisprimary))
 THEN 'INCOMPATIBLE' ELSE 'COMPATIBLE' END AS checkout_structure,
 (SELECT relrowsecurity FROM pg_class WHERE oid=t.oid) AS rls_enabled,
 (SELECT count(*) FROM pg_policy WHERE polrelid=t.oid) AS policy_count,
 has_any_column_privilege('anon',t.oid,'SELECT,INSERT,UPDATE,REFERENCES') AS anon_column_access,
 has_any_column_privilege('authenticated',t.oid,'SELECT,INSERT,UPDATE,REFERENCES') AS authenticated_column_access,
 has_table_privilege('service_role',t.oid,'SELECT') AS service_select,
 has_table_privilege('service_role',t.oid,'INSERT') AS service_insert,
 has_table_privilege('service_role',t.oid,'UPDATE') AS service_update,
 has_table_privilege('service_role',t.oid,'DELETE,TRUNCATE,TRIGGER,REFERENCES') AS service_extra_privileges
 FROM target t;

-- V2-B. Exact body/argument/config metadata pin; ACL/effective rights also below.
WITH expected(name,args,result,body,config) AS (VALUES
('onboard_user',ARRAY['p_user_id','p_company_name','p_name','p_email'],'jsonb'::regtype,$legacy_body$
declare
    v_existing_profile public.profiles%rowtype;
    v_company public.companies%rowtype;
    v_profile public.profiles%rowtype;
begin
    select *
    into v_existing_profile
    from public.profiles
    where user_id = p_user_id
    limit 1;

    if found then
        return jsonb_build_object(
            'created', false,
            'company_id', v_existing_profile.company_id,
            'profile_id', v_existing_profile.id
        );
    end if;

    insert into public.companies (
        name,
        plan,
        owner_user_id
    )
    values (
        trim(p_company_name),
        'free',
        p_user_id
    )
    returning *
    into v_company;

    insert into public.profiles (
        user_id,
        company_id,
        name,
        role,
        email
    )
    values (
        p_user_id,
        v_company.id,
        trim(p_name),
        'owner',
        p_email
    )
    returning *
    into v_profile;

    return jsonb_build_object(
        'created', true,
        'company_id', v_company.id,
        'profile_id', v_profile.id
    );
end;
$legacy_body$,ARRAY['search_path=public']),
('create_company_and_profile',ARRAY['company_name','owner_name'],'uuid'::regtype,$canonical_body$
declare
  new_company_id uuid;
  caller_email text;
begin
  if auth.uid() is null then
    raise exception 'Authentication required';
  end if;
  if nullif(trim(company_name), '') is null or nullif(trim(owner_name), '') is null then
    raise exception 'Company name and owner name are required';
  end if;
  if exists (select 1 from public.profiles where user_id = auth.uid()) then
    raise exception 'Profile already exists';
  end if;

  caller_email := coalesce(auth.jwt() ->> 'email', '');
  insert into public.companies(name, plan)
    values (trim(company_name), 'free') returning id into new_company_id;
  insert into public.profiles(user_id, company_id, name, full_name, email, role)
    values (auth.uid(), new_company_id, trim(owner_name), trim(owner_name), caller_email, 'owner');
  return new_company_id;
end;
$canonical_body$,ARRAY['search_path=pg_catalog, public']))
SELECT e.name, CASE WHEN p.oid IS NULL THEN 'MISSING'
 WHEN (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=e.name)<>1
 OR p.proowner<>'postgres'::regrole OR NOT p.prosecdef OR p.prolang<>(SELECT oid FROM pg_language WHERE lanname='plpgsql')
 OR p.proargnames IS DISTINCT FROM e.args OR p.prorettype<>e.result OR p.proretset
 OR replace(p.prosrc,chr(13)||chr(10),chr(10))<>replace(e.body,chr(13)||chr(10),chr(10))
 OR p.proconfig IS DISTINCT FROM e.config THEN 'UNKNOWN_OR_HARDENED_REVIEW_ACL'
 ELSE 'EXACT_CAPTURED_BODY_AND_CONTRACT' END AS identity,
 p.proconfig,p.proacl,pg_get_function_identity_arguments(p.oid) AS arguments,
 has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
FROM expected e LEFT JOIN pg_proc p ON p.pronamespace='public'::regnamespace AND p.proname=e.name;

-- V2-C. Event triggers are not ordinary RPCs. Read metadata, do not REVOKE.
SELECT e.evtname,e.evtevent,e.evtenabled,e.evttags,pg_get_userbyid(e.evtowner) AS trigger_owner,
 p.oid::regprocedure AS function,p.prorettype::regtype AS return_type,
 pg_get_userbyid(p.proowner) AS function_owner,p.prosecdef,p.proconfig,p.proacl,
 has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute
 FROM pg_event_trigger e JOIN pg_proc p ON p.oid=e.evtfoid
 WHERE e.evtname='ensure_rls' OR (p.pronamespace='public'::regnamespace AND p.proname='rls_auto_enable');

-- 1. Expected tables, existence, owner, RLS, kind. Missing is reported, not hidden.
WITH targets(name) AS (VALUES ('account_deletion_audit'),('account_deletion_jobs'),('ai_budget_reservations'),('ai_judgements'),('ai_usage_runs'),('billing_checkout_attempts'),('billing_runtime_config'),('billing_webhook_events'),('calendar_events'),('companies'),('company_billing'),('conversation_analysis_snapshots'),('customers'),('financial_payments'),('financial_record_history'),('financial_records'),('gmail_company_sync_runs'),('gmail_connections'),('gmail_inbound_receipts'),('gmail_send_operations'),('gmail_sync_cursors'),('gmail_sync_runs'),('gmail_work_locks'),('learning_logs'),('messages'),('operation_recovery_audit'),('profiles'),('profit_events'),('reply_drafts'),('reply_logs'),('timeline'))
SELECT t.name,c.relkind,pg_get_userbyid(c.relowner) AS owner,c.relrowsecurity,c.relforcerowsecurity,
 c.oid IS NOT NULL AS present FROM targets t LEFT JOIN pg_class c ON c.oid=to_regclass('public.'||t.name)
ORDER BY t.name;

-- 2. Release-baseline column/type/null/default metadata. Missing columns stay visible.
WITH expected(table_name,column_name,type_name) AS (VALUES
('account_deletion_audit','id','uuid'),
('account_deletion_audit','job_id','uuid'),
('account_deletion_audit','stage','text'),
('account_deletion_audit','created_at','timestamptz'),
('account_deletion_jobs','id','uuid'),
('account_deletion_jobs','company_id','uuid'),
('account_deletion_jobs','user_id','uuid'),
('account_deletion_jobs','status','text'),
('account_deletion_jobs','gmail_done','bool'),
('account_deletion_jobs','billing_done','bool'),
('account_deletion_jobs','billing_reference','text'),
('account_deletion_jobs','last_error_code','text'),
('account_deletion_jobs','requested_at','timestamptz'),
('account_deletion_jobs','completed_at','timestamptz'),
('account_deletion_jobs','purge_after','timestamptz'),
('ai_budget_reservations','id','uuid'),
('ai_budget_reservations','company_id','uuid'),
('ai_budget_reservations','model','text'),
('ai_budget_reservations','reserved_tokens','int8'),
('ai_budget_reservations','reserved_cost_micro_usd','int8'),
('ai_budget_reservations','token_limit','int8'),
('ai_budget_reservations','cost_limit_micro_usd','int8'),
('ai_budget_reservations','status','text'),
('ai_budget_reservations','actual_input_tokens','int8'),
('ai_budget_reservations','actual_output_tokens','int8'),
('ai_budget_reservations','created_at','timestamptz'),
('ai_judgements','id','uuid'),
('ai_judgements','company_id','uuid'),
('ai_judgements','customer_id','uuid'),
('ai_judgements','profit_event_id','uuid'),
('ai_judgements','provider','text'),
('ai_judgements','score','int4'),
('ai_judgements','priority','text'),
('ai_judgements','risk','text'),
('ai_judgements','reason','text'),
('ai_judgements','next_action','text'),
('ai_judgements','raw_input','jsonb'),
('ai_judgements','raw_output','jsonb'),
('ai_judgements','created_at','timestamptz'),
('ai_usage_runs','id','uuid'),
('ai_usage_runs','company_id','uuid'),
('ai_usage_runs','status','text'),
('ai_usage_runs','created_at','timestamptz'),
('ai_usage_runs','elapsed_ms','int4'),
('ai_usage_runs','input_tokens','int4'),
('ai_usage_runs','output_tokens','int4'),
('ai_usage_runs','cost_usd','numeric'),
('billing_checkout_attempts','company_id','uuid'),
('billing_checkout_attempts','attempt_id','uuid'),
('billing_checkout_attempts','session_id','text'),
('billing_checkout_attempts','created_at','timestamptz'),
('billing_runtime_config','singleton','bool'),
('billing_runtime_config','mode','text'),
('billing_runtime_config','approval_ref','text'),
('billing_runtime_config','approved_at','timestamptz'),
('billing_webhook_events','event_id','text'),
('billing_webhook_events','company_id','uuid'),
('billing_webhook_events','processed_at','timestamptz'),
('calendar_events','id','uuid'),
('calendar_events','company_id','uuid'),
('calendar_events','customer_id','uuid'),
('calendar_events','profit_event_id','uuid'),
('calendar_events','provider','text'),
('calendar_events','title','text'),
('calendar_events','description','text'),
('calendar_events','meeting_url','text'),
('calendar_events','external_id','text'),
('calendar_events','starts_at','timestamptz'),
('calendar_events','ends_at','timestamptz'),
('calendar_events','created_at','timestamptz'),
('companies','id','uuid'),
('companies','name','text'),
('companies','plan','text'),
('companies','created_at','timestamptz'),
('company_billing','company_id','uuid'),
('company_billing','trial_ends_at','timestamptz'),
('company_billing','status','text'),
('company_billing','stripe_subscription_id','text'),
('company_billing','paid_until','timestamptz'),
('company_billing','updated_at','timestamptz'),
('conversation_analysis_snapshots','id','uuid'),
('conversation_analysis_snapshots','company_id','uuid'),
('conversation_analysis_snapshots','profit_event_id','uuid'),
('conversation_analysis_snapshots','analysis_version','text'),
('conversation_analysis_snapshots','payload','jsonb'),
('conversation_analysis_snapshots','provider','text'),
('conversation_analysis_snapshots','model','text'),
('conversation_analysis_snapshots','created_at','timestamptz'),
('customers','id','uuid'),
('customers','company_id','uuid'),
('customers','name','text'),
('customers','email','text'),
('customers','phone','text'),
('customers','company_name','text'),
('customers','status','text'),
('customers','total_estimated_profit','int8'),
('customers','total_actual_profit','int8'),
('customers','last_contact_at','timestamptz'),
('customers','created_at','timestamptz'),
('customers','updated_at','timestamptz'),
('financial_payments','id','uuid'),
('financial_payments','company_id','uuid'),
('financial_payments','profit_event_id','uuid'),
('financial_payments','customer_id','uuid'),
('financial_payments','amount','int8'),
('financial_payments','paid_at','timestamptz'),
('financial_payments','created_by','uuid'),
('financial_payments','created_at','timestamptz'),
('financial_payments','voided_at','timestamptz'),
('financial_payments','voided_by','uuid'),
('financial_payments','void_reason','text'),
('financial_record_history','id','uuid'),
('financial_record_history','company_id','uuid'),
('financial_record_history','profit_event_id','uuid'),
('financial_record_history','actor_id','uuid'),
('financial_record_history','version','int8'),
('financial_record_history','previous_record','jsonb'),
('financial_record_history','new_record','jsonb'),
('financial_record_history','created_at','timestamptz'),
('financial_records','company_id','uuid'),
('financial_records','profit_event_id','uuid'),
('financial_records','customer_id','uuid'),
('financial_records','expected_revenue','int8'),
('financial_records','ordered_revenue','int8'),
('financial_records','paid_amount','int8'),
('financial_records','cost','int8'),
('financial_records','occurred_at','timestamptz'),
('financial_records','confirmed_at','timestamptz'),
('financial_records','paid_at','timestamptz'),
('financial_records','source','text'),
('financial_records','created_by','uuid'),
('financial_records','version','int8'),
('financial_records','updated_at','timestamptz'),
('gmail_company_sync_runs','id','uuid'),
('gmail_company_sync_runs','company_id','uuid'),
('gmail_company_sync_runs','status','text'),
('gmail_company_sync_runs','started_at','timestamptz'),
('gmail_company_sync_runs','finished_at','timestamptz'),
('gmail_company_sync_runs','error_code','text'),
('gmail_company_sync_runs','detected_count','int4'),
('gmail_connections','id','uuid'),
('gmail_connections','company_id','uuid'),
('gmail_connections','profile_id','uuid'),
('gmail_connections','email','text'),
('gmail_connections','token_json','jsonb'),
('gmail_connections','status','text'),
('gmail_connections','last_synced_at','timestamptz'),
('gmail_connections','created_at','timestamptz'),
('gmail_connections','updated_at','timestamptz'),
('gmail_inbound_receipts','company_id','uuid'),
('gmail_inbound_receipts','mailbox','text'),
('gmail_inbound_receipts','gmail_message_id','text'),
('gmail_inbound_receipts','profit_event_id','uuid'),
('gmail_inbound_receipts','outcome','text'),
('gmail_inbound_receipts','created_at','timestamptz'),
('gmail_send_operations','company_id','uuid'),
('gmail_send_operations','profit_event_id','uuid'),
('gmail_send_operations','customer_id','uuid'),
('gmail_send_operations','operation_id','text'),
('gmail_send_operations','request_hash','text'),
('gmail_send_operations','status','text'),
('gmail_send_operations','recipient','text'),
('gmail_send_operations','subject','text'),
('gmail_send_operations','body','text'),
('gmail_send_operations','gmail_message_id','text'),
('gmail_send_operations','gmail_thread_id','text'),
('gmail_send_operations','created_at','timestamptz'),
('gmail_send_operations','updated_at','timestamptz'),
('gmail_sync_cursors','company_id','uuid'),
('gmail_sync_cursors','mailbox','text'),
('gmail_sync_cursors','version','int8'),
('gmail_sync_cursors','mode','text'),
('gmail_sync_cursors','history_id','text'),
('gmail_sync_cursors','page_token','text'),
('gmail_sync_cursors','initial_since','int8'),
('gmail_sync_cursors','pending_ids','jsonb'),
('gmail_sync_cursors','pending_page','jsonb'),
('gmail_sync_cursors','last_page_at','timestamptz'),
('gmail_sync_cursors','last_successful_sync','timestamptz'),
('gmail_sync_runs','id','uuid'),
('gmail_sync_runs','status','text'),
('gmail_sync_runs','started_at','timestamptz'),
('gmail_sync_runs','finished_at','timestamptz'),
('gmail_work_locks','company_id','uuid'),
('gmail_work_locks','owner_id','uuid'),
('gmail_work_locks','purpose','text'),
('gmail_work_locks','acquired_at','timestamptz'),
('learning_logs','id','uuid'),
('learning_logs','company_id','uuid'),
('learning_logs','customer_id','uuid'),
('learning_logs','profit_event_id','uuid'),
('learning_logs','event_type','text'),
('learning_logs','input_data','jsonb'),
('learning_logs','result_data','jsonb'),
('learning_logs','success','bool'),
('learning_logs','actual_profit','int8'),
('learning_logs','created_at','timestamptz'),
('messages','id','uuid'),
('messages','company_id','uuid'),
('messages','customer_id','uuid'),
('messages','channel','text'),
('messages','direction','text'),
('messages','sender','text'),
('messages','recipient','text'),
('messages','subject','text'),
('messages','body','text'),
('messages','external_id','text'),
('messages','thread_id','text'),
('messages','sent_at','timestamptz'),
('messages','received_at','timestamptz'),
('messages','created_at','timestamptz'),
('operation_recovery_audit','id','uuid'),
('operation_recovery_audit','company_id','uuid'),
('operation_recovery_audit','owner_id','uuid'),
('operation_recovery_audit','purpose','text'),
('operation_recovery_audit','operator_ref','text'),
('operation_recovery_audit','ticket_ref','text'),
('operation_recovery_audit','stopped_workers_confirmed','bool'),
('operation_recovery_audit','recovered_at','timestamptz'),
('profiles','id','uuid'),
('profiles','user_id','uuid'),
('profiles','company_id','uuid'),
('profiles','email','text'),
('profiles','full_name','text'),
('profiles','role','text'),
('profiles','created_at','timestamptz'),
('profiles','name','text'),
('profit_events','id','uuid'),
('profit_events','company_id','uuid'),
('profit_events','customer_id','uuid'),
('profit_events','source_message_id','uuid'),
('profit_events','title','text'),
('profit_events','status','text'),
('profit_events','category','text'),
('profit_events','estimated_profit','int8'),
('profit_events','actual_profit','int8'),
('profit_events','opportunity_score','int4'),
('profit_events','roi_score','int4'),
('profit_events','hot_lead','bool'),
('profit_events','risk_level','text'),
('profit_events','next_action','text'),
('profit_events','due_at','timestamptz'),
('profit_events','closed_at','timestamptz'),
('profit_events','created_at','timestamptz'),
('profit_events','updated_at','timestamptz'),
('profit_events','gmail_thread_id','text'),
('profit_events','last_gmail_message_id','text'),
('profit_events','recoverable_profit','int8'),
('profit_events','neglected_days','int4'),
('profit_events','description','text'),
('reply_drafts','company_id','uuid'),
('reply_drafts','profit_event_id','uuid'),
('reply_drafts','body','text'),
('reply_drafts','subject','text'),
('reply_drafts','updated_at','timestamptz'),
('reply_logs','id','uuid'),
('reply_logs','company_id','uuid'),
('reply_logs','customer_id','uuid'),
('reply_logs','profit_event_id','uuid'),
('reply_logs','message_id','uuid'),
('reply_logs','channel','text'),
('reply_logs','reply_body','text'),
('reply_logs','reply_at','timestamptz'),
('reply_logs','detected_at','timestamptz'),
('reply_logs','external_id','text'),
('reply_logs','thread_id','text'),
('reply_logs','created_at','timestamptz'),
('reply_logs','gmail_message_id','text'),
('reply_logs','gmail_thread_id','text'),
('timeline','id','uuid'),
('timeline','company_id','uuid'),
('timeline','customer_id','uuid'),
('timeline','profit_event_id','uuid'),
('timeline','event_type','text'),
('timeline','channel','text'),
('timeline','title','text'),
('timeline','description','text'),
('timeline','amount','int8'),
('timeline','occurred_at','timestamptz'),
('timeline','metadata','jsonb'),
('timeline','created_at','timestamptz'))
SELECT e.*,a.atttypid::regtype AS actual_type,a.attnotnull,pg_get_expr(d.adbin,d.adrelid) AS default_expression,
 a.attnum IS NOT NULL AS present FROM expected e
 LEFT JOIN pg_attribute a ON a.attrelid=to_regclass('public.'||e.table_name) AND a.attname=e.column_name AND a.attnum>0 AND NOT a.attisdropped
 LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum ORDER BY 1,2;

-- 2B. Four approved forward additions. Missing is ADD_NULLABLE, never silently PASS.
WITH expected(t,c,typ) AS (VALUES
 ('profit_events','description','text'),('profit_events','neglected_days','int4'),('profit_events','recoverable_profit','int8'))
SELECT e.*,CASE WHEN a.attnum IS NULL THEN 'ADD_NULLABLE'
 WHEN a.atttypid=to_regtype(e.typ) AND a.atttypmod=-1 AND NOT a.attnotnull AND d.adbin IS NULL
 AND a.attidentity='' AND a.attgenerated='' THEN 'COMPATIBLE' ELSE 'STOP_COLUMN_DRIFT' END AS decision
FROM expected e LEFT JOIN pg_attribute a ON a.attrelid=to_regclass('public.'||e.t) AND a.attname=e.c AND NOT a.attisdropped
LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum;
-- Removed over-prerequisites: companies.updated_at, profiles.updated_at,
-- gmail_sync_runs.error_code/detected_count. Current scheduler uses gmail_company_sync_runs.

-- 3. Constraints/indexes: definition, readiness/validity, not just index names.
SELECT c.relname AS table_name,con.conname,con.contype,con.convalidated,pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid WHERE c.relnamespace='public'::regnamespace
 AND c.relname IN ('account_deletion_audit','account_deletion_jobs','ai_budget_reservations','ai_judgements','ai_usage_runs','billing_checkout_attempts','billing_runtime_config','billing_webhook_events','calendar_events','companies','company_billing','conversation_analysis_snapshots','customers','financial_payments','financial_record_history','financial_records','gmail_company_sync_runs','gmail_connections','gmail_inbound_receipts','gmail_send_operations','gmail_sync_cursors','gmail_sync_runs','gmail_work_locks','learning_logs','messages','operation_recovery_audit','profiles','profit_events','reply_drafts','reply_logs','timeline') ORDER BY 1,2;
SELECT t.relname AS table_name,i.relname AS index_name,x.indisunique,x.indisvalid,x.indisready,
 pg_get_indexdef(x.indexrelid) AS definition FROM pg_index x JOIN pg_class t ON t.oid=x.indrelid
 JOIN pg_class i ON i.oid=x.indexrelid WHERE t.relnamespace='public'::regnamespace
 AND t.relname IN ('account_deletion_audit','account_deletion_jobs','ai_budget_reservations','ai_judgements','ai_usage_runs','billing_checkout_attempts','billing_runtime_config','billing_webhook_events','calendar_events','companies','company_billing','conversation_analysis_snapshots','customers','financial_payments','financial_record_history','financial_records','gmail_company_sync_runs','gmail_connections','gmail_inbound_receipts','gmail_send_operations','gmail_sync_cursors','gmail_sync_runs','gmail_work_locks','learning_logs','messages','operation_recovery_audit','profiles','profit_events','reply_drafts','reply_logs','timeline') ORDER BY 1,2;

-- 4. All policies and explicit table/column grants, including PUBLIC/custom roles.
-- Authoritative 4-policy oracle. No role/qual/with_check/name relaxation.
WITH expected AS (SELECT $policy_oracle$[{"cmd":"INSERT","qual":null,"roles":["authenticated"],"tablename":"companies","permissive":"PERMISSIVE","policyname":"companies_insert_own","schemaname":"public","with_check":"(owner_user_id = auth.uid())"},{"cmd":"SELECT","qual":"((owner_user_id = auth.uid()) OR (EXISTS ( SELECT 1\n   FROM profiles\n  WHERE ((profiles.company_id = companies.id) AND (profiles.user_id = auth.uid())))))","roles":["authenticated"],"tablename":"companies","permissive":"PERMISSIVE","policyname":"companies_select_member_or_owner","schemaname":"public","with_check":null},{"cmd":"SELECT","qual":"(user_id = auth.uid())","roles":["authenticated"],"tablename":"profiles","permissive":"PERMISSIVE","policyname":"profiles_select_own","schemaname":"public","with_check":null},{"cmd":"UPDATE","qual":"(user_id = auth.uid())","roles":["authenticated"],"tablename":"profiles","permissive":"PERMISSIVE","policyname":"profiles_update_own","schemaname":"public","with_check":null}]$policy_oracle$::jsonb snapshot),
actual AS (SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY p.tablename,p.policyname),'[]'::jsonb) snapshot
 FROM pg_policies p WHERE schemaname='public' AND tablename IN ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections'))
SELECT CASE WHEN actual.snapshot=expected.snapshot THEN 'EXACT_REMOTE_POLICY_MATCH' ELSE 'STOP_POLICY_DRIFT' END AS policy_gate,
 actual.snapshot AS observed FROM actual CROSS JOIN expected;
SELECT * FROM pg_policies WHERE schemaname='public' ORDER BY tablename,policyname;
SELECT c.relname,a.grantee,CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END AS role_name,
 a.privilege_type,a.is_grantable FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a
 WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','v','m') ORDER BY 1,2,4;
SELECT c.relname,col.attname,a.grantee,a.privilege_type,a.is_grantable FROM pg_attribute col
 JOIN pg_class c ON c.oid=col.attrelid CROSS JOIN LATERAL aclexplode(col.attacl) a
 WHERE c.relnamespace='public'::regnamespace ORDER BY 1,2,3;

-- 5. Effective role privileges include PUBLIC and inherited grants.
SELECT r.role,c.relname,has_table_privilege(r.role,c.oid,'SELECT') AS can_select,
 has_table_privilege(r.role,c.oid,'INSERT') AS can_insert,has_table_privilege(r.role,c.oid,'UPDATE') AS can_update,
 has_table_privilege(r.role,c.oid,'DELETE') AS can_delete,
 has_table_privilege(r.role,c.oid,'TRUNCATE') AS can_truncate,
 has_table_privilege(r.role,c.oid,'TRIGGER') AS can_trigger,
 has_table_privilege(r.role,c.oid,'REFERENCES') AS can_references,
 CASE WHEN current_setting('server_version_num')::int>=170000 THEN has_table_privilege(r.role,c.oid,'MAINTAIN') ELSE false END AS can_maintain,
 has_any_column_privilege(r.role,c.oid,'SELECT,INSERT,UPDATE,REFERENCES') AS any_column_privilege
 FROM (VALUES('anon'),('authenticated'),('service_role')) r(role)
 CROSS JOIN pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','v','m') ORDER BY 1,2;
SELECT pg_get_userbyid(roleid) AS granted_role,pg_get_userbyid(member) AS member_role,admin_option
 FROM pg_auth_members ORDER BY 1,2;
SELECT r.role,has_schema_privilege(r.role,'public','USAGE') AS usage,has_schema_privilege(r.role,'public','CREATE') AS create_privilege
 FROM (VALUES('anon'),('authenticated'),('service_role')) r(role);

-- 6. ALL overloads, owner, search_path, return/argument contract, body digest, effective EXECUTE.
-- 5B. Legacy browser desired access. NEEDS_REVOKE includes inherited/PUBLIC effective grants;
-- the migration corrects only explicit PUBLIC/anon/authenticated ACLs and rejects remaining inheritance.
WITH targets(t) AS (VALUES ('companies'),('profiles'),('customers'),('messages'),('profit_events'),('timeline'),
 ('reply_logs'),('ai_judgements'),('learning_logs'),('calendar_events'),('gmail_connections')),
desired AS (SELECT t,r,p,(r='authenticated' AND t IN ('companies','profiles') AND p='SELECT') allowed
 FROM targets CROSS JOIN (VALUES('anon'),('authenticated')) roles(r)
 CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('TRIGGER'),('REFERENCES')) privileges(p))
SELECT *,has_table_privilege(r,to_regclass('public.'||t),p) effective,
 CASE WHEN to_regclass('public.'||t) IS NULL THEN 'STOP_MISSING_TABLE'
 WHEN has_table_privilege(r,to_regclass('public.'||t),p)=allowed THEN 'MATCH'
 WHEN allowed THEN 'REQUIRED_SELECT_MISSING_REVIEW_RLS' ELSE 'NEEDS_REVOKE' END AS decision FROM desired ORDER BY t,r,p;
-- Namespace ACL shows PUBLIC (grantee=0) rather than pretending PUBLIC is a pg_role.
SELECT n.nspname,x.grantee,CASE WHEN x.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(x.grantee) END AS grantee_name,
 x.privilege_type,x.is_grantable FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) x WHERE n.nspname='public';
-- Required service path; false/null is STOP. No service ACL is silently broadened.
SELECT c.relname,p.privilege,has_table_privilege('service_role',c.oid,p.privilege) required_service_access
 FROM pg_class c CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) p(privilege)
 WHERE c.relnamespace='public'::regnamespace AND c.relname IN ('companies','profiles','customers','messages','profit_events',
 'timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections') ORDER BY 1,2;

WITH expected(name) AS (VALUES ('commit_gmail_inbound_page'),('recover_company_work'),('save_financial_record'),('reserve_ai_budget'),('company_is_active'),('request_account_deletion'),('purge_account_data'),('complete_account_deletion'),('purge_expired_deletion_audit'),('prevent_deleted_user_onboarding'),('record_financial_payment'),('void_financial_payment'),('resolve_provider_uncertainty'),('promote_billing_live'),('acquire_gmail_sync_lock'),('apply_billing_snapshot'),('claim_gmail_work'),('create_company_and_profile'),('ensure_company_billing'),('finalize_gmail_send'),('onboard_user'),('release_gmail_sync_lock'),('release_gmail_work'),('reserve_ai_run'),('rls_auto_enable'))
SELECT e.name,p.oid IS NOT NULL AS present,pg_get_function_identity_arguments(p.oid) AS arguments,
 pg_get_function_result(p.oid) AS result,pg_get_userbyid(p.proowner) AS owner,p.prosecdef,p.proconfig,
 p.proargnames,md5(p.prosrc) AS body_md5,p.proacl,
 has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM expected e LEFT JOIN pg_proc p ON p.pronamespace='public'::regnamespace AND p.proname=e.name ORDER BY 1,3;

-- 7. Views, triggers and SECURITY DEFINER inventory. No function body or stored row values.
SELECT n.nspname,c.relname,c.relkind,c.reloptions,pg_get_userbyid(c.relowner) AS owner
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('v','m') ORDER BY 1,2;
SELECT c.relname,t.tgname,t.tgenabled,t.tgfoid::regprocedure AS function,pg_get_triggerdef(t.oid) AS definition
 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal ORDER BY 1,2;
SELECT p.oid::regprocedure AS function,pg_get_userbyid(p.proowner) AS owner,p.proconfig,p.proacl,md5(p.prosrc) AS body_md5
 FROM pg_proc p WHERE p.pronamespace='public'::regnamespace AND p.prosecdef ORDER BY 1;

-- 8. Only aggregate identity counts (no IDs/emails). Assumes preflight 1/2 found profiles.user_id.
-- Approved global aggregate contract, exact columns/defaults/nullability; company_id forbidden.
-- Zero rows is a release prerequisite; migration rechecks under transaction lock.
-- First result: actual metadata (no customer rows). Second: any returned row means STOP.
SELECT a.attname AS column_name,format_type(a.atttypid,a.atttypmod) AS data_type,
 a.attnotnull AS not_null,pg_get_expr(d.adbin,d.adrelid) AS column_default
 FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid='public.gmail_sync_runs'::regclass AND a.attnum>0 AND NOT a.attisdropped
 ORDER BY a.attnum;
WITH expected(name,typ,nn,def) AS (VALUES ('id','uuid',true,'gen_random_uuid()'),
 ('status','text',true,NULL),
 ('started_at','timestamptz',true,'now()'),
 ('finished_at','timestamptz',false,NULL),
 ('company_count','int4',true,'0'),
 ('success_count','int4',true,'0'),
 ('failure_count','int4',true,'0'),
 ('detected_reply_count','int4',true,'0'),
 ('error_summary','jsonb',true,'''[]''::jsonb')),
 actual AS (
 SELECT a.attname::text AS name,t.typname::text AS typ,a.attnotnull AS nn,
 pg_get_expr(d.adbin,d.adrelid) AS def,a.atttypmod,a.attidentity,a.attgenerated
 FROM pg_attribute a JOIN pg_type t ON t.oid=a.atttypid
 LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid='public.gmail_sync_runs'::regclass AND a.attnum>0 AND NOT a.attisdropped)
 SELECT 1 FROM expected e FULL JOIN actual a USING(name)
 WHERE e.name IS NULL OR a.name IS NULL OR e.typ IS DISTINCT FROM a.typ
 OR e.nn IS DISTINCT FROM a.nn OR e.def IS DISTINCT FROM a.def
 OR a.atttypmod<>-1 OR a.attidentity<>'' OR a.attgenerated<>''
;
SELECT count(*) AS legacy_sync_row_count,
 CASE WHEN count(*)=0 THEN 'EMPTY_AT_CAPTURE' ELSE 'STOP_GLOBAL_SYNC_ROWS_REVIEW' END AS legacy_review
 FROM public.gmail_sync_runs;
SELECT count(*) FILTER (WHERE user_id IS NULL) AS null_user_ids,
 (SELECT count(*) FROM (SELECT user_id FROM public.profiles GROUP BY user_id HAVING count(*)>1) d) AS duplicate_groups
 FROM public.profiles;
-- Billing mode itself is operational metadata; do not SELECT credentials or subscription references.
-- Run only when section 1 shows billing_runtime_config exists:
-- SELECT singleton,mode,approval_ref IS NOT NULL AS approval_present,approved_at IS NOT NULL AS approved
-- FROM public.billing_runtime_config;
