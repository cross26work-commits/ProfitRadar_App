-- Profit Radar remote forward v2 (standalone supplement, do not run v1 first). Remote connection/application NOT authorized.
-- Derived from 202609100002..008 and 202609110001 at checkpoint 27d6ec0.
-- Existing objects are reused only after compatibility checks; never replaced.
-- No historical migration/history repair, row backfill, cleanup, or live activation.
-- All helper/template objects are session temporary. Re-run is a validated no-op.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';
SET LOCAL search_path = pg_catalog, public, pg_temp;
SELECT pg_advisory_xact_lock(20260914, 1);
CREATE TEMP TABLE forward_created(name text primary key) ON COMMIT DROP;

-- Exact source bodies from docs/remote_onboarding_functiondefs_20260915_exact.txt.
-- Only prosrc line endings are normalized; whitespace/content/argument contracts remain exact.
DO $v2_identity_gate$
DECLARE f pg_proc%rowtype; expected_body text; expected_args text[]; n text; acl_ok boolean;
BEGIN
 IF has_schema_privilege('anon','public','CREATE') OR has_schema_privilege('authenticated','public','CREATE')
 OR has_schema_privilege('service_role','public','CREATE') THEN
  RAISE EXCEPTION 'FORWARD_V2: untrusted schema CREATE';
 END IF;
 FOREACH n IN ARRAY ARRAY['onboard_user','create_company_and_profile'] LOOP
  IF (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=n)<>1 THEN
   RAISE EXCEPTION 'FORWARD_V2: onboarding overload conflict';
  END IF;
  SELECT * INTO f FROM pg_proc WHERE oid=CASE WHEN n='onboard_user'
   THEN to_regprocedure('public.onboard_user(uuid,text,text,text)')
   ELSE to_regprocedure('public.create_company_and_profile(text,text)') END;
  IF f.oid IS NULL OR f.proowner<>'postgres'::regrole OR NOT f.prosecdef OR f.prolang<>(SELECT oid FROM pg_language WHERE lanname='plpgsql')
   OR f.prokind<>'f' OR f.proretset OR f.provolatile<>'v' OR f.proisstrict OR f.proleakproof
   OR f.proparallel<>'u' OR f.pronargdefaults<>0 OR f.proargmodes IS NOT NULL OR f.proallargtypes IS NOT NULL THEN
   RAISE EXCEPTION 'FORWARD_V2: onboarding owner/security/contract mismatch';
  END IF;
  IF n='onboard_user' THEN
   expected_body := $legacy_body$
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
$legacy_body$;
   expected_args := ARRAY['p_user_id','p_company_name','p_name','p_email'];
   IF f.prorettype<>'jsonb'::regtype OR f.proconfig NOT IN (ARRAY['search_path=public'],ARRAY['search_path=pg_catalog, pg_temp']) OR f.proconfig IS NULL THEN
    RAISE EXCEPTION 'FORWARD_V2: legacy config/return mismatch';
   END IF;
   IF f.proconfig=ARRAY['search_path=public'] THEN
    acl_ok := f.proacl IS NULL;
   ELSE
    acl_ok := (SELECT count(*)=2 AND bool_and(privilege_type='EXECUTE' AND NOT is_grantable
      AND grantor='postgres'::regrole AND grantee IN ('postgres'::regrole,'service_role'::regrole))
      FROM aclexplode(f.proacl));
   END IF;
  ELSE
   expected_body := $canonical_body$
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
$canonical_body$;
   expected_args := ARRAY['company_name','owner_name'];
   IF f.prorettype<>'uuid'::regtype OR f.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, public'] THEN
    RAISE EXCEPTION 'FORWARD_V2: canonical config/return mismatch';
   END IF;
   acl_ok := (SELECT count(*)=2 AND bool_and(privilege_type='EXECUTE' AND NOT is_grantable
     AND grantor='postgres'::regrole AND grantee IN ('postgres'::regrole,'authenticated'::regrole)) FROM aclexplode(f.proacl));
  END IF;
  IF replace(f.prosrc,E'\r\n',E'\n')<>replace(expected_body,E'\r\n',E'\n') OR f.proargnames IS DISTINCT FROM expected_args THEN
   RAISE EXCEPTION 'FORWARD_V2: onboarding exact body/arguments mismatch';
  END IF;
  IF acl_ok IS DISTINCT FROM true THEN RAISE EXCEPTION 'FORWARD_V2: onboarding ACL mismatch'; END IF;
 END LOOP;
END $v2_identity_gate$;
-- No body replacement: revoke public RPC authority, retain verified Backend service path.
ALTER FUNCTION public.onboard_user(uuid,text,text,text) SET search_path TO pg_catalog, pg_temp;
REVOKE ALL ON FUNCTION public.onboard_user(uuid,text,text,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.onboard_user(uuid,text,text,text) TO service_role;
DO $v2_effective_acl$
BEGIN
 IF has_function_privilege('anon','public.onboard_user(uuid,text,text,text)','EXECUTE')
 OR has_function_privilege('authenticated','public.onboard_user(uuid,text,text,text)','EXECUTE')
 OR NOT has_function_privilege('service_role','public.onboard_user(uuid,text,text,text)','EXECUTE')
 OR has_function_privilege('anon','public.create_company_and_profile(text,text)','EXECUTE')
 OR has_function_privilege('service_role','public.create_company_and_profile(text,text)','EXECUTE')
 OR NOT has_function_privilege('authenticated','public.create_company_and_profile(text,text)','EXECUTE') THEN
  RAISE EXCEPTION 'FORWARD_V2: inherited/effective function privilege mismatch';
 END IF;
END $v2_effective_acl$;

-- Required existing columns: actual app/RPC dependencies, not guessed remote state.
-- Forward-safe nullable compatibility columns. No defaults, backfills or guessed tenant IDs.
-- User-provided SELECT-only evidence: empty legacy/global aggregate, NOT tenant data.
-- SHARE lock prevents concurrent inserts and schema changes until COMMIT. No ACL changes.
DO $global_sync_evidence$
BEGIN
 LOCK TABLE public.gmail_sync_runs IN SHARE MODE;
 IF NOT EXISTS(SELECT 1 FROM pg_class WHERE oid='public.gmail_sync_runs'::regclass AND relkind='r') THEN
  RAISE EXCEPTION 'FORWARD: global sync schema mismatch';
 END IF;
 IF EXISTS(
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
 ) THEN RAISE EXCEPTION 'FORWARD: global sync schema mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM public.gmail_sync_runs) THEN
  RAISE EXCEPTION 'FORWARD: global sync rows require review';
 END IF;
END $global_sync_evidence$;
DO $legacy_columns$
DECLARE r record; a pg_attribute%rowtype; d text;
BEGIN
 FOR r IN SELECT * FROM (VALUES
 ('profit_events','description','text'),
 ('profit_events','neglected_days','int4'),
 ('profit_events','recoverable_profit','int8')) v(t,c,typ) LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_class WHERE oid=to_regclass('public.'||r.t) AND relkind='r'
    AND relowner IN ('postgres'::regrole,'supabase_admin'::regrole)) THEN
   RAISE EXCEPTION 'FORWARD: legacy column table owner/kind mismatch';
  END IF;
  SELECT * INTO a FROM pg_attribute WHERE attrelid=to_regclass('public.'||r.t) AND attname=r.c AND attnum>0 AND NOT attisdropped;
  IF NOT FOUND THEN
   EXECUTE format('ALTER TABLE public.%I ADD COLUMN %I %s',r.t,r.c,r.typ);
  ELSE
   SELECT pg_get_expr(adbin,adrelid) INTO d FROM pg_attrdef WHERE adrelid=a.attrelid AND adnum=a.attnum;
   IF a.atttypid<>to_regtype(r.typ) OR a.atttypmod<>-1 OR a.attnotnull OR d IS NOT NULL OR a.attidentity<>'' OR a.attgenerated<>'' THEN
    RAISE EXCEPTION 'FORWARD: legacy column contract mismatch %.%',r.t,r.c;
   END IF;
  END IF;
 END LOOP;
