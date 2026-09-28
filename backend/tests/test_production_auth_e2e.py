"""Production runner guards and a separately gated disposable-local exercise."""

import importlib.util
from pathlib import Path
import sys

import pytest
from supabase import create_client


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("run_production_auth_e2e", SCRIPTS / "run_production_auth_e2e.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize("ref,flag,url", [
    ("other", runner.CONFIRMATION, runner.URL),
    (runner.PROJECT_REF, "", runner.URL),
    (runner.PROJECT_REF, runner.CONFIRMATION, "http://127.0.0.1:54321"),
])
def test_production_gate_rejects_mismatch(ref, flag, url):
    with pytest.raises(runner.GateError, match="gate not satisfied"):
        runner.validate_gate(ref, flag, url)


def test_runner_has_no_provider_or_disposable_isolation_invocation():
    source = (SCRIPTS / "run_production_auth_e2e.py").read_text(encoding="utf-8")
    for forbidden in ("test_p0_supabase_isolation.py", ".send_message(", "stripe_request(",
                      "check-replies", "supabase db push"):
        if forbidden == "test_p0_supabase_isolation.py":
            assert source.count(forbidden) == 1  # docstring prohibition only
        else:
            assert forbidden not in source
    assert "no_op_delete_preflight(service)" in source
    assert "cleanup(service, actors)" in source
    assert 'browser.table("customers").update' in source
    assert 'browser.table("profit_events").delete' in source
    assert 'browser.rpc("onboard_user"' in source
    assert 'browser.rpc("request_account_deletion"' in source


def test_disposable_local_auth_and_cleanup(monkeypatch):
    if __import__("os").getenv("PR_AUTH_E2E_LOCAL_TEST") != "ALLOW_DISPOSABLE_LOCAL":
        pytest.skip("Explicit disposable-local Auth E2E fixture gate not set")
    sys.path.insert(0, str(SCRIPTS))
    from run_local_regression import local_credentials
    from validate_forward_local import validate_target

    validate_target(True)
    keys = local_credentials()
    local_url = "http://127.0.0.1:54321"
    monkeypatch.setattr(runner, "URL", local_url)
    # The default disposable DB predates production v2's canonical RPC ACL.
    # Use explicit local service-role fixture registration; the canonical RPC
    # itself is covered by the separate v2 synthetic-DB JWT validator.
    def local_register(service, anon, run_marker, index, actors):
        import secrets
        from uuid import uuid4
        marker = f"PR-PROD-E2E-{run_marker}-{index}"
        email = f"pr-e2e-{run_marker}-{index}@example.invalid"
        password = secrets.token_urlsafe(40)
        actor = {"marker": marker, "auth_outcome_unknown": True}
        actors.append(actor)
        actor["stage"] = "local-auth-create"
        user = service.auth.admin.create_user({"email": email, "password": password,
                                               "email_confirm": True}).user
        actor["user_id"] = str(user.id)
        actor["auth_outcome_unknown"] = False
        actor["stage"] = "local-auth-login"
        browser = create_client(local_url, anon)
        session = browser.auth.sign_in_with_password({"email": email, "password": password}).session
        actor["stage"] = "local-company-insert"
        # Local default PostgREST does not grant service INSERT on companies.
        # SQL fixture creation is confined to the validated disposable DB.
        import subprocess
        def local_sql(statement):
            completed = subprocess.run(["docker", "exec", "-i",
                "supabase_db_profit-radar-disposable", "psql", "-X", "-q", "-At", "-h",
                "/var/run/postgresql", "-U", "postgres", "-d", "postgres",
                "-v", "ON_ERROR_STOP=1", "-f", "-"], input=statement.encode(),
                capture_output=True, timeout=30, check=False)
            assert completed.returncode == 0, "Disposable fixture SQL failed: " + completed.stderr.decode("utf-8", "replace").splitlines()[0]
            return completed.stdout.decode().strip().splitlines()[0]
        actor["company_id"] = local_sql("insert into public.companies(name) "
            f"values ('{marker}') returning id;")
        actor["stage"] = "local-profile-insert"
        actor["profile_id"] = local_sql("insert into public.profiles(user_id,company_id,name,full_name,email,role) "
            f"values ('{actor['user_id']}','{actor['company_id']}','{marker}','{marker}','{email}','owner') returning id;")
        browser.postgrest.auth(session.access_token)
        actor["browser"] = browser
        actor["headers"] = {"Authorization": "Bearer " + session.access_token}
        return actor
    monkeypatch.setattr(runner, "register_actor", local_register)
    production_verify = runner.verify
    monkeypatch.setattr(runner, "verify", lambda service, anon, patch, actors:
                        production_verify(service, anon, patch, actors,
                                          require_company_owner=False))
    production_one_row = runner.one_row
    def local_one_row(service, table, row_id, fields, expected):
        if table == "companies":
            fields = "id,name"
            expected = {"name": expected["name"]}
        return production_one_row(service, table, row_id, fields, expected)
    monkeypatch.setattr(runner, "one_row", local_one_row)
    production_cleanup = runner.cleanup
    monkeypatch.setattr(runner, "cleanup", lambda service, actors:
                        production_cleanup(service, actors, owner_filter=False))
    result = runner.exercise(create_client(local_url, keys["service_role"]), keys["anon"],
                             monkeypatch, record=False)
    assert result == {"result": "PASS", "cleanup": "PASS",
                      "count_delta": {table: 0 for table in runner.COUNT_TABLES}}
