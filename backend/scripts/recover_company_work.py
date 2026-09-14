"""Read-only by default. Run from backend; secrets only from environment.

Before --apply, stop ALL API/worker processes for the target deployment and
verify no in-flight Gmail requests remain. Never use age alone to unlock.
"""
import argparse
import json
import os
from uuid import UUID
from supabase import create_client


def validate(args):
    UUID(args.company)
    if args.expected_url.rstrip("/")!=os.environ.get("SUPABASE_URL", "").rstrip("/"):
        raise ValueError("Target mismatch")
    if args.apply and (not args.workers_stopped or not args.owner or not args.operator or not args.ticket):
        raise ValueError("Stopped-worker attestation, expected owner and audit references required")
    if args.owner: UUID(args.owner)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company",required=True);parser.add_argument("--expected-url",required=True)
    parser.add_argument("--apply",action="store_true");parser.add_argument("--workers-stopped",action="store_true")
    parser.add_argument("--owner");parser.add_argument("--operator");parser.add_argument("--ticket")
    args=parser.parse_args();validate(args)
    db=create_client(os.environ["SUPABASE_URL"],os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    if args.apply:
        result=db.rpc("recover_company_work",{"p_company_id":args.company,"p_expected_owner":args.owner,
            "p_operator_ref":args.operator,"p_ticket_ref":args.ticket,"p_workers_stopped":True}).execute().data
        print(json.dumps({"recovered":result,"resend_permitted":False}))
    else:
        rows=db.table("gmail_work_locks").select("owner_id,purpose,acquired_at").eq("company_id",args.company).execute().data
        ops=db.table("gmail_send_operations").select("status").eq("company_id",args.company).in_("status",["sending","unknown"]).execute().data
        print(json.dumps({"lock":rows,"unresolved_send_count":len(ops),"changed":False}))


if __name__=="__main__":
    try:main()
    except Exception:
        print('{"error":"RECOVERY_NOT_COMPLETED","changed":"verify audit before retry"}')
        raise SystemExit(1) from None
