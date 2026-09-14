import hashlib,hmac,json,time
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.services import billing


@pytest.mark.parametrize("elapsed,allowed", [(13,True),(15,False)])
def test_trial_deadline_without_stripe(elapsed,allowed,monkeypatch):
    db=Mock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value=SimpleNamespace(data=[{"mode":"test","approval_ref":None}])
    end=datetime.now(timezone.utc)+timedelta(days=14-elapsed)
    db.rpc.side_effect=lambda name,args:SimpleNamespace(execute=lambda:SimpleNamespace(data=True if name=="company_is_active" else [{"status":"trial","trial_ends_at":end.isoformat()}]))
    provider=Mock(side_effect=AssertionError("Trial must not charge"))
    monkeypatch.setattr(billing,"stripe_request",provider)
    assert billing.status(db,"a")["allowed"] is allowed
    if not allowed:
        with pytest.raises(HTTPException) as exc: billing.require_use(db,"a")
        assert exc.value.status_code==402
    provider.assert_not_called()


def signed(raw,stamp):
    signature=hmac.new(b"fixture",str(stamp).encode()+b"."+raw,hashlib.sha256).hexdigest()
    return f"t={stamp},v1={signature}"


def test_webhook_signature_timestamp_live_guard(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET","fixture")
    stamp=int(time.time())
    raw=json.dumps({"livemode":False,"id":"fixture"}).encode()
    assert billing.verify_event(raw,signed(raw,stamp))["id"]=="fixture"
    for payload,header in [(raw+b" ",signed(raw,stamp)),(raw,signed(raw,stamp-301)),(b'{"livemode":true}',signed(b'{"livemode":true}',stamp))]:
        with pytest.raises(HTTPException) as exc: billing.verify_event(payload,header)
        assert exc.value.status_code==400


def test_live_api_key_denied(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY","sk_live_synthetic")
    request=Mock()
    monkeypatch.setattr(billing.requests,"request",request)
    with pytest.raises(HTTPException): billing.stripe_request("POST","checkout/sessions")
    request.assert_not_called()
