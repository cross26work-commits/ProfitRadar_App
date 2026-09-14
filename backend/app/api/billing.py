import os
from datetime import datetime,timezone
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter,Depends,HTTPException,Request
from app.core.company_context import get_current_company_id
from app.core.supabase_client import get_supabase_client
from app.services import billing
from app.services.gmail_work import company_lock

router=APIRouter(prefix="/billing",tags=["billing"])


class CheckoutIntent(BaseModel):
    model_config=ConfigDict(extra="forbid")
    expected_mode:Literal["test","live"]="test"


@router.get("/status")
def billing_status(company_id: str=Depends(get_current_company_id)):
    return billing.status(get_supabase_client(),company_id)


@router.post("/checkout")
def checkout(company_id: str=Depends(get_current_company_id),payload:CheckoutIntent|None=None):
    # Legacy clients imply TEST; a deployment switch cannot silently turn a
    # previously shown test confirmation into a real paid signup.
    expected=payload.expected_mode if payload else "test"
    if expected!=billing.configured_mode():
        raise HTTPException(409,"Billing mode changed; reload and confirm the current signup")
    db=get_supabase_client()
    with company_lock(db,company_id,"checkout"):
        current=billing.status(db,company_id)
        if current["status"] not in {"trial","trial_expired","canceled","incomplete_expired"}:
            raise HTTPException(409,"Resolve the existing subscription before starting another")
        price=os.getenv("STRIPE_PRICE_ID","")
        base=os.getenv("FRONTEND_URL","").rstrip("/")
        if not price or not base: raise HTTPException(503,"Checkout not configured")
        product=billing.stripe_request("GET",f"prices/{price}")
        if product.get("active") is not True or product.get("currency")!="jpy" or product.get("unit_amount")!=19800 or product.get("recurring",{}).get("interval")!="month" or product.get("recurring",{}).get("interval_count")!=1 or product.get("tax_behavior")!="inclusive":
            raise HTTPException(503,"Billing price configuration mismatch")
        attempts=db.table("billing_checkout_attempts").select("*").eq("company_id",company_id).execute().data
        attempt=attempts[0] if attempts else None
        if attempt and attempt.get("session_id"):
            previous=billing.stripe_request("GET","checkout/sessions/"+attempt["session_id"])
            if previous.get("client_reference_id")!=company_id:raise HTTPException(409,"Checkout association mismatch")
            if previous.get("status")=="open": return {"url":previous["url"],"test_mode":billing.configured_mode()=="test"}
            if previous.get("status")=="complete" and current["status"] in {"canceled","incomplete_expired"}:
                sid=previous.get("subscription")
                if not isinstance(sid,str):raise HTTPException(409,"Previous subscription requires review")
                ended=billing.stripe_request("GET","subscriptions/"+sid)
                if ended.get("metadata",{}).get("company_id")!=company_id or ended.get("status") not in {"canceled","incomplete_expired"}:
                    raise HTTPException(409,"Previous subscription is not terminated")
            elif previous.get("status")!="expired": raise HTTPException(409,"Checkout completed; waiting for billing confirmation")
            attempt=None
        if attempt:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(attempt["created_at"].replace("Z","+00:00"))).total_seconds()
            if age>23*3600: raise HTTPException(409,"Checkout outcome requires administrator reconciliation")
        else:
            attempt={"company_id":company_id,"attempt_id":str(uuid4()),"created_at":datetime.now(timezone.utc).isoformat(),"session_id":None}
            if not db.table("billing_checkout_attempts").upsert(attempt,on_conflict="company_id").execute().data:
                raise HTTPException(503,"Checkout attempt was not saved")
        session=billing.stripe_request("POST","checkout/sessions",{
            "mode":"subscription","line_items[0][price]":price,"line_items[0][quantity]":1,
            "client_reference_id":company_id,"subscription_data[metadata][company_id]":company_id,
            "success_url":base+"/settings/plan?checkout=complete","cancel_url":base+"/settings/plan?checkout=cancelled",
        },idempotency_key="checkout-"+attempt["attempt_id"])
        if not db.table("billing_checkout_attempts").update({"session_id":session["id"]}).eq("company_id",company_id).eq("attempt_id",attempt["attempt_id"]).execute().data:
            raise HTTPException(503,"Checkout result unknown; retry the existing attempt")
        return {"url":session["url"],"test_mode":billing.configured_mode()=="test"}


@router.post("/cancel")
def cancel_subscription(company_id: str=Depends(get_current_company_id)):
    db=get_supabase_client()
    with company_lock(db,company_id,"billing-cancel"):
        rows=db.table("company_billing").select("stripe_subscription_id").eq("company_id",company_id).execute().data
        if not rows or not rows[0].get("stripe_subscription_id"): raise HTTPException(409,"No paid subscription")
        sid=rows[0]["stripe_subscription_id"]
        current=billing.stripe_request("GET","subscriptions/"+sid)
        if current.get("metadata",{}).get("company_id")!=company_id: raise HTTPException(403,"Subscription association mismatch")
        billing.stripe_request("POST","subscriptions/"+sid,{"cancel_at_period_end":"true"},idempotency_key="cancel-"+sid)
        return {"cancel_at_period_end":True,"message":"期間末解約を受け付けました。支払済み期間の終了後は送信・同期を停止します。"}


@router.post("/webhook")
async def webhook(request:Request):
    raw=await request.body()
    if len(raw)>1000000: raise HTTPException(413,"Payload too large")
    event=billing.verify_event(raw,request.headers.get("stripe-signature",""))
    if not event.get("type","").startswith("customer.subscription."):
        return {"received":True,"ignored":True}
    obj=event["data"]["object"]
    company_id=obj.get("metadata",{}).get("company_id")
    if not company_id: raise HTTPException(400,"Missing subscription association")
    db=get_supabase_client()
    with company_lock(db,company_id,"billing"):
        # Fetch current provider state under lock; do not apply out-of-order event snapshots.
        current=billing.stripe_request("GET","subscriptions/"+obj["id"])
        if current.get("metadata",{}).get("company_id")!=company_id: raise HTTPException(400,"Association mismatch")
        linked=db.table("company_billing").select("stripe_subscription_id").eq("company_id",company_id).execute().data or []
        linked_id=linked[0].get("stripe_subscription_id") if linked else None
        if linked_id!=obj["id"]:
            # Only the persisted, user-requested checkout can establish/replace a contract.
            attempts=db.table("billing_checkout_attempts").select("session_id").eq("company_id",company_id).execute().data or []
            if not attempts or not attempts[0].get("session_id"):
                raise HTTPException(503,"Checkout association pending")
            checkout=billing.stripe_request("GET","checkout/sessions/"+attempts[0]["session_id"])
            if checkout.get("client_reference_id")!=company_id:
                raise HTTPException(400,"Checkout association mismatch")
            if checkout.get("subscription")!=obj["id"]:
                return {"received":True,"ignored":True}
            if checkout.get("status")!="complete":
                raise HTTPException(503,"Checkout completion pending")
        end=current.get("current_period_end") or min((item.get("current_period_end",0) for item in current.get("items",{}).get("data",[])),default=0)
        db.rpc("apply_billing_snapshot",{"p_company_id":company_id,"p_event_id":event["id"],"p_subscription_id":obj["id"],"p_status":current["status"],"p_paid_until":datetime.fromtimestamp(end,timezone.utc).isoformat() if end else None}).execute()
    return {"received":True}
