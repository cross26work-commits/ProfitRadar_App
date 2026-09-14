from contextlib import nullcontext
from unittest.mock import Mock
import json,time,hashlib,hmac
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import billing as api


def test_out_of_order_event_uses_current_provider_state(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET","synthetic")
    db=Mock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value=type("R",(),{"data":[{"stripe_subscription_id":"sub_test"}]})()
    monkeypatch.setattr(api,"get_supabase_client",lambda:db)
    monkeypatch.setattr(api,"company_lock",lambda *args:nullcontext())
    provider=Mock(return_value={"status":"canceled","metadata":{"company_id":"a"},"current_period_end":1000})
    monkeypatch.setattr(api.billing,"stripe_request",provider)
    app=FastAPI();app.include_router(api.router);client=TestClient(app)
    raw=json.dumps({"id":"old-event","livemode":False,"type":"customer.subscription.updated","data":{"object":{"id":"sub_test","status":"active","metadata":{"company_id":"a"}}}}).encode()
    stamp=str(int(time.time())); signature=hmac.new(b"synthetic",stamp.encode()+b"."+raw,hashlib.sha256).hexdigest()
    response=client.post("/billing/webhook",content=raw,headers={"stripe-signature":f"t={stamp},v1={signature}"})
    assert response.status_code==200
    assert db.rpc.call_args.args[1]["p_status"]=="canceled"
    provider.assert_called_once_with("GET","subscriptions/sub_test")


def test_old_subscription_cannot_replace_new_checkout(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET","synthetic")
    db=Mock()
    def table(name):
        q=Mock();q.select.return_value=q;q.eq.return_value=q
        q.execute.return_value=SimpleNamespace(data=[{"stripe_subscription_id":"sub_new"}] if name=="company_billing" else [{"session_id":"cs_new"}])
        return q
    db.table.side_effect=table
    monkeypatch.setattr(api,"get_supabase_client",lambda:db)
    monkeypatch.setattr(api,"company_lock",lambda *args:nullcontext())
    provider=Mock(side_effect=[{"status":"canceled","metadata":{"company_id":"a"}}, {"status":"complete","client_reference_id":"a","subscription":"sub_new"}])
    monkeypatch.setattr(api.billing,"stripe_request",provider)
    app=FastAPI();app.include_router(api.router)
    raw=json.dumps({"id":"old-event","livemode":False,"type":"customer.subscription.deleted","data":{"object":{"id":"sub_old","metadata":{"company_id":"a"}}}}).encode()
    stamp=str(int(time.time()));signature=hmac.new(b"synthetic",stamp.encode()+b"."+raw,hashlib.sha256).hexdigest()
    response=TestClient(app).post("/billing/webhook",content=raw,headers={"stripe-signature":f"t={stamp},v1={signature}"})
    assert response.status_code==200 and response.json()["ignored"] is True
    db.rpc.assert_not_called()
