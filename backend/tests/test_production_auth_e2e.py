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
    ("other", runner.CONFIRMATION_PREFIX + ":abcdefghijklmnopqrst", "https://abcdefghijklmnopqrst.supabase.co"),
    ("abcdefghijklmnopqrst", "", "https://abcdefghijklmnopqrst.supabase.co"),
    ("abcdefghijklmnopqrst", runner.CONFIRMATION_PREFIX + ":abcdefghijklmnopqrst", "http://127.0.0.1:54321"),
])
def test_production_gate_rejects_mismatch(ref, flag, url):
    with pytest.raises(runner.GateError, match="gate not satisfied"):
        runner.validate_gate(ref, flag, url, "abcdefghijklmnopqrst")


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
    result = runner.exercise(create_client(local_url, keys["service_role"]), keys["anon"],
                             monkeypatch, record=False)
    assert result == {"result": "PASS", "cleanup": "PASS",
                      "count_delta": {table: 0 for table in runner.COUNT_TABLES}}
