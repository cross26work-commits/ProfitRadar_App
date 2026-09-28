"""Grammar/authority checks only; actual DB scenarios live in validate_forward_local."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import json
import pytest
import pglast
from scripts import validate_forward_local as validation


def test_canonical_matches_independent_remote_capture_hash():
    validation.canonical_oracle_bytes()
    assert set(validation.canonical_capture_hashes().values()) == {validation.REMOTE_CANONICAL_LF_SHA256}


def test_authoritative_remote_policy_oracle():
    policies = validation.remote_policy_oracle()
    assert {p['policyname'] for p in policies} == {'companies_insert_own', 'companies_select_member_or_owner', 'profiles_select_own', 'profiles_update_own'}


def test_owner_contract_is_exact_in_transaction():
    source = validation.FORWARD_V2.read_text(encoding='utf-8')
    guard = source.split('DO $owner_contract$', 1)[1].split('END $owner_contract$;', 1)[0]
    for required in ("a.atttypid='pg_catalog.uuid'::regtype", "NOT a.attnotnull",
                     "a.attidentity=''", "a.attgenerated=''",
                     "pg_get_expr(d.adbin,d.adrelid)='auth.uid()'",
                     "IF NOT EXISTS", "FORWARD: prerequisite column/type mismatch"):
        assert required in guard
    assert 'ALTER COLUMN' not in guard


def test_global_sync_evidence_gate_not_tenant_purge():
    source = validation.FORWARD_V2.read_text(encoding='utf-8')
    gate = source.split('DO $global_sync_evidence$', 1)[1].split('END $global_sync_evidence$;', 1)[0]
    assert 'LOCK TABLE public.gmail_sync_runs IN SHARE MODE;' in gate
    assert 'global sync rows require review' in gate
    assert 'FULL JOIN actual' in gate
    assert "('gmail_sync_runs','company_id'," not in source
    for column in ('company_count', 'success_count', 'failure_count', 'detected_reply_count', 'error_summary'):
        assert column in gate
    for name in ('request_account_deletion', 'purge_account_data', 'complete_account_deletion'):
        function = source.split("create function public." + name + '(', 1)[1].split('$ddl$);', 1)[0]
        assert 'gmail_sync_runs' not in function
    assert "'gmail_company_sync_runs','operation_recovery_audit'" in source


def test_forward_legacy_scope_and_nullable_columns_are_explicit():
    source = validation.FORWARD_V2.read_text(encoding='utf-8')
    for table, column in [('companies', 'updated_at'), ('profiles', 'updated_at'), ('gmail_sync_runs', 'error_code'), ('gmail_sync_runs', 'detected_count')]:
        assert f"('{table}','{column}'," not in source
    assert 'DO $legacy_columns$' in source and 'legacy column contract mismatch' in source
    assert 'unknown legacy policy' in source and 'unexpected legacy grantee' in source
    assert 'inherited legacy MAINTAIN remains' in source
    assert 'ON ALL TABLES IN SCHEMA' not in source.upper()


def test_capture_mismatch_blocks_before_docker(monkeypatch):
    command = Mock()
    monkeypatch.setattr(validation, 'command', command)
    monkeypatch.setattr(validation, 'canonical_capture_hashes', lambda: {'docs': '0' * 64})
    with pytest.raises(ValueError, match='capture hash mismatch'):
        validation.run(True, v2=True)
    command.assert_not_called()


def test_preflight_is_parseable_readonly_sql():
    path = Path(__file__).resolve().parents[2] / "supabase/remote_schema_forward_preflight.sql"
    statements = pglast.parse_sql(path.read_text(encoding="utf-8"))
    assert statements
    assert all(type(statement.stmt).__name__ == "SelectStmt" for statement in statements)


def test_forward_utf8_japanese_literals_match_source_migrations():
    root = Path(__file__).resolve().parents[2] / "supabase/migrations"
    import re
    forward = (root / "202609140001_remote_schema_forward.sql").read_bytes().decode("utf-8", errors="strict")
    assert "\ufffd" not in forward
    assert "元メールを確認して返信要否を判断" in forward
    literals = set()
    for source in sorted(root.glob("20260910000[2-8]*.sql")):
        for literal in re.findall(r"'([^']*)'", source.read_text(encoding="utf-8")):
            if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", literal):
                literals.add(literal)
    assert literals
    assert all(literal in forward for literal in literals)


def test_v2_draft_is_utf8_parseable_and_blocks_before_persistent_changes():
    root = Path(__file__).resolve().parents[2] / "supabase/migrations"
    text = (root / "202609150001_remote_schema_forward_v2.sql").read_bytes().decode("utf-8", errors="strict")
    assert "\ufffd" not in text
    assert "元メールを確認して返信要否を判断" in text
    assert pglast.parse_sql(text)
    assert text.index("onboarding exact body/arguments mismatch") < text.index("ALTER FUNCTION public.onboard_user")


def test_v2_validator_default_blocks_without_database():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(Path(validation.__file__))], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Explicit local fixture approval" in result.stderr


def test_v2_pins_captured_bodies_without_replacing_canonical():
    import re
    root = Path(__file__).resolve().parents[2]
    evidence = (root / 'docs/remote_onboarding_functiondefs_20260915_exact.txt').read_text(encoding='utf-8')
    forward = (root / 'supabase/migrations/202609150001_remote_schema_forward_v2.sql').read_text(encoding='utf-8')
    bodies = re.findall(r'AS \$function\$([\s\S]*?)\$function\$;', evidence)
    assert len(bodies) == 2
    assert all(body in forward for body in bodies)
    preflight = (root / 'supabase/remote_schema_forward_preflight.sql').read_text(encoding='utf-8')
    assert bodies[1] == preflight.split('$canonical_body$')[1]
    assert bodies[1] == forward.split('$canonical_body$')[1]
    oracle = validation.canonical_oracle_bytes().replace(b'\r\n', b'\n').decode('utf-8')
    assert bodies[1] == oracle
    assert bodies[1].startswith('\n') and bodies[1].endswith('\n')
    assert 'ALTER FUNCTION public.create_company_and_profile' not in forward
    assert 'CREATE OR REPLACE FUNCTION public.onboard_user' not in forward
    assert 'FROM PUBLIC,anon,authenticated' in forward


def test_validation_refuses_implicit_authority_before_docker(monkeypatch):
    command = Mock()
    monkeypatch.setattr(validation, "command", command)
    with pytest.raises(ValueError, match="approval"):
        validation.validate_target(False)
    command.assert_not_called()


def test_validation_refuses_remote_context(monkeypatch):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    command = Mock(return_value=json.dumps([{"Endpoints": {"docker": {"Host": "ssh://example.invalid"}}}]))
    monkeypatch.setattr(validation, "command", command)
    with pytest.raises(ValueError, match="Local Docker"):
        validation.validate_target(True)
    assert command.call_count == 1


def test_sql_transport_error_cannot_pass_as_expected_authorization_failure(monkeypatch):
    monkeypatch.setattr(validation.subprocess, "run", Mock(return_value=SimpleNamespace(
        returncode=1, stderr="connection failed", stdout="")))
    with pytest.raises(RuntimeError, match="Expected migration guard"):
        validation.command(["synthetic"], expected_error="FORWARD: browser effective")


def test_validation_cannot_write_source_database():
    with pytest.raises(ValueError, match="newly generated"):
        validation.sql("postgres", "select 1")
