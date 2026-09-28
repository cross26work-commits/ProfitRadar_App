"""Offline checks for the production backup entry point (no remote calls)."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "backup_production_restore.py"
SPEC = importlib.util.spec_from_file_location("backup_production_restore", SCRIPT)
backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup)


def test_source_identity_is_pinned_to_approved_project():
    backup.source_identity(f"db.{backup.PROJECT_ID}.supabase.co", "postgres", 5432, "postgres")
    backup.source_identity("aws-0-ap-northeast-1.pooler.supabase.com",
                           f"postgres.{backup.PROJECT_ID}", 5432, "postgres")
    for host, user, port, dbname in (
        ("db.other.supabase.co", "postgres", 5432, "postgres"),
        (f"db.{backup.PROJECT_ID}.supabase.co", "postgres", 5433, "postgres"),
        ("aws-0-ap-northeast-1.pooler.supabase.com", "postgres.other", 5432, "postgres"),
        (f"db.{backup.PROJECT_ID}.supabase.co", "postgres", 5432, "template1"),
    ):
        with pytest.raises(backup.BackupError, match="approved project identity"):
            backup.source_identity(host, user, port, dbname)


def test_no_remote_mutation_or_password_argument():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "exec pg_dump -w -Fc --blobs" in source
    assert "--single-transaction" in source
    assert "--exit-on-error" in source
    assert "password + \"\\n\"" in source
    assert "PGPASSWORD=" not in source
    assert "supabase db push" not in source
