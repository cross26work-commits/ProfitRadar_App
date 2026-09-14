import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from app.core.token_vault import encrypt, decrypt


def test_roundtrip_tenant_binding_and_tamper(monkeypatch):
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEYS", Fernet.generate_key().decode())
    envelope = encrypt("company-a", {"token": "synthetic-token"})
    assert "synthetic-token" not in str(envelope)
    assert decrypt("company-a", envelope) == {"token": "synthetic-token"}
    with pytest.raises(HTTPException) as error:
        decrypt("company-b", envelope)
    assert error.value.status_code == 503
    with pytest.raises(HTTPException):
        decrypt("company-a", {"version": 1, "ciphertext": "invalid"})


def test_missing_key_and_plaintext_fail_closed(monkeypatch):
    monkeypatch.delenv("GMAIL_TOKEN_ENCRYPTION_KEYS", raising=False)
    with pytest.raises(HTTPException) as error:
        encrypt("a", {})
    assert error.value.status_code == 503
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEYS", Fernet.generate_key().decode())
    with pytest.raises(HTTPException):
        decrypt("a", {"token": "legacy"})


def test_key_rotation(monkeypatch):
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEYS", old)
    envelope = encrypt("a", {"token": "synthetic"})
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEYS", new + "," + old)
    assert decrypt("a", envelope)["token"] == "synthetic"
