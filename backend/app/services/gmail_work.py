from contextlib import contextmanager
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException


@contextmanager
def company_lock(db, company_id, purpose):
    owner = str(uuid4())
    claimed = db.rpc("claim_gmail_work", {"p_company_id":company_id,"p_owner_id":owner,"p_purpose":purpose}).execute().data
    if claimed is not True:
        raise HTTPException(409,"Gmail operation already running")
    try:
        yield
    finally:
        db.rpc("release_gmail_work", {"p_company_id":company_id,"p_owner_id":owner}).execute()


def sync_company(db, company_id, work):
    from app.services.billing import require_use
    require_use(db,company_id)
    with company_lock(db, company_id, "sync"):
        run_id = str(uuid4())
        db.table("gmail_company_sync_runs").insert({"id":run_id,"company_id":company_id,"status":"running"}).execute()
        try:
            result = work()
        except Exception:
            db.table("gmail_company_sync_runs").update({"status":"failed","error_code":"SYNC_FAILED","finished_at":datetime.now(timezone.utc).isoformat()}).eq("id",run_id).eq("company_id",company_id).execute()
            raise HTTPException(503,"Gmail sync failed; retry later") from None
        db.table("gmail_company_sync_runs").update({"status":"succeeded","finished_at":datetime.now(timezone.utc).isoformat(),"detected_count":int(result.get("count",0))}).eq("id",run_id).eq("company_id",company_id).execute()
        return result


def batch(company_ids, work):
    summary={"processed":0,"succeeded":0,"failed":0,"busy":0,"deferred":0,"errors":[]}
    for company_id in company_ids:
        summary["processed"]+=1
        try:
            result=work(company_id)
            summary["deferred" if isinstance(result,dict) and result.get("deferred") is True else "succeeded"]+=1
        except HTTPException as exc:
            code="BUSY" if exc.status_code==409 else "SYNC_FAILED"
            summary["busy" if code=="BUSY" else "failed"]+=1
            summary["errors"].append({"company_id":company_id,"code":code})
        except Exception:
            summary["failed"]+=1
            summary["errors"].append({"company_id":company_id,"code":"SYNC_FAILED"})
    return summary


def retry_due(recent_runs, now=None):
    """Bound consecutive company failures; never release a running lock here."""
    if not recent_runs:
        return True
    if recent_runs[0].get("status") == "running":
        return False
    failures = 0
    for row in recent_runs:
        if row.get("status") != "failed":
            break
        failures += 1
    if not failures:
        return True
    try:
        last = datetime.fromisoformat(recent_runs[0]["finished_at"].replace("Z", "+00:00"))
        if last.tzinfo is None:
            return False
        delay = min(300 * 2 ** (failures - 1), 3600)
        return (now or datetime.now(timezone.utc)) >= last + timedelta(seconds=delay)
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return False
