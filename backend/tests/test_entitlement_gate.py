from unittest.mock import Mock
import pytest
from fastapi import FastAPI,Depends,HTTPException
from fastapi.testclient import TestClient
from app.core import entitlements as gate


@pytest.mark.parametrize("path",["/reply/event/draft","/profit-events/event/actual-profit","/revenue/analyze","/new-business-write"])
def test_expired_contract_blocks_all_business_writes_before_handler(monkeypatch,path):
    monkeypatch.setattr(gate,"get_current_user",lambda _: {"sub":"a"})
    monkeypatch.setattr(gate,"get_current_company_id",lambda _:"company-a")
    monkeypatch.setattr(gate,"get_supabase_client",lambda:None)
    reject=Mock(side_effect=HTTPException(402,"expired"));monkeypatch.setattr(gate,"require_use",reject)
    app=FastAPI(dependencies=[Depends(gate.enforce_entitlements)])
    handler=Mock()
    @app.post(path)
    def write():handler();return {}
    assert TestClient(app).post(path).status_code==402
    handler.assert_not_called()


def test_no_prefix_wide_lifecycle_bypass():
    for path in ("/auth/unreviewed-write","/billing/unreviewed-write","/account/new-write"):
        assert not gate.lifecycle_path(path)


def test_all_registered_business_mutations_reject_expiry(monkeypatch):
    import re
    monkeypatch.setenv("APP_ENV","test")
    from app.main import app
    monkeypatch.setattr(gate,"get_current_user",lambda _: {"sub":"fixture"})
    monkeypatch.setattr(gate,"get_current_company_id",lambda _:"fixture")
    monkeypatch.setattr(gate,"get_supabase_client",lambda:None)
    monkeypatch.setattr(gate,"require_use",Mock(side_effect=HTTPException(402,"expired")))
    client=TestClient(app)
    tested=[]
    for route_path,operations in app.openapi()["paths"].items():
        for method in set(operations) & {"post","put","patch","delete"}:
            path=re.sub(r"\{[^}]+\}","00000000-0000-4000-8000-000000000001",route_path)
            if gate.lifecycle_path(path):continue
            response=client.request(method,path,json={})
            assert response.status_code==402,(method,route_path,response.status_code)
            assert response.json().get("code")=="HTTP_402"
            tested.append((method,route_path))
    assert len(tested)>=10