END $legacy_columns$;
-- Exact ownership contract; never repair unknown drift. Lock survives to COMMIT.
DO $owner_contract$
BEGIN
 LOCK TABLE public.companies IN SHARE MODE;
 IF NOT EXISTS(
  SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
  WHERE c.oid='public.companies'::regclass AND c.relkind='r'
   AND a.attname='owner_user_id' AND a.attnum>0 AND NOT a.attisdropped
   AND a.atttypid='pg_catalog.uuid'::regtype AND a.atttypmod=-1
   AND NOT a.attnotnull AND a.attidentity='' AND a.attgenerated=''
   AND pg_get_expr(d.adbin,d.adrelid)='auth.uid()'
 ) THEN
  RAISE EXCEPTION 'FORWARD: prerequisite column/type mismatch';
 END IF;
END $owner_contract$;
DO $preflight$
DECLARE r record; actual oid;
BEGIN
 IF current_user NOT IN ('postgres','supabase_admin') THEN RAISE EXCEPTION 'FORWARD: trusted migration owner required'; END IF;
 IF NOT has_schema_privilege('service_role','public','USAGE') THEN RAISE EXCEPTION 'FORWARD: service_role schema USAGE missing'; END IF;
 IF has_schema_privilege('anon','public','CREATE') OR has_schema_privilege('authenticated','public','CREATE') THEN
  RAISE EXCEPTION 'FORWARD: untrusted public schema CREATE; review before applying';
 END IF;
 FOR r IN SELECT * FROM (VALUES
 ('companies','owner_user_id','uuid'),
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
 ('timeline','created_at','timestamptz')
 ) AS required(table_name,column_name,type_name) LOOP
  SELECT a.atttypid INTO actual FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
   JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname=r.table_name AND c.relkind='r'
    AND a.attname=r.column_name AND a.attnum>0 AND NOT a.attisdropped;
  IF actual IS DISTINCT FROM to_regtype('pg_catalog.'||r.type_name)::oid THEN
   RAISE EXCEPTION 'FORWARD: prerequisite column/type mismatch %.%',r.table_name,r.column_name;
  END IF;
 END LOOP;
 IF NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid='public.profiles'::regclass
   AND i.indisunique AND i.indisvalid AND i.indisready AND i.indpred IS NULL AND i.indexprs IS NULL
   AND i.indnkeyatts=1 AND i.indnatts=1
   AND i.indkey[0]=(SELECT attnum FROM pg_attribute WHERE attrelid=i.indrelid AND attname='user_id')) THEN
  RAISE EXCEPTION 'FORWARD: profiles.user_id valid unique index required';
 END IF;
 IF EXISTS(SELECT 1 FROM public.profiles WHERE user_id IS NULL)
 OR EXISTS(SELECT 1 FROM public.profiles GROUP BY user_id HAVING count(*)>1) THEN
  RAISE EXCEPTION 'FORWARD: profiles identity preflight failed';
 END IF;
END $preflight$;

-- These existing RPCs are prerequisites, NOT replaced by this migration.
-- Authoritative remote snapshot: 1016 bytes, SHA256 DF734F55B6379D0C2983D658AA15E6D93A667EFE5200A13B6B4199CB9905DCC2.
-- Policies are compared, never modified. Exact fields/roles/expressions required.
DO $remote_policy_oracle$
DECLARE actual jsonb;
BEGIN
 SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY p.tablename,p.policyname),'[]'::jsonb) INTO actual
 FROM pg_policies p WHERE schemaname='public' AND tablename IN
 ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections');
 IF actual IS DISTINCT FROM $policy_oracle$[{"cmd":"INSERT","qual":null,"roles":["authenticated"],"tablename":"companies","permissive":"PERMISSIVE","policyname":"companies_insert_own","schemaname":"public","with_check":"(owner_user_id = auth.uid())"},{"cmd":"SELECT","qual":"((owner_user_id = auth.uid()) OR (EXISTS ( SELECT 1\n   FROM profiles\n  WHERE ((profiles.company_id = companies.id) AND (profiles.user_id = auth.uid())))))","roles":["authenticated"],"tablename":"companies","permissive":"PERMISSIVE","policyname":"companies_select_member_or_owner","schemaname":"public","with_check":null},{"cmd":"SELECT","qual":"(user_id = auth.uid())","roles":["authenticated"],"tablename":"profiles","permissive":"PERMISSIVE","policyname":"profiles_select_own","schemaname":"public","with_check":null},{"cmd":"UPDATE","qual":"(user_id = auth.uid())","roles":["authenticated"],"tablename":"profiles","permissive":"PERMISSIVE","policyname":"profiles_update_own","schemaname":"public","with_check":null}]$policy_oracle$::jsonb THEN
  RAISE EXCEPTION 'FORWARD: unknown legacy policy snapshot';
 END IF;
END $remote_policy_oracle$;
DO $legacy_acl$
DECLARE t text; obj oid; own oid; cols text; p record; expected text; priv text; role_name text;
BEGIN
 FOREACH t IN ARRAY ARRAY['companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections'] LOOP
  SELECT oid,relowner INTO obj,own FROM pg_class WHERE oid=to_regclass('public.'||t) AND relkind='r' AND relrowsecurity;
  IF obj IS NULL OR own NOT IN ('postgres'::regrole,'supabase_admin'::regrole) THEN
   RAISE EXCEPTION 'FORWARD: legacy RLS/owner mismatch %',t;
  END IF;
  IF EXISTS(SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) x WHERE c.oid=obj
     AND x.grantee NOT IN (0,own,'postgres'::regrole,'supabase_admin'::regrole,'anon'::regrole,'authenticated'::regrole,'service_role'::regrole))
  OR EXISTS(SELECT 1 FROM pg_attribute a CROSS JOIN LATERAL aclexplode(a.attacl) x WHERE a.attrelid=obj
     AND x.grantee NOT IN (0,own,'postgres'::regrole,'supabase_admin'::regrole,'anon'::regrole,'authenticated'::regrole,'service_role'::regrole)) THEN
   RAISE EXCEPTION 'FORWARD: unexpected legacy grantee %',t;
  END IF;
  IF EXISTS(SELECT 1 FROM pg_depend d JOIN pg_rewrite w ON w.oid=d.objid JOIN pg_class v ON v.oid=w.ev_class
    WHERE d.refobjid=obj AND v.relkind IN ('v','m')) THEN RAISE EXCEPTION 'FORWARD: legacy dependent view requires review'; END IF;
  EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC,anon,authenticated',t);
  SELECT string_agg(quote_ident(attname),',') INTO cols FROM pg_attribute WHERE attrelid=obj AND attnum>0 AND NOT attisdropped;
  EXECUTE format('REVOKE SELECT(%s),INSERT(%s),UPDATE(%s),REFERENCES(%s) ON TABLE public.%I FROM PUBLIC,anon,authenticated',cols,cols,cols,cols,t);
  IF t IN ('companies','profiles') THEN EXECUTE format('GRANT SELECT ON TABLE public.%I TO authenticated',t); END IF;
  FOREACH role_name IN ARRAY ARRAY['anon','authenticated'] LOOP
   FOREACH priv IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','TRIGGER','REFERENCES'] LOOP
    IF has_table_privilege(role_name,obj,priv) IS DISTINCT FROM (role_name='authenticated' AND t IN ('companies','profiles') AND priv='SELECT') THEN
     RAISE EXCEPTION 'FORWARD: inherited legacy privilege remains %',t;
    END IF;
   END LOOP;
   IF current_setting('server_version_num')::int>=170000 AND has_table_privilege(role_name,obj,'MAINTAIN') THEN
    RAISE EXCEPTION 'FORWARD: inherited legacy MAINTAIN remains %',t;
   END IF;
   IF has_any_column_privilege(role_name,obj,'INSERT,UPDATE,REFERENCES')
    OR (NOT(role_name='authenticated' AND t IN ('companies','profiles')) AND has_any_column_privilege(role_name,obj,'SELECT')) THEN
    RAISE EXCEPTION 'FORWARD: inherited legacy column privilege remains %',t;
   END IF;
  END LOOP;
  FOREACH priv IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE'] LOOP
   IF NOT has_table_privilege('service_role',obj,priv) THEN RAISE EXCEPTION 'FORWARD: required legacy service privilege missing %',t; END IF;
  END LOOP;
 END LOOP;
