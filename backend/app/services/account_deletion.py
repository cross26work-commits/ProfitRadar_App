"""Resumable deletion. No success until DB and Auth deletion are both confirmed."""
from fastapi import HTTPException
from app.services.gmail_work import company_lock
from app.services.gmail_revocation import disconnect
from app.services.billing import stripe_request


def read_job(db,user_id):
    rows=db.table("account_deletion_jobs").select("*").eq("user_id",user_id).execute().data or []
    return rows[0] if rows else None


def public_status(job):
    return {"success":job["status"]=="completed","status":job["status"],"job_id":job["id"],
            "message":"削除が完了しました" if job["status"]=="completed" else "削除処理は未完了です。再試行または運営者による復旧が必要です。"}


def mark(db,job,**fields):
    if not db.table("account_deletion_jobs").update(fields).eq("id",job["id"]).eq("user_id",job["user_id"]).execute().data:
        raise HTTPException(503,"Deletion state was not saved")


def resume(db,job):
    if job["status"]=="completed":return public_status(job)
    try:
        if job["status"] in {"providers","data"}:
            with company_lock(db,job["company_id"],"delete"):
                job=read_job(db,job["user_id"])
                if not job["gmail_done"]:
                    disconnect(db,job["company_id"])
                    mark(db,job,gmail_done=True)
                if not job["billing_done"]:
                    rows=db.table("company_billing").select("stripe_subscription_id").eq("company_id",job["company_id"]).execute().data or []
                    sid=rows[0].get("stripe_subscription_id") if rows else None
                    if sid:
                        sub=stripe_request("GET","subscriptions/"+sid)
                        if sub.get("metadata",{}).get("company_id")!=job["company_id"]:raise HTTPException(409,"Billing association changed")
                        if sub.get("status") not in {"canceled","incomplete_expired"}:
                            raise HTTPException(409,"Cancel subscription and wait for its period to end before deletion")
                    mark(db,job,billing_done=True,billing_reference=sid)
                db.rpc("purge_account_data",{"p_job_id":job["id"]}).execute()
        # Auth removal is outside the database transaction. Retry only this phase.
        try:
            db.auth.admin.delete_user(job["user_id"])
        except Exception as error:
            if getattr(error,"code",None)!="user_not_found":raise
        db.rpc("complete_account_deletion",{"p_job_id":job["id"]}).execute()
        return public_status(read_job(db,job["user_id"]))
    except Exception:
        try:mark(db,job,last_error_code="DELETION_PENDING")
        except Exception:pass  # Do not replace the retained durable job with a success.
        raise HTTPException(503,"Deletion pending; no completion confirmed") from None
