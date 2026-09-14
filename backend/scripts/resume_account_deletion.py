"""Explicit operator retry, readonly by default. Never print credentials or rows."""
import argparse
import json
import os
from uuid import UUID
from app.core.supabase_client import get_supabase_client
from app.services.account_deletion import resume,public_status


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job",required=True)
    parser.add_argument("--expected-url",required=True)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args();UUID(args.job)
    if args.expected_url.rstrip("/")!=os.environ.get("SUPABASE_URL","").rstrip("/"):
        raise ValueError("Target mismatch")
    db=get_supabase_client()
    rows=db.table("account_deletion_jobs").select("*").eq("id",args.job).execute().data
    if len(rows)!=1:raise ValueError("Job missing")
    print(json.dumps(resume(db,rows[0]) if args.apply else public_status(rows[0]),ensure_ascii=False))


if __name__=="__main__":
    try:main()
    except Exception:
        print('{"success":false,"error":"DELETION_PENDING"}')
        raise SystemExit(1) from None