END $legacy_acl$;
DO $rpc_preflight$
DECLARE sig text; f pg_proc%rowtype;
BEGIN
 FOREACH sig IN ARRAY ARRAY['onboard_user(uuid,text,text,text)','claim_gmail_work(uuid,uuid,text)',
 'release_gmail_work(uuid,uuid)','finalize_gmail_send(uuid,text,text,text)',
 'ensure_company_billing(uuid)','apply_billing_snapshot(uuid,text,text,text,timestamp with time zone)',
 'reserve_ai_run(uuid,integer)'] LOOP
  SELECT * INTO f FROM pg_proc WHERE oid=to_regprocedure('public.'||sig);
  IF NOT FOUND OR NOT f.prosecdef OR f.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, pg_temp']::text[]
   OR pg_get_userbyid(f.proowner) NOT IN ('postgres','supabase_admin')
   OR has_function_privilege('anon',f.oid,'EXECUTE') OR has_function_privilege('authenticated',f.oid,'EXECUTE')
   OR NOT has_function_privilege('service_role',f.oid,'EXECUTE') THEN
   RAISE EXCEPTION 'FORWARD: prerequisite RPC signature/security mismatch %',sig;
  END IF;
  IF (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=f.proname)<>1 THEN
   RAISE EXCEPTION 'FORWARD: prerequisite RPC overload conflict %',sig;
  END IF;
 END LOOP;
END $rpc_preflight$;

-- Temporary FK targets mirror only prerequisite structure, never customer rows.
DO $templates$
DECLARE t text;
BEGIN
 FOR t IN SELECT DISTINCT table_name FROM information_schema.columns
 WHERE table_schema='public' AND table_name IN (
 'companies','profiles','customers','messages','profit_events','reply_logs','timeline',
 'gmail_connections','gmail_work_locks','gmail_send_operations','gmail_company_sync_runs',
 'gmail_sync_runs','company_billing','billing_webhook_events',
 'ai_usage_runs','reply_drafts','conversation_analysis_snapshots','learning_logs','ai_judgements','calendar_events') LOOP
  EXECUTE format('CREATE TEMP TABLE pg_temp.%I (LIKE public.%I INCLUDING ALL) ON COMMIT DROP',t,t);
 END LOOP;
END $templates$;

-- Templates are independent DDL specifications. IF NOT EXISTS alone is not a compatibility test.
CREATE FUNCTION pg_temp.forward_table_signature(p_table regclass) RETURNS jsonb
LANGUAGE sql SET search_path=pg_catalog,pg_temp AS $helper$
 SELECT jsonb_build_object(
 'columns',(SELECT jsonb_agg(jsonb_build_array(a.attname,a.atttypid,a.atttypmod,a.attnotnull,
 a.attidentity,a.attgenerated,pg_get_expr(d.adbin,d.adrelid)) ORDER BY a.attnum)
 FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid=p_table AND a.attnum>0 AND NOT a.attisdropped),
 'constraints',(SELECT jsonb_agg(definition ORDER BY definition::text) FROM (
 SELECT CASE WHEN contype='f' THEN jsonb_build_array(contype,conkey,confkey,
 (SELECT CASE WHEN relnamespace=pg_my_temp_schema() THEN 'public' ELSE n.nspname END||'.'||c.relname
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.oid=confrelid),confupdtype,confdeltype,confmatchtype,
 condeferrable,condeferred,convalidated)
 ELSE jsonb_build_array(contype,pg_get_constraintdef(oid),convalidated) END AS definition
 FROM pg_constraint WHERE conrelid=p_table) definitions))
$helper$;
CREATE FUNCTION pg_temp.forward_table(p_name text,p_ddl text) RETURNS void
LANGUAGE plpgsql SET search_path=pg_catalog,pg_temp AS $helper$
DECLARE actual regclass;
BEGIN
 EXECUTE replace(replace(p_ddl,'CREATE TABLE public.'||p_name,'CREATE TEMP TABLE pg_temp.'||p_name),
 'references public.','references pg_temp.')||' ON COMMIT DROP';
 actual:=to_regclass('public.'||p_name);
 IF actual IS NULL THEN
  EXECUTE p_ddl;
  INSERT INTO pg_temp.forward_created VALUES(p_name);
 ELSE
  IF NOT EXISTS(SELECT 1 FROM pg_class WHERE oid=actual AND relkind='r' AND relrowsecurity
      AND pg_get_userbyid(relowner) IN ('postgres','supabase_admin')) THEN
   RAISE EXCEPTION 'FORWARD: table kind/owner/RLS mismatch %',p_name;
  END IF;
  IF pg_temp.forward_table_signature(actual) IS DISTINCT FROM pg_temp.forward_table_signature(to_regclass('pg_temp.'||p_name)) THEN
   RAISE EXCEPTION 'FORWARD: incompatible existing table %',p_name;
  END IF;
 END IF;
 IF EXISTS(SELECT 1 FROM pg_policy WHERE polrelid=to_regclass('public.'||p_name))
 OR EXISTS(SELECT 1 FROM pg_trigger WHERE tgrelid=to_regclass('public.'||p_name) AND NOT tgisinternal) THEN
  RAISE EXCEPTION 'FORWARD: unexpected policy/trigger on %',p_name;
 END IF;
 IF EXISTS(SELECT 1 FROM pg_index WHERE indrelid=to_regclass('public.'||p_name) AND (NOT indisvalid OR NOT indisready)) THEN
  RAISE EXCEPTION 'FORWARD: invalid/unready index on %',p_name;
 END IF;
END $helper$;

-- Source: 202609100002_atomic_gmail_sync.sql
-- Historical definition: 202609090007_checkout_attempts.sql.
SELECT pg_temp.forward_table('billing_checkout_attempts', $ddl$
CREATE TABLE public.billing_checkout_attempts (
 company_id uuid primary key references public.companies(id),attempt_id uuid not null,
 session_id text,created_at timestamptz not null default now()
)
$ddl$);
DO $checkout_indexes$
BEGIN
 IF (SELECT count(*) FROM pg_index WHERE indrelid='public.billing_checkout_attempts'::regclass)<>1 THEN
  RAISE EXCEPTION 'FORWARD_V2: unexpected checkout index';
 END IF;
