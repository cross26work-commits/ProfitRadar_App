"""Dedicated local Docker only. Retains new synthetic databases; never resets a DB.

Run from backend with --allow-disposable-fixtures. No remote URL option, keys,
provider calls, migrations history repairs, or customer rows in the output.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = "supabase_db_profit-radar-disposable"
FORWARD = ROOT / "supabase/migrations/202609140001_remote_schema_forward.sql"
FORWARD_V2 = ROOT / "supabase/migrations/202609150001_remote_schema_forward_v2.sql"
REMOTE_CANONICAL_LF_SHA256 = '12a8812b782d2d2fd1d41a9199f12199d0c3767e76d4cfbe649ccdb15d1b08d2'
REMOTE_CANONICAL_RAW_SHA256 = 'e426bdea084dfd662e3c766eeec3853588ae03affc16f7d7f885a576ec9f48ac'
REMOTE_POLICY_SHA256 = 'df734f55b6379d0c2983d658aa15e6d93a667efe5200a13b6b4199cb9905dcc2'


def remote_policy_oracle():
    raw = (ROOT / 'docs/remote_policy_snapshot_20260915.json').read_bytes()
    if len(raw) != 1016 or hashlib.sha256(raw).hexdigest() != REMOTE_POLICY_SHA256:
        raise ValueError('Remote policy oracle corrupted')
    policies = json.loads(raw)
    if len(policies) != 4:
        raise ValueError('Remote policy count mismatch')
    for path in (FORWARD_V2, ROOT / 'supabase/remote_schema_forward_preflight.sql'):
        embedded = json.loads(path.read_text(encoding='utf-8').split('$policy_oracle$')[1])
        if sorted(embedded, key=lambda p: (p['tablename'], p['policyname'])) != sorted(policies, key=lambda p: (p['tablename'], p['policyname'])):
            raise ValueError('Remote policy pin mismatch')
    return policies


def canonical_oracle_bytes():
    """Lossless repository copy of independent capture, not a generated SQL fixture."""
    capture = json.loads((ROOT / 'docs/create_company_and_profile_remote_capture.json').read_text(encoding='utf-8'))
    raw = base64.b64decode(capture['raw_base64'], validate=True)
    if len(raw) != 847 or hashlib.sha256(raw).hexdigest() != REMOTE_CANONICAL_RAW_SHA256:
        raise ValueError('Independent raw capture corrupted')
    normalized = raw.replace(b'\r\n', b'\n')
    if hashlib.sha256(normalized).hexdigest() != REMOTE_CANONICAL_LF_SHA256:
        raise ValueError('Independent LF capture corrupted')
    normalized.decode('utf-8', errors='strict')
    return raw


def canonical_capture_hashes():
    """Independent user-supplied remote digest; never derive approval from fixtures."""
    paths = {
        'docs': ROOT / 'docs/remote_onboarding_functiondefs_20260915_exact.txt',
        'preflight': ROOT / 'supabase/remote_schema_forward_preflight.sql',
        'migration': FORWARD_V2,
    }
    hashes = {}
    for name, path in paths.items():
        text = path.read_bytes().decode('utf-8', errors='strict')
        if name == 'docs':
            canonical = text.split('CREATE OR REPLACE FUNCTION public.create_company_and_profile(', 1)[1]
            body = canonical.split('AS $function$', 1)[1].split('$function$;', 1)[0]
        else:
            body = text.split('$canonical_body$')[1]
        # No strip, indentation removal, universal newline reader or other normalization.
        hashes[name] = hashlib.sha256(body.replace('\r\n', '\n').encode('utf-8')).hexdigest()
    return hashes


def validate_canonical_capture():
    canonical_oracle_bytes()
    hashes = canonical_capture_hashes()
    if any(value != REMOTE_CANONICAL_LF_SHA256 for value in hashes.values()):
        raise ValueError('Remote canonical capture hash mismatch; no validation database created: ' + json.dumps(hashes))
    return hashes


def command(args, input=None, expected_error=None):
    result = subprocess.run(args, input=input, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=180)
    if expected_error:
        if result.returncode == 0 or expected_error not in result.stderr:
            raise RuntimeError("Expected migration guard did not reject the test case")
        return "EXPECTED_REJECTION"
    if result.returncode:
        # Do not echo SQL, environment, data, or provider credentials.
        codes = re.findall(r"(?:ERROR|FATAL):\s+([^\n]{0,120})", result.stderr)
        raise RuntimeError("Local validation command failed: " + (codes[0] if codes else "inspect isolated engine"))
    return result.stdout.strip()


def validate_target(approved):
    if not approved or os.getenv("DOCKER_HOST") or os.getenv("DOCKER_CONTEXT"):
        raise ValueError("Explicit local fixture approval and default Docker endpoint required")
    context = json.loads(command(["docker", "context", "inspect"]))[0]
    endpoint = context.get("Endpoints", {}).get("docker", {}).get("Host", "")
    if not (endpoint.startswith("npipe://") or endpoint == "unix:///var/run/docker.sock"):
        raise ValueError("Local Docker socket required")
    info = json.loads(command(["docker", "inspect", CONTAINER]))[0]
    if (info.get("Config", {}).get("Labels", {}).get("com.supabase.cli.project") != "profit-radar-disposable"
            or not info.get("State", {}).get("Running")):
        raise ValueError("Disposable Supabase identity mismatch")
    ports = info.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp", []) or []
    if not ports or any(p.get("HostPort") != "54322" or p.get("HostIp") not in
                        {"127.0.0.1", "::1", "0.0.0.0", "::"} for p in ports):
        raise ValueError("Disposable port mismatch")


def sql(db, source, expected_error=None):
    if not re.fullmatch(r"pr_forward_[a-f0-9]{32}", db):
        raise ValueError("Only newly generated validation DB names allowed")
    return command(["docker", "exec", "-i", CONTAINER, "psql", "-X", "-q", "-At",
                    "-h", "/var/run/postgresql", "-U", "supabase_admin", "-d", db,
                    "-v", "ON_ERROR_STOP=1"], source, expected_error)


def rows_fingerprint(db, tables, ignore_added=False):
    # Only synthetic databases; digest calculated by PostgreSQL, no row content output.
    parts = []
    for table in tables:
        if not re.fullmatch(r"[a-z_]+", table):
            raise ValueError("Invalid table")
        omitted = {'profit_events': ['description', 'neglected_days', 'recoverable_profit']}.get(table, []) if ignore_added else []
        expression = 'to_jsonb(t)' + ''.join(" - '" + column + "'" for column in omitted)
        parts.append(f"select '{table}' as name,md5(coalesce(string_agg(j,',' order by j),'')) as digest from "
                     f"(select ({expression})::text j from public.{table} t) x")
    result = sql(db, "select md5(string_agg(name||':'||digest,'|' order by name)) from (" +
                 " union all ".join(parts) + ") checks;")
    return result


def schema_fingerprint(db):
    # Includes only persistent schema; ignores ephemeral helper OIDs / ordering of ACL arrays.
    text = sql(db, """
