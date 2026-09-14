"""Local rehearsal only; no credential values printed or written to files.

Default: counts only. --apply requires explicit disposable environment consent.
Production migration requires a separately reviewed/approved execution procedure.
Run from backend: python -m scripts.migrate_local_gmail_tokens [--apply]
"""
import argparse
import os
from urllib.parse import urlsplit
from supabase import create_client
from app.core.token_vault import encrypt, decrypt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    url = os.getenv("P0_SUPABASE_TEST_URL", "")
    parsed = urlsplit(url)
    if (url != os.getenv("P0_SUPABASE_EXPECTED_URL") or parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.port != 54321
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {"", "/"}
            or os.getenv("P0_ALLOW_FIXTURE_WRITES") != "CREATE_DISPOSABLE_FIXTURES"):
        raise SystemExit("Disposable loopback target confirmation required")
    db = create_client(url, os.environ["P0_SUPABASE_TEST_SERVICE_KEY"])
    offset, legacy, encrypted = 0, 0, 0
    while True:
        rows = db.table("gmail_connections").select("id,company_id,token_json").order("id").range(offset, offset+99).execute().data
        if not rows: break
        for row in rows:
            token = row["token_json"]
            if isinstance(token, dict) and token.get("version") == 1:
                decrypt(row["company_id"], token)
                encrypted += 1
                continue
            if not isinstance(token, dict) or not token.get("refresh_token"):
                raise RuntimeError("Connection requires reconnection; no writes for this row")
            envelope = encrypt(row["company_id"], token)
            assert decrypt(row["company_id"], envelope) == token
            legacy += 1
            if args.apply:
                # Rehearsal assumes stopped writers. Do not run concurrently with OAuth.
                db.table("gmail_connections").update({"token_json": envelope}).eq("id", row["id"]).eq("company_id", row["company_id"]).execute()
        offset += len(rows)
    print(f"legacy={legacy} encrypted={encrypted} applied={args.apply}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Migration stopped; inspect configuration without exposing credentials") from None