END $checkout_indexes$;
SELECT pg_temp.forward_table('gmail_sync_cursors', $ddl$
CREATE TABLE public.gmail_sync_cursors (
 company_id uuid primary key references public.companies(id), mailbox text not null,
 version bigint not null, mode text not null check(mode in ('full','delta')),
 history_id text not null, page_token text, initial_since bigint not null,
 pending_ids jsonb, pending_page jsonb,
 last_page_at timestamptz not null default now(), last_successful_sync timestamptz
)
$ddl$);
-- Source: 202609100002_atomic_gmail_sync.sql
SELECT pg_temp.forward_table('gmail_inbound_receipts', $ddl$
CREATE TABLE public.gmail_inbound_receipts (
 company_id uuid not null references public.companies(id), mailbox text not null,
 gmail_message_id text not null, profit_event_id uuid references public.profit_events(id),
 outcome text not null, created_at timestamptz not null default now(),
 primary key(company_id,mailbox,gmail_message_id)
)
$ddl$);
-- Source: 202609100003_operator_recovery.sql
SELECT pg_temp.forward_table('operation_recovery_audit', $ddl$
CREATE TABLE public.operation_recovery_audit (
 id uuid primary key default gen_random_uuid(), company_id uuid not null references public.companies(id),
 owner_id uuid not null, purpose text not null, operator_ref text not null, ticket_ref text not null,
 stopped_workers_confirmed boolean not null check(stopped_workers_confirmed), recovered_at timestamptz not null default now()
)
$ddl$);
-- Source: 202609100004_financial_records.sql
SELECT pg_temp.forward_table('financial_records', $ddl$
CREATE TABLE public.financial_records (
 company_id uuid not null references public.companies(id), profit_event_id uuid primary key references public.profit_events(id),
 customer_id uuid not null references public.customers(id), expected_revenue bigint check(expected_revenue>=0),
 ordered_revenue bigint check(ordered_revenue>=0), paid_amount bigint check(paid_amount>=0), cost bigint check(cost>=0),
 occurred_at timestamptz not null, confirmed_at timestamptz, paid_at timestamptz,
 source text not null default 'manual' check(source='manual'), created_by uuid not null,
 version bigint not null, updated_at timestamptz not null default now(),
 check(ordered_revenue is null or confirmed_at is not null), check(paid_amount is null or paid_at is not null)
)
$ddl$);
-- Source: 202609100004_financial_records.sql
SELECT pg_temp.forward_table('financial_record_history', $ddl$
CREATE TABLE public.financial_record_history (
 id uuid primary key default gen_random_uuid(),company_id uuid not null references public.companies(id),
 profit_event_id uuid not null references public.profit_events(id), actor_id uuid not null,
 version bigint not null, previous_record jsonb, new_record jsonb not null,created_at timestamptz not null default now(),
 unique(profit_event_id,version)
)
$ddl$);
-- Source: 202609100005_ai_hard_budget.sql
SELECT pg_temp.forward_table('ai_budget_reservations', $ddl$
CREATE TABLE public.ai_budget_reservations (
 id uuid primary key default gen_random_uuid(), company_id uuid not null references public.companies(id),
 model text not null, reserved_tokens bigint not null check(reserved_tokens>0),
 reserved_cost_micro_usd bigint not null check(reserved_cost_micro_usd>0),
 token_limit bigint not null, cost_limit_micro_usd bigint not null,
 status text not null default 'reserved' check(status in ('reserved','succeeded','reviewed_unknown')),
 actual_input_tokens bigint, actual_output_tokens bigint, created_at timestamptz not null default now()
)
$ddl$);
-- Source: 202609100006_account_deletion.sql
SELECT pg_temp.forward_table('account_deletion_jobs', $ddl$
CREATE TABLE public.account_deletion_jobs (
 id uuid primary key default gen_random_uuid(), company_id uuid not null unique, user_id uuid not null unique,
 status text not null default 'providers' check(status in ('providers','data','auth','completed')),
 gmail_done boolean not null default false, billing_done boolean not null default false,
 billing_reference text, last_error_code text, requested_at timestamptz not null default now(),
 completed_at timestamptz, purge_after timestamptz not null
)
$ddl$);
-- Source: 202609100006_account_deletion.sql
SELECT pg_temp.forward_table('account_deletion_audit', $ddl$
CREATE TABLE public.account_deletion_audit (
 id uuid primary key default gen_random_uuid(), job_id uuid not null references public.account_deletion_jobs(id) on delete cascade,
 stage text not null, created_at timestamptz not null default now(), unique(job_id,stage)
)
$ddl$);
-- Source: 202609100007_payment_entries.sql
SELECT pg_temp.forward_table('financial_payments', $ddl$
CREATE TABLE public.financial_payments (
 id uuid primary key, company_id uuid not null references public.companies(id),
 profit_event_id uuid not null references public.profit_events(id), customer_id uuid not null references public.customers(id),
 amount bigint not null check(amount>0 and amount<=1000000000000), paid_at timestamptz not null,
 created_by uuid not null, created_at timestamptz not null default now(),
 voided_at timestamptz, voided_by uuid, void_reason text
)
$ddl$);
-- Source: 202609110001_billing_production_gate.sql
SELECT pg_temp.forward_table('billing_runtime_config', $ddl$
CREATE TABLE public.billing_runtime_config (
 singleton boolean primary key default true check(singleton),
 mode text not null default 'test' check(mode in ('test','live')),
 approval_ref text,
 approved_at timestamptz
)
$ddl$);

-- Exact least privileges on these ten reviewed internal tables only.
-- Legacy Supabase default grants can leave service_role ALL after GRANT SELECT.
-- Normalize its table/column ACL; preserve data and unknown policies (fail closed above).
DO $acl$
DECLARE t text; col text; role_name text; op text; allowed boolean; existing boolean;
BEGIN
 FOREACH t IN ARRAY ARRAY['billing_checkout_attempts','gmail_sync_cursors','gmail_inbound_receipts','operation_recovery_audit','financial_records','financial_record_history','ai_budget_reservations','account_deletion_jobs','account_deletion_audit','financial_payments','billing_runtime_config'] LOOP
  existing:=NOT EXISTS(SELECT 1 FROM pg_temp.forward_created WHERE name=t);
  IF NOT existing THEN
   EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
   EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC,anon,authenticated,service_role',t);
  END IF;
   EXECUTE format('REVOKE ALL ON public.%I FROM service_role',t);
   FOR col IN SELECT attname FROM pg_attribute WHERE attrelid=to_regclass('public.'||t) AND attnum>0 AND NOT attisdropped LOOP
    EXECUTE format('REVOKE ALL (%I) ON public.%I FROM service_role',col,t);
   END LOOP;
   EXECUTE format('GRANT SELECT ON public.%I TO service_role',t);
   IF t='billing_checkout_attempts' THEN GRANT INSERT,UPDATE ON public.billing_checkout_attempts TO service_role; END IF;
   IF t='ai_budget_reservations' THEN
    GRANT UPDATE(status,actual_input_tokens,actual_output_tokens) ON public.ai_budget_reservations TO service_role;
   ELSIF t='account_deletion_jobs' THEN
    GRANT UPDATE(gmail_done,billing_done,billing_reference,last_error_code) ON public.account_deletion_jobs TO service_role;
   END IF;
  FOREACH role_name IN ARRAY ARRAY['anon','authenticated'] LOOP
   FOREACH op IN ARRAY ARRAY['SELECT','INSERT','UPDATE','REFERENCES'] LOOP
    IF has_any_column_privilege(role_name,'public.'||t,op) THEN
     RAISE EXCEPTION 'FORWARD: browser effective column/table privilege on %',t;
    END IF;
   END LOOP;
   IF has_table_privilege(role_name,'public.'||t,'DELETE,TRUNCATE,TRIGGER') THEN
    RAISE EXCEPTION 'FORWARD: browser effective write privilege on %',t;
   END IF;
  END LOOP;
  IF EXISTS(SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) acl
    WHERE c.oid=to_regclass('public.'||t) AND acl.grantee NOT IN (c.relowner,'service_role'::regrole))
  OR EXISTS(SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid CROSS JOIN LATERAL aclexplode(a.attacl) acl
    WHERE c.oid=to_regclass('public.'||t) AND acl.grantee NOT IN (c.relowner,'service_role'::regrole)) THEN
   RAISE EXCEPTION 'FORWARD: unreviewed grantee on %',t;
  END IF;
  IF (t<>'billing_checkout_attempts' AND has_table_privilege('service_role','public.'||t,'INSERT,UPDATE'))
    OR has_table_privilege('service_role','public.'||t,'DELETE,TRUNCATE,REFERENCES,TRIGGER')
    OR (t='billing_checkout_attempts' AND (NOT has_table_privilege('service_role','public.'||t,'INSERT') OR NOT has_table_privilege('service_role','public.'||t,'UPDATE')))
    OR NOT has_table_privilege('service_role','public.'||t,'SELECT') THEN
   RAISE EXCEPTION 'FORWARD: service_role table privilege mismatch %',t;
  END IF;
  FOR col IN SELECT attname FROM pg_attribute WHERE attrelid=to_regclass('public.'||t) AND attnum>0 AND NOT attisdropped LOOP
   allowed:=(t='billing_checkout_attempts') OR (t='ai_budget_reservations' AND col IN ('status','actual_input_tokens','actual_output_tokens'))
     OR (t='account_deletion_jobs' AND col IN ('gmail_done','billing_done','billing_reference','last_error_code'));
   IF has_column_privilege('service_role','public.'||t,col,'UPDATE') IS DISTINCT FROM allowed
     OR has_column_privilege('service_role','public.'||t,col,'REFERENCES')
     OR (has_column_privilege('service_role','public.'||t,col,'INSERT') IS DISTINCT FROM (t='billing_checkout_attempts')) THEN
    RAISE EXCEPTION 'FORWARD: service_role column privilege mismatch %.%',t,col;
   END IF;
  END LOOP;
 END LOOP;
