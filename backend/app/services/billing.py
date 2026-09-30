"""Seven-day card-on-file trial with explicit disclosure and automatic renewal.

Default TEST only; live requires deployment approval and a matching DB gate.
"""
import os
import time
import hashlib
import hmac
import json
from datetime import datetime,timezone
import requests
from fastapi import HTTPException
from app.core.billing_mode import configured_mode, require_database_mode


def status(db, company_id):
    mode = configured_mode()
    if os.getenv("APP_ENV") not in {"development", "test"}:
        require_database_mode(db)
    rows=db.rpc("ensure_company_billing",{"p_company_id":company_id}).execute().data
    if not rows: raise HTTPException(403,"Company not found")
    row=rows[0]
    now=datetime.now(timezone.utc)
    trial=datetime.fromisoformat(row["trial_ends_at"].replace("Z","+00:00"))
    paid=datetime.fromisoformat(row["paid_until"].replace("Z","+00:00")) if row.get("paid_until") else None
    trial_status = row["status"] in {"trial", "trialing"}
    allowed=(trial_status and trial>now) or (row["status"]=="active" and paid is not None and paid>now)
    display_status = row["status"] if allowed else ("trial_expired" if trial_status else row["status"])
    return {"status":display_status,"allowed":bool(allowed),"trial_ends_at":row["trial_ends_at"],"paid_until":row.get("paid_until"),
            "trial_days":7,"monthly_price_jpy":19800,"today_due_jpy":0,
            "automatic_trial_charge":True,"automatic_renewal":True,"business_only":True,
            "first_billing_at":row["trial_ends_at"],"test_mode":mode=="test"}


def require_use(db,company_id):
    if db.rpc("company_is_active",{"p_company_id":company_id}).execute().data is not True:
        raise HTTPException(423,"Company deletion is in progress")
    if not status(db,company_id)["allowed"]:
        raise HTTPException(402,"Trial ended or subscription unavailable")



def require_ai_preview(db, company_id):
    # Compatibility name only: no unmigrated database bypass in any environment.
    return require_use(db,company_id)



def stripe_request(method,path,data=None,idempotency_key=None):
    mode=configured_mode()
    key=os.getenv("STRIPE_SECRET_KEY","")
    if not key.startswith((f"sk_{mode}_",f"rk_{mode}_")):
        raise HTTPException(503,"Stripe credentials do not match deployment mode")
    from app.core.supabase_client import get_supabase_client
    require_database_mode(get_supabase_client())
    headers={"Authorization":f"Bearer {key}"}
    if idempotency_key: headers["Idempotency-Key"]=idempotency_key
    try:
        response=requests.request(method,"https://api.stripe.com/v1/"+path,headers=headers,data=data,timeout=15,allow_redirects=False)
        if response.status_code>=400: raise ValueError()
        result=response.json()
        if result.get("livemode") is not (mode=="live"): raise ValueError()
        return result
    except Exception:
        raise HTTPException(503,"Billing provider temporarily unavailable") from None


def verify_event(raw,header):
    mode=configured_mode()
    secret=os.getenv("STRIPE_WEBHOOK_SECRET","")
    if not secret: raise HTTPException(503,"Billing webhook not configured")
    try:
        pairs=[part.split("=",1) for part in header.split(",")]
        stamp=next(value for key,value in pairs if key=="t")
        if abs(time.time()-int(stamp))>300: raise ValueError()
        expected=hmac.new(secret.encode(),stamp.encode()+b"."+raw,hashlib.sha256).hexdigest()
        if not any(key=="v1" and hmac.compare_digest(expected,value) for key,value in pairs): raise ValueError()
        event=json.loads(raw)
        if event.get("livemode") is not (mode=="live"): raise ValueError()
        return event
    except Exception:
        raise HTTPException(400,"Invalid webhook") from None