select string_agg(x,'|' order by x) from (
 select 'column:'||table_name||':'||column_name||':'||data_type||':'||is_nullable||':'||coalesce(column_default,'') x
 from information_schema.columns where table_schema='public'
 union all select 'function:'||proname||':'||prosrc||':'||coalesce(proconfig::text,'') from pg_proc where pronamespace='public'::regnamespace
 union all select 'policy:'||tablename||':'||policyname||':'||coalesce(qual,'')||':'||coalesce(with_check,'') from pg_policies where schemaname='public'
 union all select 'index:'||indexdef from pg_indexes where schemaname='public'
 union all select 'grant:'||table_name||':'||grantee||':'||privilege_type from information_schema.role_table_grants where table_schema='public'
 union all select 'column_grant:'||table_name||':'||column_name||':'||grantee||':'||privilege_type from information_schema.role_column_grants where table_schema='public'
) x;
""")
    return hashlib.sha256(text.encode()).hexdigest()


def run(approved=False, v2=False):
    if v2 and approved:
        validate_canonical_capture()
        remote_policy_oracle()
    validate_target(approved)
    db = "pr_forward_" + uuid4().hex
    command(["docker", "exec", CONTAINER, "createdb", "-h", "/var/run/postgresql",
             "-U", "supabase_admin", "-T", "template0", db])
    print(json.dumps({"retained_validation_db": db}), flush=True)
    # Auth schema only; no real Auth rows, credentials, or secrets copied.
    auth_schema = command(["docker", "exec", CONTAINER, "pg_dump", "-h", "/var/run/postgresql",
                           "-U", "supabase_admin", "-d", "postgres", "--schema-only", "-n", "auth"])
    sql(db, auth_schema)
    # Reproduce Supabase default service-role grants in this new DB only.
    sql(db, """grant usage,create on schema public to postgres;