END $acl$;

-- A view can bypass table ACL through its owner. Refuse unreviewed dependants,
-- including chained views, instead of changing or dropping somebody else's view.
DO $views$
BEGIN
 IF EXISTS(WITH RECURSIVE dependent(oid) AS (
  SELECT to_regclass('public.'||name)::oid FROM (VALUES
   ('billing_checkout_attempts'),('gmail_sync_cursors'),('gmail_inbound_receipts'),('operation_recovery_audit'),
   ('financial_records'),('financial_record_history'),('ai_budget_reservations'),
   ('account_deletion_jobs'),('account_deletion_audit'),('financial_payments'),('billing_runtime_config')) t(name)
  UNION
  SELECT rw.ev_class FROM dependent p JOIN pg_depend d ON d.refobjid=p.oid AND d.refclassid='pg_class'::regclass
    JOIN pg_rewrite rw ON rw.oid=d.objid AND d.classid='pg_rewrite'::regclass
 ) SELECT 1 FROM dependent p JOIN pg_class c ON c.oid=p.oid WHERE c.relkind IN ('v','m')) THEN
  RAISE EXCEPTION 'FORWARD: dependent view requires explicit review';
 END IF;
END $views$;

CREATE FUNCTION pg_temp.forward_index(p_name text,p_table text,p_ddl text) RETURNS void
LANGUAGE plpgsql SET search_path=pg_catalog,pg_temp AS $helper$
DECLARE existing regclass; expected regclass; a jsonb; b jsonb;
BEGIN
 EXECUTE replace(p_ddl,'public.'||p_table,'pg_temp.'||p_table);
 expected:=to_regclass('pg_temp.'||p_name);
 existing:=to_regclass('public.'||p_name);
 IF existing IS NULL THEN EXECUTE p_ddl; existing:=to_regclass('public.'||p_name); END IF;
 SELECT jsonb_build_array(i.indisunique,i.indisvalid,i.indisready,i.indnkeyatts,i.indnatts,i.indkey::text,
 i.indclass::text,i.indcollation::text,i.indoption::text,pg_get_expr(i.indexprs,i.indrelid),pg_get_expr(i.indpred,i.indrelid),c.relam)
 INTO a FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indexrelid=existing AND i.indrelid=to_regclass('public.'||p_table);
 SELECT jsonb_build_array(i.indisunique,i.indisvalid,i.indisready,i.indnkeyatts,i.indnatts,i.indkey::text,
 i.indclass::text,i.indcollation::text,i.indoption::text,pg_get_expr(i.indexprs,i.indrelid),pg_get_expr(i.indpred,i.indrelid),c.relam)
 INTO b FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indexrelid=expected;
 IF a IS DISTINCT FROM b THEN RAISE EXCEPTION 'FORWARD: index definition mismatch %',p_name; END IF;
END $helper$;
SELECT pg_temp.forward_index('ai_budget_company_month','ai_budget_reservations',$ddl$create index ai_budget_company_month on public.ai_budget_reservations(company_id,created_at)$ddl$);
SELECT pg_temp.forward_index('financial_payments_company_date','financial_payments',$ddl$create index financial_payments_company_date on public.financial_payments(company_id,paid_at)$ddl$);

-- A missing billing configuration starts in test mode. Existing values are never rewritten.
DO $billing$
BEGIN
 IF EXISTS(SELECT 1 FROM pg_temp.forward_created WHERE name='billing_runtime_config') THEN
  INSERT INTO public.billing_runtime_config(singleton) VALUES(true);
 END IF;
 IF (SELECT count(*) FROM public.billing_runtime_config)<>1 OR NOT EXISTS(
 SELECT 1 FROM public.billing_runtime_config WHERE singleton AND mode='test' AND approval_ref IS NULL AND approved_at IS NULL) THEN
  RAISE EXCEPTION 'FORWARD: test-only billing configuration required; no mode change performed';
 END IF;
END $billing$;

CREATE FUNCTION pg_temp.forward_function(p_name text,p_ddl text) RETURNS void
LANGUAGE plpgsql SET search_path=pg_catalog,pg_temp AS $helper$
DECLARE expected pg_proc%rowtype; actual pg_proc%rowtype; sig text;
BEGIN
 EXECUTE replace(p_ddl,'create function public.'||p_name,'create function pg_temp.'||p_name);
 SELECT * INTO STRICT expected FROM pg_proc WHERE pronamespace=pg_my_temp_schema() AND proname=p_name;
 sig:=p_name||'('||oidvectortypes(expected.proargtypes)||')';
 IF NOT EXISTS(SELECT 1 FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=p_name) THEN
  EXECUTE p_ddl;
  EXECUTE 'REVOKE ALL ON FUNCTION public.'||sig||' FROM PUBLIC,anon,authenticated,service_role';
  IF p_name<>'prevent_deleted_user_onboarding' THEN EXECUTE 'GRANT EXECUTE ON FUNCTION public.'||sig||' TO service_role'; END IF;
 END IF;
 IF (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=p_name)<>1 THEN
  RAISE EXCEPTION 'FORWARD: function overload conflict %',p_name;
 END IF;
 SELECT * INTO STRICT actual FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=p_name;
 IF actual.proargtypes<>expected.proargtypes OR actual.prorettype<>expected.prorettype
 OR actual.proargnames IS DISTINCT FROM expected.proargnames OR actual.proallargtypes IS DISTINCT FROM expected.proallargtypes
 OR actual.proargmodes IS DISTINCT FROM expected.proargmodes OR actual.proretset<>expected.proretset
 OR actual.prolang<>expected.prolang OR actual.prosrc<>expected.prosrc
 OR actual.prosecdef<>expected.prosecdef OR actual.proconfig IS DISTINCT FROM expected.proconfig
 OR actual.provolatile<>expected.provolatile OR actual.proisstrict<>expected.proisstrict
 OR actual.pronargdefaults<>expected.pronargdefaults OR actual.proleakproof<>expected.proleakproof
 OR pg_get_userbyid(actual.proowner) NOT IN ('postgres','supabase_admin') THEN
  RAISE EXCEPTION 'FORWARD: existing function differs; reviewed forward replacement required %',p_name;
 END IF;
 IF has_function_privilege('anon',actual.oid,'EXECUTE') OR has_function_privilege('authenticated',actual.oid,'EXECUTE')
 OR (p_name<>'prevent_deleted_user_onboarding' AND NOT has_function_privilege('service_role',actual.oid,'EXECUTE')) THEN
  RAISE EXCEPTION 'FORWARD: function privileges mismatch %',p_name;
 END IF;
 IF EXISTS(SELECT 1 FROM aclexplode(coalesce(actual.proacl,acldefault('f',actual.proowner))) acl
   WHERE acl.grantee NOT IN (actual.proowner,'service_role'::regrole)
    OR (acl.is_grantable AND acl.grantee<>actual.proowner)) THEN
  RAISE EXCEPTION 'FORWARD: unreviewed function grantee %',p_name;
 END IF;
