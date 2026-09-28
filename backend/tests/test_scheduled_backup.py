from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import scheduled_backup


def values(monkeypatch, tmp_path):
    identity = tmp_path / "identity.txt"
    identity.write_text("fixture", encoding="utf-8")
    for name, value in {
        "APP_ENV": "test", "PGHOST": "127.0.0.1", "PGPORT": "54322",
        "PGUSER": "postgres", "PGDATABASE": "postgres", "PGPASSWORD": "fixture",
        "BACKUP_DIR": str(tmp_path / "backup"),
        "BACKUP_AGE_RECIPIENT": "age1" + "q" * 30,
        "BACKUP_AGE_IDENTITY_FILE": str(identity), "BACKUP_RETENTION_DAYS": "30",
    }.items(): monkeypatch.setenv(name, value)
    monkeypatch.setattr(scheduled_backup.shutil, "which", lambda name: f"/bin/{name}")


def test_backup_configuration_is_explicit_and_outside_repo(monkeypatch, tmp_path):
    values(monkeypatch, tmp_path)
    target, identity, retention = scheduled_backup.configuration(repo=tmp_path / "repo")
    assert target == (tmp_path / "backup").resolve() and identity.is_file() and retention == 30


def test_production_backup_rejects_loopback_or_unverified_tls(monkeypatch, tmp_path):
    values(monkeypatch, tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(scheduled_backup.BackupError, match="TLS"):
        scheduled_backup.configuration(repo=tmp_path / "repo")
    monkeypatch.setenv("PGHOST", "db.example.invalid")
    monkeypatch.setenv("PGSSLMODE", "require")
    with pytest.raises(scheduled_backup.BackupError, match="TLS"):
        scheduled_backup.configuration(repo=tmp_path / "repo")


def test_backup_configuration_errors_do_not_expose_secret(monkeypatch, tmp_path):
    values(monkeypatch, tmp_path)
    monkeypatch.setenv("PGPASSWORD", "secret-value")
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "invalid")
    with pytest.raises(scheduled_backup.BackupError) as error:
        scheduled_backup.configuration(repo=tmp_path / "repo")
    assert "secret-value" not in str(error.value)
