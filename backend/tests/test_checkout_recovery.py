from contextlib import nullcontext
from datetime import datetime,timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.api import billing as api


def setup(monkeypatch,status='trial',attempt=None):
    db=Mock();q=Mock();db.table.return_value=q
    for name in ('select','eq','upsert','update'):getattr(q,name).return_value=q
    q.execute.return_value=SimpleNamespace(data=[attempt] if attempt else [])
    monkeypatch.setattr(api,'get_supabase_client',lambda:db)
    monkeypatch.setattr(api,'company_lock',lambda *args:nullcontext())
    monkeypatch.setattr(api.billing,'status',lambda *args:{'status':status})
    monkeypatch.setenv('STRIPE_PRICE_ID','price_fixture');monkeypatch.setenv('FRONTEND_URL','http://localhost:3000')
    provider=Mock();monkeypatch.setattr(api.billing,'stripe_request',provider)
    return q,provider


def price():return {'active':True,'currency':'jpy','unit_amount':19800,'recurring':{'interval':'month','interval_count':1},'tax_behavior':'inclusive'}


@pytest.mark.parametrize('status',['active','past_due','unpaid','incomplete','paused'])
def test_existing_contract_cannot_create_second_subscription(monkeypatch,status):
    _,provider=setup(monkeypatch,status)
    with pytest.raises(HTTPException) as exc:api.checkout('a')
    assert exc.value.status_code==409;provider.assert_not_called()


def test_attempt_must_be_saved_before_checkout_provider_call(monkeypatch):
    _,provider=setup(monkeypatch);provider.return_value=price()
    with pytest.raises(HTTPException) as exc:api.checkout('a')
    assert exc.value.status_code==503
    provider.assert_called_once_with('GET','prices/price_fixture')


def test_unknown_checkout_reuses_durable_idempotency_key(monkeypatch):
    attempt={'attempt_id':'fixture-id','created_at':datetime.now(timezone.utc).isoformat(),'session_id':None}
    _,provider=setup(monkeypatch,attempt=attempt)
    provider.side_effect=[price(),HTTPException(503,'unknown'),price(),{'id':'cs_test','url':'https://checkout.stripe.com/test'}]
    with pytest.raises(HTTPException) as exc:api.checkout('a')
    assert exc.value.status_code==503
    assert api.checkout('a')['test_mode']
    writes=[c for c in provider.call_args_list if c.args[0]=='POST']
    assert len(writes)==2 and all(c.kwargs['idempotency_key']=='checkout-fixture-id' for c in writes)


def test_resubscribe_only_after_provider_confirms_old_contract_ended(monkeypatch):
    q,provider=setup(monkeypatch,status='canceled',attempt={'session_id':'cs_old'})
    q.execute.side_effect=[SimpleNamespace(data=[{'session_id':'cs_old'}]),SimpleNamespace(data=[{'saved':True}]),SimpleNamespace(data=[{'saved':True}])]
    provider.side_effect=[price(),{'status':'complete','client_reference_id':'a','subscription':'sub_old'},
                          {'status':'canceled','metadata':{'company_id':'a'}},{'id':'cs_new','url':'https://checkout.stripe.com/test'}]
    assert api.checkout('a')['url']=='https://checkout.stripe.com/test'
    assert provider.call_args.kwargs['idempotency_key'].startswith('checkout-')