END $helper$;
-- Source: 202609100002_atomic_gmail_sync.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('commit_gmail_inbound_page',$ddl$
create function public.commit_gmail_inbound_page(p_company_id uuid,p_owner_id uuid,p_connection_id uuid,p_mailbox text,p_expected_version bigint,p_state jsonb,p_records jsonb)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare r jsonb; cid uuid; eid uuid; mid uuid; n integer:=0; current_version bigint; outgoing boolean;
begin
 perform 1 from public.gmail_work_locks where company_id=p_company_id and owner_id=p_owner_id and purpose='sync' for update;
 if not found then raise exception 'sync owner mismatch'; end if;
 perform 1 from public.gmail_connections where id=p_connection_id and company_id=p_company_id and lower(email)=p_mailbox and status='connected' for update;
 if not found then raise exception 'connection changed'; end if;
 select version into current_version from public.gmail_sync_cursors where company_id=p_company_id for update;
 if coalesce(current_version,0)<>p_expected_version then raise exception 'cursor version conflict'; end if;
 if jsonb_typeof(p_records)<>'array' or jsonb_array_length(p_records)>1000 then raise exception 'invalid page'; end if;
 for r in select value from jsonb_array_elements(p_records) loop
  cid:=null; eid:=null; mid:=null;
  outgoing:=coalesce(r->>'direction','incoming')='outgoing';
  if coalesce(r->>'message_id','')='' or coalesce(r->>'thread_id','')='' or coalesce(r->>'sender','')='' then raise exception 'invalid message'; end if;
  if exists(select 1 from public.gmail_inbound_receipts where company_id=p_company_id and mailbox=p_mailbox and gmail_message_id=r->>'message_id' and outcome='imported') then continue; end if;
  -- Prefer an already imported legacy message relationship before thread lookup.
  select e.id,c.id into eid,cid from public.reply_logs l
   join public.profit_events e on e.id=l.profit_event_id and e.company_id=l.company_id
   join public.customers c on c.id=e.customer_id and c.company_id=e.company_id
   where l.company_id=p_company_id and (l.gmail_message_id=r->>'message_id' or l.external_id=r->>'message_id')
    and lower(c.email)=r->>'sender' order by l.reply_at,l.id limit 1;
  -- Same-company thread AND sender. Never reassign an existing event to an unrelated sender.
  if eid is null then
  select e.id,e.customer_id into eid,cid from public.profit_events e join public.customers c on c.id=e.customer_id and c.company_id=e.company_id
   where e.company_id=p_company_id and e.gmail_thread_id=r->>'thread_id' and lower(c.email)=r->>'sender' order by e.created_at,e.id limit 1;
  end if;
  if eid is null and not coalesce((r->>'candidate')::boolean,false) then
   insert into public.gmail_inbound_receipts values(p_company_id,p_mailbox,r->>'message_id',null,'not_target',now()) on conflict do nothing; continue;
  end if;
  -- Serialize address-based find/create with all pages for this company; retain existing duplicates for audit.
  perform pg_advisory_xact_lock(hashtextextended(p_company_id::text||':'||(r->>'sender'),73));
  if cid is null then
   select id into cid from public.customers where company_id=p_company_id and lower(email)=r->>'sender' order by created_at,id limit 1;
   if cid is null then insert into public.customers(company_id,name,email) values(p_company_id,left(r->>'sender_name',200),r->>'sender') returning id into cid; end if;
  end if;
  select id into mid from public.messages where company_id=p_company_id and customer_id=cid
   and channel='gmail' and direction=case when outgoing then 'outgoing' else 'incoming' end and external_id=r->>'message_id'
   and lower(sender)=case when outgoing then p_mailbox else r->>'sender' end order by received_at,id limit 1;
  if mid is null then
   insert into public.messages(company_id,customer_id,direction,channel,sender,recipient,subject,body,external_id,thread_id,received_at)
   values(p_company_id,cid,case when outgoing then 'outgoing' else 'incoming' end,'gmail',case when outgoing then p_mailbox else r->>'sender' end,case when outgoing then r->>'sender' else p_mailbox end,r->>'subject',left(r->>'body',30000),r->>'message_id',r->>'thread_id',(r->>'received_at')::timestamptz) returning id into mid;
  end if;
  if eid is null then
   insert into public.profit_events(company_id,customer_id,source_message_id,title,gmail_thread_id,next_action,category)
    values(p_company_id,cid,mid,coalesce(nullif(r->>'subject',''),'新規問い合わせ'),r->>'thread_id','元メールを確認して返信要否を判断','inquiry') returning id into eid;
  end if;
  -- Legacy receipt might already exist; repair its missing timeline rather than duplicating it.
  if not outgoing and not exists(select 1 from public.reply_logs where company_id=p_company_id and (gmail_message_id=r->>'message_id' or external_id=r->>'message_id')) then
   insert into public.reply_logs(company_id,customer_id,profit_event_id,message_id,channel,reply_body,reply_at,external_id,thread_id,gmail_message_id,gmail_thread_id)
    values(p_company_id,cid,eid,mid,'gmail',left(r->>'body',30000),(r->>'received_at')::timestamptz,r->>'message_id',r->>'thread_id',r->>'message_id',r->>'thread_id');
  end if;
  if not exists(select 1 from public.timeline where company_id=p_company_id and event_type=case when outgoing then 'gmail_sent_imported' else 'gmail_reply_detected' end and metadata->>'gmail_message_id'=r->>'message_id') then
   insert into public.timeline(company_id,customer_id,profit_event_id,event_type,channel,title,description,occurred_at,metadata)
    values(p_company_id,cid,eid,case when outgoing then 'gmail_sent_imported' else 'gmail_reply_detected' end,'gmail',case when outgoing then 'Gmail送信済み商談・要確認' else 'Gmail受信・要確認' end,left(r->>'body',500),(r->>'received_at')::timestamptz,jsonb_build_object('gmail_message_id',r->>'message_id','gmail_thread_id',r->>'thread_id','from_email',case when outgoing then p_mailbox else r->>'sender' end,'subject',r->>'subject','reason',r->>'reason','suppressed',r->'suppressed'));
  end if;
  update public.profit_events set last_gmail_message_id=case when outgoing then last_gmail_message_id else r->>'message_id' end,next_action=case when coalesce((r->>'suppressed')::boolean,false) then '連絡停止・受信内容を確認（自動追客禁止）' when outgoing then '送信済み・返信待ち。元メールと経過日数を確認' else '元メールを確認して返信要否を判断' end
   where id=eid and company_id=p_company_id and not exists(
    select 1 from public.messages m where m.company_id=p_company_id and m.customer_id=cid
     and m.thread_id=r->>'thread_id' and m.direction in ('incoming','outgoing') and m.received_at>(r->>'received_at')::timestamptz)
    and not (outgoing and next_action like '連絡停止%');
  insert into public.gmail_inbound_receipts values(p_company_id,p_mailbox,r->>'message_id',eid,'imported',now())
   on conflict(company_id,mailbox,gmail_message_id) do update set profit_event_id=excluded.profit_event_id,outcome='imported';
  n:=n+1;
 end loop;
 insert into public.gmail_sync_cursors(company_id,mailbox,version,mode,history_id,page_token,initial_since,last_successful_sync)
 values(p_company_id,p_mailbox,p_expected_version+1,p_state->>'mode',p_state->>'history_id',p_state->>'page_token',(p_state->>'initial_since')::bigint,
  case when coalesce((p_state->>'caught_up')::boolean,false) then now() end)
 on conflict(company_id) do update set mailbox=excluded.mailbox,version=excluded.version,mode=excluded.mode,history_id=excluded.history_id,page_token=excluded.page_token,initial_since=excluded.initial_since,last_page_at=now(),last_successful_sync=case when public.gmail_sync_cursors.mailbox<>excluded.mailbox then excluded.last_successful_sync else coalesce(excluded.last_successful_sync,public.gmail_sync_cursors.last_successful_sync) end;
 update public.gmail_sync_cursors set pending_ids=nullif(p_state->'pending_ids','null'::jsonb),pending_page=nullif(p_state->'pending_page','null'::jsonb) where company_id=p_company_id;
 return jsonb_build_object('inserted',n,'version',p_expected_version+1);
end $$
$ddl$);
-- Source: 202609100003_operator_recovery.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('recover_company_work',$ddl$
create function public.recover_company_work(p_company_id uuid,p_expected_owner uuid,p_operator_ref text,p_ticket_ref text,p_workers_stopped boolean)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare work public.gmail_work_locks%rowtype;
begin
 if p_workers_stopped is distinct from true or coalesce(length(trim(p_operator_ref)),0)<3 or coalesce(length(trim(p_ticket_ref)),0)<3 then raise exception 'operator attestation required'; end if;
 select * into work from public.gmail_work_locks where company_id=p_company_id for update;
 if not found then return false; end if;
 if work.owner_id<>p_expected_owner then raise exception 'owner changed; inspect again'; end if;
 insert into public.operation_recovery_audit(company_id,owner_id,purpose,operator_ref,ticket_ref,stopped_workers_confirmed)
 values(p_company_id,work.owner_id,work.purpose,left(p_operator_ref,100),left(p_ticket_ref,100),true);
 update public.gmail_send_operations set status='unknown',updated_at=now() where company_id=p_company_id and status='sending';
 update public.gmail_company_sync_runs set status='failed',error_code='OPERATOR_RECOVERED',finished_at=now() where company_id=p_company_id and status='running';
 delete from public.gmail_work_locks where company_id=p_company_id and owner_id=p_expected_owner;
 return true;
end $$
$ddl$);
-- Source: 202609100004_financial_records.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('save_financial_record',$ddl$
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
end $$
$ddl$);
-- Source: 202609100005_ai_hard_budget.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('reserve_ai_budget',$ddl$
create function public.reserve_ai_budget(p_company_id uuid,p_model text,p_tokens bigint,p_cost_micro_usd bigint,p_token_limit bigint,p_cost_limit_micro_usd bigint)
returns uuid language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare result uuid; used_tokens bigint; used_cost bigint; token_cap bigint; cost_cap bigint;
begin
 if p_tokens is null or p_tokens<1 or p_cost_micro_usd is null or p_cost_micro_usd<1
  or p_token_limit is null or p_token_limit<1 or p_cost_limit_micro_usd is null or p_cost_limit_micro_usd<1
  or coalesce(length(p_model),0)<1 then raise exception 'invalid budget'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_company_id::text,48));
 -- A worker crash remains locked for paid generation until explicit operator review.
 if exists(select 1 from public.ai_budget_reservations where company_id=p_company_id and status='reserved') then return null; end if;
 select coalesce(sum(reserved_tokens),0),coalesce(sum(reserved_cost_micro_usd),0),
  least(p_token_limit,coalesce(min(token_limit),p_token_limit)),
  least(p_cost_limit_micro_usd,coalesce(min(cost_limit_micro_usd),p_cost_limit_micro_usd))
 into used_tokens,used_cost,token_cap,cost_cap from public.ai_budget_reservations
 where company_id=p_company_id and created_at >= date_trunc('month',now() at time zone 'UTC') at time zone 'UTC';
 -- Limits cannot silently increase mid-month after a configuration change.
 if used_tokens+p_tokens>token_cap or used_cost+p_cost_micro_usd>cost_cap then return null; end if;
 insert into public.ai_budget_reservations(company_id,model,reserved_tokens,reserved_cost_micro_usd,token_limit,cost_limit_micro_usd)
 values(p_company_id,p_model,p_tokens,p_cost_micro_usd,token_cap,cost_cap) returning id into result;
 return result;
