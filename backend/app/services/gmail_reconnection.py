"""Never reuse a refresh credential across accounts, clients or revoked connections."""
from fastapi import HTTPException
from app.core.token_vault import decrypt


def merge_refresh(company_id,email,new_token,existing):
    result=dict(new_token)
    if result.get("refresh_token"):
        return result
    if existing and existing.get("status")=="connected" and existing.get("email","").lower()==email.lower():
        old=decrypt(company_id,existing["token_json"])
        if old.get("client_id")==result.get("client_id") and old.get("refresh_token"):
            result["refresh_token"]=old["refresh_token"]
            return result
    raise HTTPException(409,"Gmail offline access requires reconnection")