grant usage on schema public to anon,authenticated,service_role;
alter default privileges for role postgres in schema public grant all on tables to service_role;
""")
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    for path in migrations:
        if path.name >= "202609100002":
            break
        if v2 and path.name.startswith('202609090007'):
            continue
        sql(db, "set role postgres; set search_path=public,extensions;\n" + path.read_text(encoding="utf-8"))
        if path.name.startswith("202607020001"):
            sql(db, "set role postgres;\n" + (ROOT / "backend/tests/isolated/baseline.sql").read_text(encoding="utf-8"))
    if v2:
        evidence = (ROOT / 'docs/remote_onboarding_functiondefs_20260915_exact.txt').read_text(encoding='utf-8')
        definitions = re.findall(r'CREATE OR REPLACE FUNCTION[\s\S]*?\$function\$;', evidence)
        assert len(definitions) == 2
        # New synthetic DB only: model observed remote instead of the newer local RPC.
        sql(db, 'set role postgres; alter table public.companies add column owner_user_id uuid default auth.uid(); drop function public.onboard_user(uuid,text,text,text); '
            + '\n'.join(definitions) + '''
revoke all on function public.create_company_and_profile(text,text) from public,anon,service_role;
grant execute on function public.create_company_and_profile(text,text) to authenticated;
''')
        # Model observed missing columns and ACLs, not unknown remote policy bodies.
        sql(db, '''set role postgres;
alter table public.companies drop column updated_at;
alter table public.profiles drop column updated_at;
alter table public.gmail_sync_runs drop column company_id;
alter table public.gmail_sync_runs drop column error_code;
alter table public.gmail_sync_runs drop column detected_count;
alter table public.gmail_sync_runs drop constraint gmail_sync_runs_status_check;
alter table public.gmail_sync_runs add constraint gmail_sync_runs_status_check check(status in ('running','completed','failed','skipped'));
alter table public.gmail_sync_runs add column company_count integer not null default 0;
alter table public.gmail_sync_runs add column success_count integer not null default 0;
alter table public.gmail_sync_runs add column failure_count integer not null default 0;
alter table public.gmail_sync_runs add column detected_reply_count integer not null default 0;
alter table public.gmail_sync_runs add column error_summary jsonb not null default '[]'::jsonb;
alter table public.profit_events drop column description;
alter table public.profit_events drop column neglected_days;
alter table public.profit_events drop column recoverable_profit;
grant truncate,trigger,references on public.ai_judgements,public.calendar_events,public.companies,public.customers,public.gmail_connections,public.learning_logs,public.messages,public.profiles,public.profit_events,public.reply_logs,public.timeline to anon,authenticated;
grant insert,update on public.companies,public.profiles to authenticated;
''')
        # Replace repository fixture policies in this NEW disposable DB only.
        sql(db, '''set role postgres;
drop policy legacy_broad_profiles on public.profiles;
drop policy profiles_select_own on public.profiles;
drop policy profiles_self_boundary on public.profiles;
drop policy companies_own_read on public.companies;
drop policy companies_self_boundary on public.companies;
''')
        for policy in remote_policy_oracle():
            assert policy['tablename'] in {'companies', 'profiles'} and policy['roles'] == ['authenticated']
            statement = f"CREATE POLICY {policy['policyname']} ON public.{policy['tablename']} AS {policy['permissive']} FOR {policy['cmd']} TO authenticated"
            if policy['qual'] is not None:
                statement += ' USING (' + policy['qual'] + ')'
            if policy['with_check'] is not None:
                statement += ' WITH CHECK (' + policy['with_check'] + ')'
            sql(db, 'set role postgres;' + statement + ';')
    legacy_tables = sql(db, "select tablename from pg_tables where schemaname='public' order by 1;").splitlines()
    global_acl = sql(db, "select coalesce(relacl::text,'NULL') from pg_class where oid='public.gmail_sync_runs'::regclass;")
    canonical_before = sql(db, "select pg_get_functiondef(oid)||proacl::text from pg_proc where oid='public.create_company_and_profile(text,text)'::regprocedure;") if v2 else None
    # The empty fresh DB path and populated old-schema path are both exercised.
    forward = (FORWARD_V2 if v2 else FORWARD).read_text(encoding="utf-8")
    sql(db, "set role postgres;\n" + forward.replace("COMMIT;", "ROLLBACK;"))
    assert sql(db, "select to_regclass('public.gmail_sync_cursors') is null;") == "t"
    company, customer, event = (str(uuid4()) for _ in range(3))
    sql(db, f"""insert into public.companies(id,name) values('{company}','FORWARD SYNTHETIC');
