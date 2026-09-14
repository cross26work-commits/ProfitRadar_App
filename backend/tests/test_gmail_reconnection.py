import pytest
from fastapi import HTTPException
from app.services import gmail_reconnection as service


def test_missing_refresh_reuses_only_same_active_account(monkeypatch):
    monkeypatch.setattr(service,"decrypt",lambda *args:{"client_id":"client","refresh_token":"synthetic"})
    row={"status":"connected","email":"a@example.invalid","token_json":{}}
    result=service.merge_refresh("company","a@example.invalid",{"client_id":"client"},row)
    assert result["refresh_token"]=="synthetic"


@pytest.mark.parametrize("email,status,client",[("b@example.invalid","connected","client"),("a@example.invalid","revocation_pending","client"),("a@example.invalid","connected","other")])
def test_reconnect_does_not_cross_identity_or_revocation(monkeypatch,email,status,client):
    monkeypatch.setattr(service,"decrypt",lambda *args:{"client_id":client,"refresh_token":"synthetic"})
    with pytest.raises(HTTPException) as exc:
        service.merge_refresh("company","a@example.invalid",{"client_id":"client"},{"email":email,"status":status,"token_json":{}})
    assert exc.value.status_code==409
