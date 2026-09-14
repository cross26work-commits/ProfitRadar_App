from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from app.core.token_vault import encrypt, decrypt
from app.services import gmail_credentials


class DB:
    def __init__(self, matched=True):
        self.filters, self.payload, self.matched = {}, None, matched
    def table(self, name):
        assert name == "gmail_connections"
        return self
    def update(self, payload):
        self.payload = payload
        return self
    def eq(self, key, value):
        self.filters[key] = value
        return self
    def execute(self):
        return SimpleNamespace(data=[{"id": "connection"}] if self.matched else [])


@pytest.fixture
def row(monkeypatch):
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEYS", Fernet.generate_key().decode())
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fixture-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fixture-secret")
    return {"id": "connection", "token_json": encrypt("a", {"token": "old", "refresh_token": "refresh", "client_id": "fixture-client", "token_uri": "https://oauth2.googleapis.com/token", "expiry": "2020-01-01T00:00:00"})}


def test_refresh_encrypted_persistence_and_cas(monkeypatch, row):
    def refresh(self, request):
        self.token = "new"
        self.expiry = datetime.now() + timedelta(hours=1)
    monkeypatch.setattr(gmail_credentials.Credentials, "refresh", refresh)
    db = DB()
    credentials = gmail_credentials.credentials_for_connection(db, "a", row)
    assert credentials.token == "new"
    assert decrypt("a", db.payload["token_json"])["token"] == "new"
    assert db.filters["company_id"] == "a" and db.filters["status"] == "connected"
    assert "token_json" in db.filters
    assert set(db.payload["token_json"]) == {"version", "ciphertext"}
    with pytest.raises(HTTPException) as error:
        gmail_credentials.credentials_for_connection(DB(False), "a", row)
    assert error.value.status_code == 409


def test_refresh_failure_redacted_without_write(monkeypatch, row):
    def fail(self, request):
        raise RuntimeError("private-provider-body")
    monkeypatch.setattr(gmail_credentials.Credentials, "refresh", fail)
    db = DB()
    with pytest.raises(HTTPException) as error:
        gmail_credentials.credentials_for_connection(db, "a", row)
    assert error.value.status_code == 503 and "private" not in error.value.detail
    assert db.payload is None
