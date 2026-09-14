"""Grammar/authority checks only; actual DB scenarios live in validate_forward_local."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import json
import pytest
import pglast
from scripts import validate_forward_local as validation


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
