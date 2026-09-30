"""Read-only health counters by default; explicitly approved retention sweep only.

Run as `python -m scripts.maintenance --expected-url <configured target>`.
No Gmail, AI, Auth deletion or billing provider is called by this command.
"""
import argparse
import json
import os
from urllib.parse import urlsplit
import requests
from datetime import datetime,timezone,timedelta
from app.core.supabase_client import get_supabase_client


def counters(db):
    # Only counts are returned, no customer rows, message text or credentials.
    threshold=(datetime.now(timezone.utc)-timedelta(minutes=15)).isoformat()
    queries={
      "unresolved_sends":db.table("gmail_send_operations").select("operation_id",count="exact",head=True).in_("status",["unknown","sending"]),
      "pending_deletions":db.table("account_deletion_jobs").select("id",count="exact",head=True).neq("status","completed"),
      "reserved_ai":db.table("ai_budget_reservations").select("id",count="exact",head=True).eq("status","reserved"),
        "old_company_locks":db.table("gmail_work_locks").select("company_id",count="exact",head=True).lt("acquired_at",threshold),
        "recent_sync_failures":db.table("gmail_company_sync_runs").select("id",count="exact",head=True).eq("status","failed").gte("started_at",threshold),
        "stuck_sync_runs":db.table("gmail_company_sync_runs").select("id",count="exact",head=True).eq("status","running").lt("started_at",threshold),
        "recent_ai_failures":db.table("ai_usage_runs").select("id",count="exact",head=True).in_("status",["failed","fallback"]).gte("created_at",threshold),
        "unhandled_support":db.table("support_requests").select("id",count="exact",head=True).eq("status","unhandled"),
        "unknown_support_replies":db.table("support_messages").select("id",count="exact",head=True).in_("delivery_status",["unknown","sending"]),
    }
    result={}
    for name,query in queries.items():
        value=query.execute().count
        if type(value) is not int or value<0:raise ValueError("Count unavailable")
        result[name]=value
    return result


def run(db,expected_url,apply_retention=False):
    if not os.environ.get("SUPABASE_URL") or expected_url.rstrip("/")!=os.environ["SUPABASE_URL"].rstrip("/"):
        raise ValueError("Target mismatch")
    result={"event":"maintenance","severity":"info","counts":counters(db),"retention_applied":False}
    if apply_retention:
        if os.getenv("RETENTION_SWEEP_APPROVED")!="true":raise ValueError("Retention policy approval required")
        result["purged_audit_jobs"]=db.rpc("purge_expired_deletion_audit",{}).execute().data
        try:
            support_days=int(os.environ["SUPPORT_RETENTION_DAYS"])
        except (KeyError, ValueError):
            raise ValueError("Support retention policy required") from None
        result["purged_support_requests"]=db.rpc("purge_expired_support_records",{"p_retention_days":support_days}).execute().data
        result["retention_applied"]=True
    result["operator_review_required"]=any(result["counts"].values())
    if result["operator_review_required"]:
        result["severity"]="warning"
    return result


def notify(result):
    target=os.getenv("MONITORING_WEBHOOK_URL","")
    parsed=urlsplit(target)
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Monitoring HTTPS destination required")
    # Fixed operational counts only. Never include rows, provider exceptions,
    # URLs, tickets, environment values, email or tokens in the payload.
    payload={"event":"profit_radar_maintenance","severity":result.get("severity","warning"),"review_required":bool(result["operator_review_required"]),
             "counts":{key:int(result["counts"][key]) for key in ("unresolved_sends","pending_deletions","reserved_ai","old_company_locks","recent_sync_failures","stuck_sync_runs","recent_ai_failures","unhandled_support","unknown_support_replies")}}
    try:
        response=requests.post(target,json=payload,timeout=5,allow_redirects=False)
        if not 200<=response.status_code<300:raise ValueError()
    except Exception:
        raise ValueError("Monitoring delivery not confirmed") from None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-url",required=True)
    parser.add_argument("--apply-retention",action="store_true")
    parser.add_argument("--notify",action="store_true",help="Explicitly send fixed health counters to the configured HTTPS monitoring receiver")
    args=parser.parse_args()
    result=run(get_supabase_client(),args.expected_url,args.apply_retention)
    if args.notify:notify(result)
    print(json.dumps(result))


if __name__=="__main__":
    try:main()
    except Exception:
        print('{"event":"maintenance_failed","severity":"critical","operator_review_required":true}')
        raise SystemExit(1) from None