insert into public.customers(id,company_id,name,email) values('{customer}','{company}','FORWARD SYNTHETIC','forward@example.invalid');
insert into public.profit_events(id,company_id,customer_id,title) values('{event}','{company}','{customer}','FORWARD SYNTHETIC');
create table public.unrelated_forward_sentinel(id integer primary key, marker text);
insert into public.unrelated_forward_sentinel values(1,'preserve');
grant select on public.unrelated_forward_sentinel to authenticated;
""")
    before = rows_fingerprint(db, legacy_tables + ["unrelated_forward_sentinel"], ignore_added=v2)
    sql(db, "set role postgres;\n" + forward)
    assert before == rows_fingerprint(db, legacy_tables + ["unrelated_forward_sentinel"], ignore_added=v2)
    assert sql(db, "select has_table_privilege('authenticated','public.unrelated_forward_sentinel','SELECT');") == "t"
    assert sql(db, "select mode from public.billing_runtime_config;") == "test"
    all_tables = sql(db, "select tablename from pg_tables where schemaname='public' order by 1;").splitlines()
    committed_rows = rows_fingerprint(db, all_tables)
    signature = schema_fingerprint(db)
    sql(db, "set role postgres;\n" + forward)
    assert signature == schema_fingerprint(db)
    assert global_acl == sql(db, "select coalesce(relacl::text,'NULL') from pg_class where oid='public.gmail_sync_runs'::regclass;")
    if v2:
        # Known observed ACL drift is corrected on replay; no persistent row changes.
        sql(db, 'set role postgres; grant truncate,trigger,references on public.customers to public,anon,authenticated; grant update(email) on public.profiles to authenticated;')
        sql(db, 'set role postgres;' + forward)
        assert signature == schema_fingerprint(db)
        assert committed_rows == rows_fingerprint(db, all_tables)
        assert canonical_before == sql(db, "select pg_get_functiondef(oid)||proacl::text from pg_proc where oid='public.create_company_and_profile(text,text)'::regprocedure;")
    cases = [
        ("alter table public.financial_records add column unexpected text;", "incompatible existing table"),
        ("create policy unexpected on public.gmail_sync_cursors for select to authenticated using(true);", "unexpected policy/trigger"),
        ("grant select(mailbox) on public.gmail_sync_cursors to authenticated;", "browser effective"),
        ("alter index public.ai_budget_company_month rename to fixture_original_index; create index ai_budget_company_month on public.ai_budget_reservations(model);", "index definition mismatch"),
        ("create function public.reserve_ai_budget(text) returns int language sql as 'select 1';", "function overload conflict"),
        ("alter function public.company_is_active(uuid) set search_path=public;", "existing function differs"),
        ("set role supabase_admin; grant create on schema public to authenticated; set role postgres;", "untrusted public schema CREATE"),
        ("create view public.fixture_cursor_leak as select * from public.gmail_sync_cursors; grant select on public.fixture_cursor_leak to anon;", "dependent view requires explicit review"),
        ("alter table public.profiles enable always trigger prevent_deleted_user_onboarding;", "onboarding trigger conflict"),
        ("update public.billing_runtime_config set approval_ref='fixture-unapproved';", "test-only billing configuration required"),
    ]
    if v2:
        cases.extend([
            ("alter table public.gmail_sync_runs add column company_id uuid;", "global sync schema mismatch"),
            ("alter table public.gmail_sync_runs alter column company_count drop not null;", "global sync schema mismatch"),
            ("alter table public.gmail_sync_runs alter column error_summary set default '{}';", "global sync schema mismatch"),
            ("insert into public.gmail_sync_runs(status) values('completed');", "global sync rows require review"),
            ("alter table public.profit_events alter column description set default 'unknown';", "legacy column contract mismatch"),
            ("alter table public.profit_events alter column neglected_days type bigint;", "legacy column contract mismatch"),
            ("alter table public.profit_events alter column recoverable_profit type text using recoverable_profit::text;", "legacy column contract mismatch"),
            ("create policy unknown on public.profiles for select to authenticated using(true);", "unknown legacy policy"),
            ("alter policy profiles_update_own on public.profiles using(true);", "unknown legacy policy"),
            ("alter policy companies_insert_own on public.companies to authenticated,anon;", "unknown legacy policy"),
            ("grant select on public.customers to authenticator;", "unexpected legacy grantee"),
            ("alter table public.companies alter column owner_user_id type text using owner_user_id::text;", "prerequisite column/type mismatch"),
            ("alter table public.companies alter column owner_user_id drop default;", "prerequisite column/type mismatch"),
            ("alter table public.companies alter column owner_user_id set default gen_random_uuid();", "prerequisite column/type mismatch"),
            ("update public.companies set owner_user_id=gen_random_uuid() where owner_user_id is null; alter table public.companies alter column owner_user_id set not null;", "prerequisite column/type mismatch"),
            ("alter table public.billing_checkout_attempts add column unexpected text;", "incompatible existing table"),
            ("create index unexpected_checkout on public.billing_checkout_attempts(session_id);", "unexpected checkout index"),
        ])
    for mutation, expected in cases:
        print(json.dumps({"checking_rejection": expected}), flush=True)
        # Disposable transaction only: PostgreSQL otherwise rejects the type mutation
        # BEFORE the migration because the authoritative policies depend on this column.
        # Keep the uuid -> text case unchanged; all removed fixture policies roll back.
        if mutation == "alter table public.companies alter column owner_user_id type text using owner_user_id::text;":
            mutation = ("drop policy companies_insert_own on public.companies; "
                        "drop policy companies_select_member_or_owner on public.companies; " + mutation)
        error = 'FORWARD_V2: untrusted schema CREATE' if v2 and expected == 'untrusted public schema CREATE' else 'FORWARD: ' + expected
        sql(db, "begin; set role postgres;\n" + mutation + "\n" + forward, error if expected != 'unexpected checkout index' else expected)
        assert signature == schema_fingerprint(db)
        assert before == rows_fingerprint(db, legacy_tables + ["unrelated_forward_sentinel"], ignore_added=v2)
        assert committed_rows == rows_fingerprint(db, all_tables)
    if v2:
        identity_cases = [
            (definitions[1].replace('\ndeclare\n', '\ndeclare\n ') , 'exact body/arguments'),
            ("alter function public.onboard_user(uuid,text,text,text) set search_path=public;", 'onboarding ACL mismatch'),
            ("alter function public.onboard_user(uuid,text,text,text) security invoker;", 'owner/security/contract'),
            ("set role supabase_admin; alter function public.onboard_user(uuid,text,text,text) owner to supabase_admin; set role postgres;", 'owner/security/contract'),
            ("create function public.onboard_user(text) returns int language sql as 'select 1';", 'overload conflict'),
            ("alter function public.create_company_and_profile(text,text) set search_path=public;", 'canonical config/return'),
            ("grant execute on function public.create_company_and_profile(text,text) to anon;", 'ACL mismatch'),
            ("alter function public.onboard_user(uuid,text,text,text) set statement_timeout='1s';", 'legacy config/return'),
            ("create or replace function public.create_company_and_profile(company_name text,owner_name text) returns uuid language plpgsql security definer set search_path=pg_catalog,public as $$begin return null; end$$;", 'exact body/arguments'),
            ("create or replace function public.onboard_user(p_user_id uuid,p_company_name text,p_name text,p_email text) returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$begin return '{}'::jsonb; end$$;", 'exact body/arguments'),
        ]
        for mutation, expected in identity_cases:
            print(json.dumps({'identity_rejection': expected}), flush=True)
            sql(db, 'begin; set role postgres;' + mutation + forward, expected)
            assert signature == schema_fingerprint(db)
            assert committed_rows == rows_fingerprint(db, all_tables)
    jwt_result = None
    if v2:
        from validate_v2_jwt import verify
        jwt_result = verify(db)
    return {"validation_db": db, "fresh_apply_rollback": True, "legacy_forward_commit": True,
            "legacy_rows_unchanged": True, "unrelated_acl_unchanged": True,
            "replay_no_schema_or_data_drift": True, "conflict_rollbacks": len(cases),
            "billing_mode": "test", "remote_access": False,
            "v2_full": v2, "identity_rollbacks": len(identity_cases) if v2 else 0, 'jwt': jwt_result}


def checkout_only_v2(approved=False):
    """Isolated component proof, NOT proof that the blocked full v2 can commit."""
    validate_target(approved)
    source = FORWARD_V2.read_text(encoding="utf-8")
    helpers = re.search(r"CREATE FUNCTION pg_temp.forward_table_signature[\s\S]*?END \$helper\$;", source).group()
    table = re.search(r"SELECT pg_temp.forward_table\('billing_checkout_attempts'[\s\S]*?\$ddl\$\);", source).group()
    indexes = re.search(r"DO \$checkout_indexes\$[\s\S]*?END \$checkout_indexes\$;", source).group()
    acl = re.search(r"DO \$acl\$[\s\S]*?END \$acl\$;", source).group()
    acl = re.sub(r"FOREACH t IN ARRAY ARRAY\[[^\]]+\]", "FOREACH t IN ARRAY ARRAY['billing_checkout_attempts']", acl)
    component = ("BEGIN; SET ROLE postgres; SET LOCAL search_path=pg_catalog,public,pg_temp; "
                 "CREATE TEMP TABLE forward_created(name text primary key) ON COMMIT DROP; "
                 "CREATE TEMP TABLE companies (LIKE public.companies INCLUDING ALL) ON COMMIT DROP; "
                 + helpers + table + indexes + acl + "COMMIT;")
    db = "pr_forward_" + uuid4().hex
    command(["docker", "exec", CONTAINER, "createdb", "-h", "/var/run/postgresql", "-U", "supabase_admin", "-T", "template0", db])
    sql(db, "grant create,usage on schema public to postgres; grant usage on schema public to anon,authenticated,service_role; "
            "set role postgres; create table public.companies(id uuid primary key); "
            "insert into public.companies values('11111111-1111-4111-8111-111111111111');")
    before = rows_fingerprint(db, ["companies"])
    sql(db, component)
    sql(db, "set role service_role; insert into public.billing_checkout_attempts(company_id,attempt_id) "
            "values('11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222');")
    signature = schema_fingerprint(db)
    rows = rows_fingerprint(db, ["companies", "billing_checkout_attempts"])
    sql(db, component)
    assert schema_fingerprint(db) == signature
    assert rows_fingerprint(db, ["companies", "billing_checkout_attempts"]) == rows
    cases = [
        ("alter table public.billing_checkout_attempts add column unexpected text;", "incompatible existing table"),
        ("create policy unexpected on public.billing_checkout_attempts for select to authenticated using(true);", "unexpected policy/trigger"),
        ("grant select(session_id) on public.billing_checkout_attempts to authenticated;", "browser effective"),
        ("create index unexpected_checkout_index on public.billing_checkout_attempts(session_id);", "unexpected checkout index"),
    ]
    for mutation, expected in cases:
        sql(db, "BEGIN; SET ROLE postgres;" + mutation + component, expected)
        assert signature == schema_fingerprint(db)
        assert rows_fingerprint(db, ["companies", "billing_checkout_attempts"]) == rows
    assert before == rows_fingerprint(db, ["companies"])
    return {"checkout_component_pass": True, "component_rejections": len(cases), "database": db,
            "full_v2_pass": False, "reason": "Component-only run; use default full validator for v2 proof", "remote_access": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-disposable-fixtures", action="store_true")
    parser.add_argument("--checkout-only-v2", action="store_true")
    parser.add_argument("--legacy-v1-validation", action="store_true")
    args = parser.parse_args()
    if args.checkout_only_v2:
        print(json.dumps(checkout_only_v2(args.allow_disposable_fixtures)))
    elif args.legacy_v1_validation:
        print(json.dumps(run(args.allow_disposable_fixtures)))
    else:
        print(json.dumps(run(args.allow_disposable_fixtures, v2=True)))
