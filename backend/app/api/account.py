import os
import requests
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from app.core.auth import get_current_user
from app.core.company_context import _extract_user_id
from app.core.supabase_client import get_supabase_client
from app.services.account_deletion import read_job,public_status,resume
from app.services.gmail_work import company_lock
from app.services.billing import stripe_request

router=APIRouter(prefix="/account",tags=["account"])


class DeleteAccountRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    password:str=Field(min_length=1,max_length=1024)
    confirmation:str


@router.get("/deletion")
def deletion_status(user:dict=Depends(get_current_user)):
    job=read_job(get_supabase_client(),_extract_user_id(user))
    return public_status(job) if job else {"status":"not_requested","success":False}


@router.delete("")
def delete_account(payload:DeleteAccountRequest,user:dict=Depends(get_current_user)):
    if payload.confirmation!="削除":raise HTTPException(422,"Confirmation required")
    uid=_extract_user_id(user)
    email=user.get("email") or user.get("user",{}).get("email")
    if not uid or not email:raise HTTPException(401,"Verified identity required")
    try:
        retention=int(os.environ["ACCOUNT_AUDIT_RETENTION_DAYS"])
        if not 1<=retention<=3650:raise ValueError()
        url=os.environ["SUPABASE_URL"].rstrip("/")
        anon=os.environ["SUPABASE_ANON_KEY"]
    except (KeyError,ValueError):raise HTTPException(503,"Deletion configuration unavailable") from None
    try:
        response=requests.post(url+"/auth/v1/token?grant_type=password",
            headers={"apikey":anon},json={"email":email,"password":payload.password},timeout=15,allow_redirects=False)
        if response.status_code!=200 or response.json().get("user",{}).get("id")!=uid:
            raise HTTPException(401,"Reauthentication failed")
    except HTTPException:raise
    except Exception:raise HTTPException(503,"Reauthentication unavailable") from None
    db=get_supabase_client()
    job=read_job(db,uid)
    if not job:
        profiles=db.table("profiles").select("company_id").eq("user_id",uid).execute().data or []
        if len(profiles)!=1:raise HTTPException(403,"Company profile required")
        company=profiles[0]["company_id"]
        # Do not freeze a customer who still needs the cancellation screen.
        with company_lock(db,company,"delete-request"):
            rows=db.table("company_billing").select("stripe_subscription_id").eq("company_id",company).execute().data or []
            sid=rows[0].get("stripe_subscription_id") if rows else None
            if sid:
                sub=stripe_request("GET","subscriptions/"+sid)
                if sub.get("metadata",{}).get("company_id")!=company:raise HTTPException(403,"Billing association mismatch")
                if sub.get("status") not in {"canceled","incomplete_expired"}:
                    raise HTTPException(409,"Cancel and finish paid period before deletion")
            job=db.rpc("request_account_deletion",{"p_user_id":uid,"p_retention_days":retention}).execute().data
    return resume(db,job)
