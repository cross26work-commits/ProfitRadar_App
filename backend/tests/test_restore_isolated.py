"""Command orchestration substitutes only; no Docker/restore success claim."""
import json
from unittest.mock import Mock
import pytest
from scripts import restore_isolated as restore


def test_restore_requires_explicit_authority_before_docker(monkeypatch):
    command=Mock();monkeypatch.setattr(restore,"command",command)
    with pytest.raises(ValueError):restore.run()
    command.assert_not_called()


def setup(monkeypatch):
    monkeypatch.delenv("DOCKER_HOST",raising=False);monkeypatch.delenv("DOCKER_CONTEXT",raising=False)
    context=[{"Endpoints":{"docker":{"Host":"unix:///var/run/docker.sock"}}}]
    info=[{"Config":{"Labels":{"com.supabase.cli.project":restore.LABEL}},"State":{"Running":True},
           "NetworkSettings":{"Ports":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"54322"}]}}}]
    command=Mock(side_effect=[json.dumps(context),json.dumps(info),"","","","",""])
    monkeypatch.setattr(restore,"command",command)
    monkeypatch.setattr(restore,"fingerprint",Mock(return_value=("matching-metadata",12)))
    return command


def test_only_new_random_target_is_restored_source_is_unchanged(monkeypatch):
    command=setup(monkeypatch)
    result=restore.run(True,True)
    assert result["restore_verified"] and result["table_count"]==12
    restore_call=next(c.args[0] for c in command.call_args_list if "pg_restore" in c.args[0])
    assert restore_call[restore_call.index("-d")+1]==result["target_database"]
    assert result["target_database"].startswith("pr_restore_")
    assert "--single-transaction" in restore_call
    preparation=next(c.args[0] for c in command.call_args_list if "psql" in c.args[0])
    assert preparation[preparation.index("-d")+1]==result["target_database"]
    assert preparation[preparation.index("-U")+1]=="supabase_admin"
    assert "--clean" not in restore_call
    assert "dropdb" not in repr(command.call_args_list)


def test_mismatch_does_not_report_restore_success(monkeypatch):
    setup(monkeypatch)
    monkeypatch.setattr(restore,"fingerprint",Mock(side_effect=[("source",12),("different",12),("source",12)]))
    with pytest.raises(RuntimeError,match="verification failed"):restore.run(True,True)


def test_remote_docker_is_rejected(monkeypatch):
    command=setup(monkeypatch);monkeypatch.setenv("DOCKER_HOST","ssh://not-local.invalid")
    with pytest.raises(ValueError,match="overrides"):restore.run(True,True)
    command.assert_not_called()
