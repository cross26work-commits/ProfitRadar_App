"""All keys/signatures/providers below are synthetic substitutes; no HTTP or real keys."""
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.core.billing_mode import configured_mode, require_database_mode
from app.services import billing


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    for name in ("STRIPE_MODE","BILLING_LIVE_APPROVED","BILLING_LIVE_APPROVAL_REF","STRIPE_SECRET_KEY"):
        monkeypatch.delenv(name,raising=False)
    monkeypatch.setenv("APP_ENV","test")
    forbidden=Mock(side_effect=AssertionError("Network forbidden in gate tests"))
    monkeypatch.setattr(billing.requests,"request",forbidden)


def approved(monkeypatch):
    for key,value in {"APP_ENV":"production","STRIPE_MODE":"live","BILLING_LIVE_APPROVED":"true",
                      "BILLING_LIVE_APPROVAL_REF":"fixture-ticket","FRONTEND_URL":"https://fixture.invalid"}.items():
        monkeypatch.setenv(key,value)


def database(mode="test",ref=None):
    db=Mock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value=SimpleNamespace(data=[{"mode":mode,"approval_ref":ref}])
    return db


def test_default_is_test_and_never_calls_provider():
    assert configured_mode()=="test"
    assert require_database_mode(database())=="test"
    billing.requests.request.assert_not_called()


@pytest.mark.parametrize("key,value",[("APP_ENV","test"),("APP_ENV","staging"),("BILLING_LIVE_APPROVED","false"),
                                      ("BILLING_LIVE_APPROVAL_REF",""),("FRONTEND_URL","http://fixture.invalid"),
                                      ("FRONTEND_URL","https://user@fixture.invalid"),("STRIPE_MODE","typo")])
def test_live_gate_rejects_missing_approval_before_network(monkeypatch,key,value):
    approved(monkeypatch);monkeypatch.setenv(key,value)
    with pytest.raises(HTTPException) as error:configured_mode()
    assert error.value.status_code==503
    billing.requests.request.assert_not_called()


def test_live_requires_matching_db_and_approval(monkeypatch):
    approved(monkeypatch)
    for db in (database(),database("live","other-ticket")):
        with pytest.raises(HTTPException) as error:require_database_mode(db)
        assert error.value.status_code==503
    assert require_database_mode(database("live","fixture-ticket"))=="live"


def test_wrong_key_mode_rejected_without_provider(monkeypatch):
    approved(monkeypatch);monkeypatch.setenv("STRIPE_SECRET_KEY","sk_test_synthetic_not_a_real_key")
    with pytest.raises(HTTPException) as error:billing.stripe_request("POST","checkout/sessions")
    assert error.value.status_code==503
    billing.requests.request.assert_not_called()


def test_signed_live_event_only_after_approval_and_no_mode_mix(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET","synthetic-signature-only")
    stamp=str(int(time.time()))
    def event(live):
        raw=json.dumps({"livemode":live,"id":"fixture"}).encode()
        signature=hmac.new(b"synthetic-signature-only",stamp.encode()+b"."+raw,hashlib.sha256).hexdigest()
        return raw,f"t={stamp},v1={signature}"
    with pytest.raises(HTTPException) as error:billing.verify_event(*event(True))
    assert error.value.status_code==400
    approved(monkeypatch)
    assert billing.verify_event(*event(True))["id"]=="fixture"
    with pytest.raises(HTTPException) as error:billing.verify_event(*event(False))
    assert error.value.status_code==400
    billing.requests.request.assert_not_called()


def test_test_provider_response_mode_and_redirect_guard(monkeypatch):
    from app.core import supabase_client
    monkeypatch.setenv("STRIPE_SECRET_KEY","sk_test_synthetic_not_a_real_key")
    monkeypatch.setattr(supabase_client,"get_supabase_client",lambda:database())
    request=Mock(return_value=SimpleNamespace(status_code=200,json=lambda:{"id":"fixture","livemode":False}))
    monkeypatch.setattr(billing.requests,"request",request)
    assert billing.stripe_request("GET","prices/fixture")["id"]=="fixture"
    assert request.call_args.kwargs["allow_redirects"] is False
    for payload in ({"livemode":True},{"id":"missing-mode"}):
        request.return_value.json=lambda:payload
        with pytest.raises(HTTPException) as error:billing.stripe_request("GET","prices/fixture")
        assert error.value.status_code==503


def test_stale_test_confirmation_cannot_create_live_checkout(monkeypatch):
    from app.api import billing as api
    approved(monkeypatch)
    db=Mock(side_effect=AssertionError("Must reject before DB or provider"))
    monkeypatch.setattr(api,"get_supabase_client",db)
    for payload in (None,api.CheckoutIntent(expected_mode="test")):
        with pytest.raises(HTTPException) as error:api.checkout("fixture",payload)
        assert error.value.status_code==409
    db.assert_not_called()
    billing.requests.request.assert_not_called()
