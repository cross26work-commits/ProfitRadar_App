"""Revocation is explicit user action. Failures retain encrypted retry material."""
import requests
from fastapi import HTTPException
from app.core.token_vault import decrypt


def require_changed(response):
    # PostgREST can succeed with zero matched rows after a concurrent change.
    # Never report disconnect success or contact Google unless our state write
    # really took effect. The caller holds the shared company work lock.
    if not response.data:
        raise HTTPException(409, "Gmail connection changed; reload and retry")


def revoke(token):
    try:
        response = requests.post("https://oauth2.googleapis.com/revoke", data={"token": token}, timeout=10, allow_redirects=False)
    except requests.RequestException:
        raise HTTPException(503, "Gmail disconnect pending; retry later") from None
    if response.status_code != 200:
        raise HTTPException(503, "Gmail disconnect pending; retry later")


def disconnect(db, company_id):
    rows = db.table("gmail_connections").select("id,token_json,status").eq("company_id", company_id).execute().data or []
    for row in rows:
        if row.get("status")=="revoked":
            # Provider success was committed earlier; retry only local removal.
            require_changed(db.table("gmail_connections").delete().eq("company_id",company_id).eq("id",row["id"]).eq("status","revoked").execute())
            continue
        # Stop new Gmail work before contacting the provider. Keep token until success.
        require_changed(db.table("gmail_connections").update({"status": "revocation_pending"}).eq("company_id", company_id).eq("id", row["id"]).eq("status", row["status"]).execute())
        token = decrypt(company_id, row["token_json"])
        refresh = token.get("refresh_token") or token.get("token")
        if not refresh:
            raise HTTPException(503, "Gmail disconnect requires administrator review")
        revoke(refresh)
        require_changed(db.table("gmail_connections").update({"status":"revoked","token_json":{}}).eq("company_id",company_id).eq("id",row["id"]).eq("status","revocation_pending").execute())
        require_changed(db.table("gmail_connections").delete().eq("company_id", company_id).eq("id", row["id"]).eq("status","revoked").execute())
    return {"disconnected": True, "message": "Gmail connection revoked and removed"}
