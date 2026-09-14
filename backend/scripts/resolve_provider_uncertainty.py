"""Explicit operator recovery; read-only by default. No secret or payload output."""
import argparse
import json
import os
from uuid import UUID
from app.core.supabase_client import get_supabase_client


def validate(args):
    UUID(args.company)
    UUID(args.expected_id)
    if not os.environ.get("SUPABASE_URL") or args.expected_url.rstrip("/") != os.environ["SUPABASE_URL"].rstrip("/"):
        raise ValueError("Target mismatch")
    if args.apply and (not args.workers_stopped or not args.provider_reviewed or
                      len((args.operator or "").strip()) < 3 or len((args.ticket or "").strip()) < 3):
        raise ValueError("Stopped workers and provider review attestations required")


def run(db,args):
    validate(args)
    if args.apply:
        result=db.rpc("resolve_provider_uncertainty",{
            "p_company_id":args.company,"p_expected_id":args.expected_id,"p_kind":args.kind,
            "p_operator_ref":args.operator,"p_ticket_ref":args.ticket,
            "p_workers_stopped":args.workers_stopped,"p_provider_reviewed":args.provider_reviewed}).execute().data
        return {"resolved":result,"budget_refunded":False,"mail_sent":False}
    table="ai_budget_reservations" if args.kind=="ai" else "gmail_connections"
    return {"state":db.table(table).select("id,status").eq("company_id",args.company).eq("id",args.expected_id).execute().data,"changed":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("company","expected-id","expected-url"):parser.add_argument("--"+name,required=True)
    parser.add_argument("--kind",choices=("ai","gmail-revoke"),required=True)
    for name in ("apply","workers-stopped","provider-reviewed"):parser.add_argument("--"+name,action="store_true")
    for name in ("operator","ticket"):parser.add_argument("--"+name)
    args=parser.parse_args();validate(args)
    print(json.dumps(run(get_supabase_client(),args)))


if __name__=="__main__":
    try:main()
    except Exception:
        print('{"error":"RECOVERY_NOT_COMPLETED; inspect audit before retry"}')
        raise SystemExit(1) from None
