"""Dedicated local Docker only. Retains new synthetic databases; never resets a DB.

Run from backend with --allow-disposable-fixtures. No remote URL option, keys,
provider calls, migrations history repairs, or customer rows in the output.
"""
import argparse
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


def rows_fingerprint(db, tables):
    # Only synthetic databases; digest calculated by PostgreSQL, no row content output.
    parts = []
    for table in tables:
        if not re.fullmatch(r"[a-z_]+", table):
            raise ValueError("Invalid table")
        parts.append(f"select '{table}' as name,md5(coalesce(string_agg(j,',' order by j),'')) as digest from "
                     f"(select to_jsonb(t)::text j from public.{table} t) x")
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
        sql(db, 'set role postgres; alter table public.companies add column owner_user_id uuid; drop function public.onboard_user(uuid,text,text,text); '
            + '\n'.join(definitions) + '''
revoke all on function public.create_company_and_profile(text,text) from public,anon,service_role;
grant execute on function public.create_company_and_profile(text,text) to authenticated;
''')
    legacy_tables = sql(db, "select tablename from pg_tables where schemaname='public' order by 1;").splitlines()
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
    before = rows_fingerprint(db, legacy_tables + ["unrelated_forward_sentinel"])
    sql(db, "set role postgres;\n" + forward)
    assert before == rows_fingerprint(db, legacy_tables + ["unrelated_forward_sentinel"])
    assert sql(db, "select has_table_privilege('authenticated','public.unrelated_forward_sentinel','SELECT');") == "t"
    assert sql(db, "select mode from public.billing_runtime_config;") == "test"
    all_tables = sql(db, "select tablename from pg_tables where schemaname='public' order by 1;").splitlines()
    committed_rows = rows_fingerprint(db, all_tables)
    signature = schema_fingerprint(db)
    sql(db, "set role postgres;\n" + forward)
    assert signature == schema_fingerprint(db)
    if v2:
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
            ("alter table public.companies alter column owner_user_id type text using owner_user_id::text;", "prerequisite column/type mismatch"),
            ("alter table public.billing_checkout_attempts add column unexpected text;", "incompatible existing table"),
            ("create index unexpected_checkout on public.billing_checkout_attempts(session_id);", "unexpected checkout index"),
        ])
    for mutation, expected in cases:
        print(json.dumps({"checking_rejection": expected}), flush=True)
        error = 'FORWARD_V2: untrusted schema CREATE' if v2 and expected == 'untrusted public schema CREATE' else 'FORWARD: ' + expected
        sql(db, "begin; set role postgres;\n" + mutation + "\n" + forward, error if expected != 'unexpected checkout index' else expected)
        assert signature == schema_fingerprint(db)
        assert before == rows_fingerprint(db, legacy_tables + ["unrelated_forward_sentinel"])
        assert committed_rows == rows_fingerprint(db, all_tables)
    if v2:
        identity_cases = [
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