end $$
$ddl$);
-- Source: 202609100006_account_deletion.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('company_is_active',$ddl$
create function public.company_is_active(p_company_id uuid) returns boolean language sql stable security definer set search_path=pg_catalog,pg_temp as $$
 select exists(select 1 from public.companies where id=p_company_id) and not exists(select 1 from public.account_deletion_jobs where company_id=p_company_id)
$$
$ddl$);
-- Source: 202609100006_account_deletion.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('request_account_deletion',$ddl$
create function public.request_account_deletion(p_user_id uuid,p_retention_days integer) returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare profile public.profiles%rowtype; job public.account_deletion_jobs%rowtype;
begin
 -- Unknown legacy ownership is not evidence of successful per-company erasure.
 if p_retention_days is null or p_retention_days<1 or p_retention_days>3650 then raise exception 'retention configuration required'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_user_id::text,0));
 select * into job from public.account_deletion_jobs where user_id=p_user_id;
 if found then return to_jsonb(job); end if;
 select * into profile from public.profiles where user_id=p_user_id for update;
 if not found or profile.role<>'owner' then raise exception 'owner required'; end if;
 if (select count(*) from public.profiles where company_id=profile.company_id)<>1 then raise exception 'single-user company required'; end if;
 insert into public.account_deletion_jobs(company_id,user_id,purge_after)
 values(profile.company_id,p_user_id,now()+make_interval(days=>p_retention_days)) returning * into job;
 insert into public.account_deletion_audit(job_id,stage) values(job.id,'requested');
 return to_jsonb(job);
