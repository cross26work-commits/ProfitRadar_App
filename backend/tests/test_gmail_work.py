from unittest.mock import Mock
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from app.services.gmail_work import company_lock,batch,retry_due
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


def test_batch_deferred_company_does_not_block_others():
    visited=[]
    def work(cid):
        visited.append(cid)
        return {"deferred":True} if cid=="b" else {"count":0}
    result=batch(["a","b","c"],work)
    assert visited==["a","b","c"]
    assert result["succeeded"]==2 and result["deferred"]==1 and result["failed"]==0


def test_retry_backoff_is_company_local_and_does_not_unlock_running_work():
    now=datetime(2026,9,18,0,0,tzinfo=timezone.utc)
    def failed(minutes):
        return {"status":"failed","started_at":(now-timedelta(minutes=minutes+1)).isoformat(),
                "finished_at":(now-timedelta(minutes=minutes)).isoformat()}
    assert retry_due([],now)
    assert not retry_due([failed(4)],now)
    assert retry_due([failed(5)],now)
    assert not retry_due([failed(9),failed(30)],now)
    assert retry_due([failed(10),failed(30)],now)
    assert not retry_due([{"status":"running","started_at":now.isoformat()}],now)
    assert not retry_due([{"status":"failed","finished_at":"invalid"}],now)


def test_scheduler_auth_denied_before_database(monkeypatch):
    monkeypatch.setenv("GMAIL_SCHEDULER_SECRET","synthetic")
    db=Mock(side_effect=AssertionError("must not access DB"))
    monkeypatch.setattr(gmail,"get_supabase_client",db)
    for provided in (None,"wrong"):
        with pytest.raises(HTTPException) as error:
            gmail.scheduled_sync(provided)
        assert error.value.status_code==401
    db.assert_not_called()


def test_scheduler_defers_only_failed_company(monkeypatch):
    monkeypatch.setenv("GMAIL_SCHEDULER_SECRET","synthetic")
    now=datetime.now(timezone.utc)
    def query(table):
        q=Mock()
        for method in ("select","order","limit"):
            getattr(q,method).return_value=q
        company=[None]
        def eq(key,value):
            if key=="company_id": company[0]=value
            return q
        q.eq.side_effect=eq
        q.execute.side_effect=lambda:SimpleNamespace(data=(
            [{"company_id":"a"},{"company_id":"b"}] if table=="gmail_connections" else
            [{"status":"failed","started_at":now.isoformat(),"finished_at":now.isoformat()}] if company[0]=="a" else []))
        return q
    db=Mock();db.table.side_effect=query
    monkeypatch.setattr(gmail,"get_supabase_client",lambda:db)
    sync=Mock(return_value={"count":0})
    monkeypatch.setattr(gmail.gmail_work,"sync_company",sync)
    result=gmail.scheduled_sync("synthetic")
    assert result["processed"]==2 and result["deferred"]==1 and result["succeeded"]==1
    assert sync.call_count==1 and sync.call_args.args[1]=="b"
