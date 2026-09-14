"""Single backend-only decrypt/refresh path; never return credentials to clients."""
import json
import os
from datetime import datetime, timezone
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app.core.token_vault import encrypt, decrypt


def credentials_for_connection(db, company_id, row):
    data = decrypt(company_id, row.get("token_json") or {})
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret or data.get("client_id") != client_id:
        raise HTTPException(503, "Gmail credentials require reconnection")
    if data.get("token_uri") != "https://oauth2.googleapis.com/token":
        raise HTTPException(503, "Gmail credentials require reconnection")
    try:
        expiry = datetime.fromisoformat(data["expiry"]) if data.get("expiry") else datetime.now(timezone.utc)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        # google-auth uses naive UTC expiration timestamps.
        expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
        credentials = Credentials(token=data.get("token"), refresh_token=data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token", client_id=client_id,
            client_secret=client_secret, scopes=data.get("scopes"), expiry=expiry)
        if credentials.valid:
            return credentials
        credentials.refresh(Request())
    except Exception:
        raise HTTPException(503, "Gmail refresh failed; retry or reconnect") from None
    updated = {**data, "token": credentials.token,
               "refresh_token": credentials.refresh_token,
               "expiry": credentials.expiry.isoformat() if credentials.expiry else None}
    # Compare-and-set prevents a stale refresh overwriting a newer OAuth connection.
    result = db.table("gmail_connections").update({"token_json": encrypt(company_id, updated)}).eq("id", row["id"]).eq("company_id", company_id).eq("status", "connected").eq("token_json", json.dumps(row["token_json"])).execute()
    if not result.data:
        raise HTTPException(409, "Gmail connection changed; retry")
    return credentials
