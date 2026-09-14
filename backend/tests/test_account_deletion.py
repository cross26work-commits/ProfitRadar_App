from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.services import account_deletion as deletion


def environment(monkeypatch, status="providers"):
    job={"id":"job","company_id":"a","user_id":"user-a","status":status,"gmail_done":False,"billing_done":False}
    db=Mock();q=Mock();db.table.return_value=q
    for method in ("select","eq","update"):getattr(q,method).return_value=q
    q.execute.return_value=SimpleNamespace(data=[{}])
    monkeypatch.setattr(deletion,"read_job",lambda *args:job)
    monkeypatch.setattr(deletion,"company_lock",lambda *args:nullcontext())
    gmail=Mock();monkeypatch.setattr(deletion,"disconnect",gmail)
    stripe=Mock(side_effect=AssertionError("no billing contract"));monkeypatch.setattr(deletion,"stripe_request",stripe)
    def rpc(name,params):
        def execute():
            if name=="purge_account_data":job["status"]="auth"
            if name=="complete_account_deletion":job["status"]="completed"
            return SimpleNamespace(data=None)
        return SimpleNamespace(execute=execute)
    db.rpc.side_effect=rpc
    return job,db,gmail,stripe


def test_full_deletion_then_idempotent_replay(monkeypatch):
    job,db,gmail,stripe=environment(monkeypatch)
    assert deletion.resume(db,job)["success"]
    assert deletion.resume(db,job)["success"]
    gmail.assert_called_once();db.auth.admin.delete_user.assert_called_once_with("user-a")
    stripe.assert_not_called()


def test_auth_failure_retries_only_auth_phase(monkeypatch):
    job,db,gmail,_=environment(monkeypatch)
    db.auth.admin.delete_user.side_effect=RuntimeError("private")
    with pytest.raises(HTTPException) as error:deletion.resume(db,job)
    assert error.value.status_code==503 and job["status"]=="auth"
    db.auth.admin.delete_user.side_effect=None
    assert deletion.resume(db,job)["success"]
    gmail.assert_called_once()
    assert sum(c.args[0]=="purge_account_data" for c in db.rpc.call_args_list)==1


def test_revoke_failure_preserves_all_data(monkeypatch):
    job,db,gmail,_=environment(monkeypatch)
    gmail.side_effect=RuntimeError("private")
    with pytest.raises(HTTPException):deletion.resume(db,job)
    assert job["status"]=="providers"
    db.rpc.assert_not_called();db.auth.admin.delete_user.assert_not_called()


def test_already_deleted_auth_is_only_specific_not_found(monkeypatch):
    job,db,gmail,_=environment(monkeypatch,"auth")
    error=RuntimeError("absent");error.code="user_not_found"
    db.auth.admin.delete_user.side_effect=error
    assert deletion.resume(db,job)["success"]
    gmail.assert_not_called()
