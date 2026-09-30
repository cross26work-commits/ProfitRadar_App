from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import support
from app.core.admin_auth import require_support_admin

def test_contact_create_and_legal_classification(monkeypatch):
    db=Mock(); db.rpc.return_value.execute.return_value=SimpleNamespace(data=[{"public_request_id":"PR-20260929-ABCDEF123456","created_at":"2026-09-29T00:00:00Z"}])
    monkeypatch.setattr(support,"get_supabase_client",lambda:db);monkeypatch.setenv("APP_ENV","test")
    app=FastAPI();app.include_router(support.public_router);client=TestClient(app)
    payload={"name":"担当者","email":"OWNER@EXAMPLE.JP","company_name":"法人A","category":"commercial_disclosure","subject":"開示請求","body":"事業者情報の開示を請求します。","website":"","form_started_at":(datetime.now(timezone.utc)-timedelta(seconds=3)).isoformat()}
    response=client.post("/support/contact",json=payload,headers={"X-Contact-Intent":"public-form-v1"})
    assert response.status_code==201 and response.json()["request_id"].startswith("PR-")
    args=db.rpc.call_args.args[1];assert args["p_category"]=="commercial_disclosure" and args["p_requester_email"]=="owner@example.jp"
    assert len(args["p_abuse_key"])==64

@pytest.mark.parametrize("change",[{"website":"spam"},{"body":"short"},{"category":"not-approved"}])
def test_contact_validation_and_spam_rejected_before_db(monkeypatch,change):
    db=Mock();monkeypatch.setattr(support,"get_supabase_client",lambda:db);monkeypatch.setenv("APP_ENV","test")
    app=FastAPI();app.include_router(support.public_router)
    payload={"name":"担当者","email":"a@example.jp","category":"general","subject":"問い合わせ","body":"問い合わせ本文は十分な長さです。","website":"","form_started_at":(datetime.now(timezone.utc)-timedelta(seconds=3)).isoformat()};payload.update(change)
    assert TestClient(app).post("/support/contact",json=payload,headers={"X-Contact-Intent":"public-form-v1"}).status_code==422
    db.rpc.assert_not_called()

def test_normal_user_cannot_enumerate_admin_records(monkeypatch):
    db=Mock();monkeypatch.setattr(support,"get_supabase_client",lambda:db)
    app=FastAPI();app.include_router(support.admin_router)
    response=TestClient(app).get("/admin/support",headers={"Authorization":"Bearer invalid"})
    assert response.status_code in {401,403};db.table.assert_not_called()

def test_admin_list_excludes_abuse_key_and_reply_is_idempotent(monkeypatch):
    actor=str(uuid4());request_id=uuid4();db=Mock()
    row={"id":str(request_id),"public_request_id":"PR-20260929-ABCDEF123456","requester_email":"fixed@example.jp","subject":"help","abuse_key":"secret-hash"}
    query=Mock();query.select.return_value=query;query.order.return_value=query;query.limit.return_value=query;query.execute.return_value=SimpleNamespace(data=[row]);db.table.return_value=query
    db.rpc.return_value.execute.return_value=SimpleNamespace(data=[{"message_id":str(uuid4()),"created":False,"recipient_email":"fixed@example.jp","delivery_status":"sent","thread_reference":None}])
    monkeypatch.setattr(support,"get_supabase_client",lambda:db)
    app=FastAPI();app.dependency_overrides[require_support_admin]=lambda:actor;app.include_router(support.admin_router);client=TestClient(app)
    listed=client.get("/admin/support").json()["requests"][0];assert "abuse_key" not in listed
    response=client.post(f"/admin/support/{request_id}/replies",json={"subject":"回答","body":"回答本文","idempotency_key":str(uuid4())})
    assert response.status_code==200 and response.json()["duplicate"] is True

def test_provider_failure_is_unknown_and_not_retried(monkeypatch):
    actor=str(uuid4());request_id=uuid4();message_id=str(uuid4());db=Mock();calls=[]
    def rpc(name,args):
        calls.append(name);result=[{"message_id":message_id,"created":True,"recipient_email":"fixed@example.jp","delivery_status":"sending","thread_reference":None}] if name=="reserve_support_reply" else True
        return SimpleNamespace(execute=lambda:SimpleNamespace(data=result))
    db.rpc.side_effect=rpc;monkeypatch.setattr(support,"get_supabase_client",lambda:db);monkeypatch.setattr(support,"send_plain_text",Mock(side_effect=RuntimeError()))
    app=FastAPI();app.dependency_overrides[require_support_admin]=lambda:actor;app.include_router(support.admin_router)
    response=TestClient(app).post(f"/admin/support/{request_id}/replies",json={"subject":"回答","body":"本文","idempotency_key":str(uuid4())})
    assert response.status_code==503 and calls==["reserve_support_reply","finalize_support_reply"]
    assert db.rpc.call_args.args[1]["p_status"]=="unknown"
