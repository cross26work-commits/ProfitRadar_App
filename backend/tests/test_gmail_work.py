from unittest.mock import Mock
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services.gmail_work import company_lock,batch
from app.api import gmail


def test_lock_contention_prevents_work():
    db=Mock()
    db.rpc.return_value.execute.return_value=SimpleNamespace(data=False)
    with pytest.raises(HTTPException) as error:
        with company_lock(db,"a","send"):
            pytest.fail("Lock not acquired")
    assert error.value.status_code==409
    assert db.rpc.call_count==1


def test_release_on_worker_failure():
    db=Mock()
    db.rpc.return_value.execute.return_value=SimpleNamespace(data=True)
    with pytest.raises(ValueError):
        with company_lock(db,"a","sync"):
            raise ValueError()
    assert db.rpc.call_args.args[0]=="release_gmail_work"


def test_batch_failure_isolation():
    visited=[]
    def work(cid):
        visited.append(cid)
        if cid=="b": raise RuntimeError("private")
    result=batch(["a","b","c"],work)
    assert visited==["a","b","c"]
    assert result["succeeded"]==2 and result["failed"]==1
    assert result["errors"]==[{"company_id":"b","code":"SYNC_FAILED"}]


def test_scheduler_auth_denied_before_database(monkeypatch):
    monkeypatch.setenv("GMAIL_SCHEDULER_SECRET","synthetic")
    db=Mock(side_effect=AssertionError("must not access DB"))
    monkeypatch.setattr(gmail,"get_supabase_client",db)
    for provided in (None,"wrong"):
        with pytest.raises(HTTPException) as error:
            gmail.scheduled_sync(provided)
        assert error.value.status_code==401
    db.assert_not_called()
