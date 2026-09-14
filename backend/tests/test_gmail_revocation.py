from types import SimpleNamespace
import pytest
import requests
from unittest.mock import Mock
from fastapi import HTTPException
from app.services import gmail_revocation


def test_revoke_posts_body_not_url(monkeypatch):
    def post(url, **kwargs):
        assert url == "https://oauth2.googleapis.com/revoke"
        assert kwargs["data"] == {"token": "synthetic"}
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == 10
        return SimpleNamespace(status_code=200)
    monkeypatch.setattr(gmail_revocation.requests, "post", post)
    gmail_revocation.revoke("synthetic")


@pytest.mark.parametrize("status", [302,400,429,500])
def test_revoke_non_success_not_treated_as_deleted(monkeypatch, status):
    monkeypatch.setattr(gmail_revocation.requests, "post", lambda *a, **k: SimpleNamespace(status_code=status))
    with pytest.raises(HTTPException) as error:
        gmail_revocation.revoke("synthetic")
    assert error.value.status_code == 503


def test_revoke_network_failure_redacted(monkeypatch):
    def fail(*a, **k):
        raise requests.Timeout("private")
    monkeypatch.setattr(gmail_revocation.requests, "post", fail)
    with pytest.raises(HTTPException) as error:
        gmail_revocation.revoke("synthetic")
    assert error.value.detail == "Gmail disconnect pending; retry later"


def test_retry_after_db_delete_failure_does_not_revoke_again(monkeypatch):
    row={"id":"connection","token_json":{},"status":"revoked"}
    db=Mock();q=Mock();db.table.return_value=q
    q.select.return_value=q;q.eq.return_value=q;q.delete.return_value=q
    q.execute.return_value=SimpleNamespace(data=[row])
    provider=Mock(side_effect=AssertionError("already revoked"))
    monkeypatch.setattr(gmail_revocation,"revoke",provider)
    monkeypatch.setattr(gmail_revocation,"decrypt",Mock(side_effect=AssertionError("no ciphertext should remain")))
    assert gmail_revocation.disconnect(db,"a")["disconnected"] is True
    provider.assert_not_called();q.update.assert_not_called();q.delete.assert_called_once()


def test_success_erases_credentials_before_local_delete(monkeypatch):
    db=Mock();q=Mock();db.table.return_value=q
    q.select.return_value=q;q.eq.return_value=q;q.update.return_value=q;q.delete.return_value=q
    q.execute.return_value=SimpleNamespace(data=[{"id":"connection","status":"connected","token_json":{}}])
    monkeypatch.setattr(gmail_revocation,"decrypt",lambda *args:{"refresh_token":"synthetic"})
    provider=Mock();monkeypatch.setattr(gmail_revocation,"revoke",provider)
    gmail_revocation.disconnect(db,"a")
    assert q.update.call_args_list[-1].args[0]=={"status":"revoked","token_json":{}}
    provider.assert_called_once()


@pytest.mark.parametrize("failed_write", [1, 2, 3])
def test_zero_row_write_never_reports_disconnected(monkeypatch, failed_write):
    db=Mock();q=Mock();db.table.return_value=q
    q.select.return_value=q;q.eq.return_value=q;q.update.return_value=q;q.delete.return_value=q
    row={"id":"connection","status":"connected","token_json":{}}
    q.execute.side_effect=[SimpleNamespace(data=[row])] + [
        SimpleNamespace(data=[] if i==failed_write else [row]) for i in range(1,4)]
    monkeypatch.setattr(gmail_revocation,"decrypt",lambda *args:{"refresh_token":"synthetic"})
    provider=Mock();monkeypatch.setattr(gmail_revocation,"revoke",provider)
    with pytest.raises(HTTPException) as error:
        gmail_revocation.disconnect(db,"a")
    assert error.value.status_code==409
    assert provider.call_count == (0 if failed_write==1 else 1)