end $$
$ddl$);
-- Source: 202609100006_account_deletion.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('purge_account_data',$ddl$
create function public.purge_account_data(p_job_id uuid) returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare job public.account_deletion_jobs%rowtype; t text;
begin
 select * into job from public.account_deletion_jobs where id=p_job_id for update;
 if not found then raise exception 'job missing'; end if;
 if job.status in ('auth','completed') then return; end if;
 if not job.gmail_done or not job.billing_done then raise exception 'provider cleanup pending'; end if;
 if exists(select 1 from public.gmail_connections where company_id=job.company_id) then raise exception 'credential cleanup pending'; end if;
 if exists(select 1 from public.gmail_send_operations where company_id=job.company_id and status in ('sending','unknown')) then raise exception 'send reconciliation required'; end if;
 if exists(select 1 from public.ai_budget_reservations where company_id=job.company_id and status='reserved') then raise exception 'AI reconciliation required'; end if;
 -- Explicit known children only. Unexpected foreign keys fail and roll back all DB deletion.
 foreach t in array array['financial_payments','financial_record_history','financial_records','gmail_inbound_receipts','gmail_sync_cursors',
  'reply_drafts','gmail_send_operations','conversation_analysis_snapshots','ai_budget_reservations','ai_usage_runs',
  'gmail_company_sync_runs','operation_recovery_audit','billing_webhook_events','billing_checkout_attempts',
  'company_billing','timeline','learning_logs','ai_judgements','calendar_events','reply_logs','profit_events','messages','customers','profiles','gmail_work_locks'] loop
  execute format('delete from public.%I where company_id=$1',t) using job.company_id;
 end loop;
 delete from public.companies where id=job.company_id;
 update public.account_deletion_jobs set status='auth',last_error_code=null where id=job.id;
 insert into public.account_deletion_audit(job_id,stage) values(job.id,'data_deleted') on conflict do nothing;
end $$
$ddl$);
-- Source: 202609100006_account_deletion.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('complete_account_deletion',$ddl$
create function public.complete_account_deletion(p_job_id uuid) returns void language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare job public.account_deletion_jobs%rowtype;
begin
 select * into job from public.account_deletion_jobs where id=p_job_id for update;
 if not found then raise exception 'job missing'; end if;
 if job.status='completed' then return; end if;
 if job.status<>'auth' or exists(select 1 from auth.users where id=job.user_id) then raise exception 'auth cleanup pending'; end if;
 -- Count the approved retention interval from completion, not from an earlier
 -- request that may have spent weeks awaiting provider recovery.
 update public.account_deletion_jobs set status='completed',completed_at=now(),
  purge_after=now()+(job.purge_after-job.requested_at),last_error_code=null where id=job.id;
 insert into public.account_deletion_audit(job_id,stage) values(job.id,'completed') on conflict do nothing;
end $$
$ddl$);
-- Source: 202609100006_account_deletion.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('purge_expired_deletion_audit',$ddl$
create function public.purge_expired_deletion_audit() returns bigint language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare n bigint;
begin
 delete from public.account_deletion_jobs where status='completed' and purge_after<now();
 get diagnostics n=row_count; return n;
end $$
$ddl$);
-- Source: 202609100006_account_deletion.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('prevent_deleted_user_onboarding',$ddl$
create function public.prevent_deleted_user_onboarding() returns trigger language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
begin
 perform pg_advisory_xact_lock(hashtextextended(new.user_id::text,0));
 if exists(select 1 from public.account_deletion_jobs where user_id=new.user_id) then raise exception 'deletion requested'; end if;
 return new;
end $$
$ddl$);
-- Source: 202609100007_payment_entries.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('record_financial_payment',$ddl$
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
end $$
$ddl$);
-- Source: 202609100007_payment_entries.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('void_financial_payment',$ddl$
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
end $$
$ddl$);
-- Source: 202609100008_provider_recovery.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('resolve_provider_uncertainty',$ddl$
create function public.resolve_provider_uncertainty(p_company_id uuid,p_expected_id uuid,p_kind text,p_operator_ref text,p_ticket_ref text,p_workers_stopped boolean,p_provider_reviewed boolean)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare current_status text;
begin
 if p_workers_stopped is distinct from true or p_provider_reviewed is distinct from true
 or coalesce(length(trim(p_operator_ref)),0)<3 or coalesce(length(trim(p_ticket_ref)),0)<3 then
  raise exception 'operator and provider review required';
 end if;
 if p_kind not in ('ai','gmail-revoke') or p_kind is null then raise exception 'invalid recovery kind'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_company_id::text,48));
 -- This is not a stale-lock takeover. Recover that lock separately after review.
 if exists(select 1 from public.gmail_work_locks where company_id=p_company_id) then raise exception 'company work unresolved'; end if;
 if p_kind='ai' then
  select status into current_status from public.ai_budget_reservations where id=p_expected_id and company_id=p_company_id for update;
  if not found or current_status<>'reserved' then return false; end if;
  update public.ai_budget_reservations set status='reviewed_unknown' where id=p_expected_id and company_id=p_company_id;
 else
  -- Human must verify removal in Google account permissions, not infer it from
  -- a generic HTTP 400. Exact row/status fence prevents touching a reconnect.
  select status into current_status from public.gmail_connections where id=p_expected_id and company_id=p_company_id for update;
  if not found then return false; end if;
  if current_status<>'revocation_pending' then raise exception 'connection changed'; end if;
  delete from public.gmail_connections where id=p_expected_id and company_id=p_company_id and status='revocation_pending';
 end if;
 insert into public.operation_recovery_audit(company_id,owner_id,purpose,operator_ref,ticket_ref,stopped_workers_confirmed)
 values(p_company_id,p_expected_id,p_kind,left(p_operator_ref,100),left(p_ticket_ref,100),true);
 return true;
end $$
$ddl$);
-- Source: 202609110001_billing_production_gate.sql. No CREATE OR REPLACE of existing remote functions.
SELECT pg_temp.forward_function('promote_billing_live',$ddl$
create function public.promote_billing_live(p_approval_ref text,p_workers_stopped boolean)
returns boolean language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare current_row public.billing_runtime_config%rowtype;
begin
 if p_workers_stopped is distinct from true or p_approval_ref is null
 or p_approval_ref !~ '^[A-Za-z0-9_-]{3,100}$' then raise exception 'approval and stopped workers required'; end if;
 lock table public.company_billing,public.billing_checkout_attempts,public.billing_webhook_events in share row exclusive mode;
 select * into strict current_row from public.billing_runtime_config where singleton for update;
 if current_row.mode='live' then
  if current_row.approval_ref<>p_approval_ref then raise exception 'approval mismatch'; end if;
  return false;
 end if;
 -- Never turn test subscriptions, unknown checkout attempts or paid access into live entitlements.
 if exists(select 1 from public.company_billing where stripe_subscription_id is not null or paid_until is not null or status not in ('trial','trial_expired'))
 or exists(select 1 from public.billing_checkout_attempts)
 or exists(select 1 from public.billing_webhook_events) then raise exception 'test billing history exists; use a separate reviewed production database'; end if;
 update public.billing_runtime_config set mode='live',approval_ref=p_approval_ref,approved_at=now() where singleton;
 return true;
end $$
$ddl$);

DO $trigger$
DECLARE existing pg_trigger%rowtype;
BEGIN
 SELECT * INTO existing FROM pg_trigger WHERE tgrelid='public.profiles'::regclass AND tgname='prevent_deleted_user_onboarding';
 IF NOT FOUND THEN
  CREATE TRIGGER prevent_deleted_user_onboarding BEFORE INSERT ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.prevent_deleted_user_onboarding();
 ELSIF existing.tgfoid<>'public.prevent_deleted_user_onboarding()'::regprocedure
 OR existing.tgtype<>7 OR existing.tgenabled<>'O' OR existing.tgqual IS NOT NULL OR existing.tgnargs<>0 OR existing.tgisinternal THEN
  RAISE EXCEPTION 'FORWARD: onboarding trigger conflict';
 END IF;
END $trigger$;
-- PostgREST reload only after commit. No cron/worker/provider invocation.
NOTIFY pgrst, 'reload schema';
COMMIT;
