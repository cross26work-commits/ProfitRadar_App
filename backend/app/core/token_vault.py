"""Versioned authenticated encryption, bound to the connection's tenant.

Comma-separated Fernet keys: first encrypts, remaining keys allow key rotation.
Key material belongs in the backend secret store, never in the database.
"""
import json
import os
from cryptography.fernet import Fernet, MultiFernet
from fastapi import HTTPException


def _cipher():
    try:
        keys = [value.strip() for value in os.environ["GMAIL_TOKEN_ENCRYPTION_KEYS"].split(",") if value.strip()]
        if not keys:
            raise ValueError()
        return MultiFernet([Fernet(key.encode("ascii")) for key in keys])
    except (KeyError, ValueError, UnicodeError):
        raise HTTPException(503, "Gmail credential storage unavailable") from None


def encrypt(company_id, token):
    plaintext = json.dumps({"company_id": str(company_id), "token": token}).encode("utf-8")
    return {"version": 1, "ciphertext": _cipher().encrypt(plaintext).decode("ascii")}


def decrypt(company_id, envelope):
    cipher = _cipher()
    try:
        if envelope.get("version") != 1:
            raise ValueError()
        result = json.loads(cipher.decrypt(envelope["ciphertext"].encode("ascii")))
        if result["company_id"] != str(company_id) or not isinstance(result["token"], dict):
            raise ValueError()
        return result["token"]
    except Exception:
        # No silent legacy plaintext fallback; migrate or reconnect before enabling.
        raise HTTPException(503, "Gmail credential requires secure migration or reconnection") from None
