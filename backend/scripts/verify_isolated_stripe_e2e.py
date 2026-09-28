"""Verify, cancel, and clean up the isolated real Stripe TEST subscription."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import hmac
import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import requests
from dotenv import dotenv_values
from supabase import create_client


ROOT = Path(__file__).resolve().parents[2]
ISOLATED = ROOT / ".local-isolated"
STATE_FILE = ISOLATED / "stripe-e2e-state.json"
SECRET_FILE = ISOLATED / "stripe-test.env"
RESULT_FILE = ISOLATED / "stripe-e2e-result.json"
COUNT_TABLES = ("companies", "profiles", "company_billing", "billing_checkout_attempts", "billing_webhook_events")


def local_status() -> dict[str, str]:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    result = subprocess.run(
        [npx, "--yes", "supabase@2.117.0", "status", "-o", "json"], cwd=ISOLATED,
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode:
        raise RuntimeError("Disposable Supabase unavailable")
    status = json.loads(result.stdout)
    parsed = urlsplit(status["API_URL"])
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.port != 54321:
        raise RuntimeError("Production target rejected")
    return status


def config() -> dict[str, str]:
    raw = dotenv_values(SECRET_FILE)
    values = {name: str(raw.get(name) or "").strip() for name in (
        "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID"
    )}
    for name, prefix in (("STRIPE_SECRET_KEY", "sk_test_"), ("STRIPE_WEBHOOK_SECRET", "whsec_"), ("STRIPE_PRICE_ID", "price_")):
        if not values[name].startswith(prefix):
            raise RuntimeError(f"Invalid TEST configuration: {name}")
    return values


def stripe(method: str, path: str, cfg: dict[str, str], data: dict | None = None) -> dict:
    response = requests.request(
        method, "https://api.stripe.com/v1/" + path,
        headers={"Authorization": "Bearer " + cfg["STRIPE_SECRET_KEY"]}, data=data,
        timeout=20, allow_redirects=False,
    )
    if response.status_code >= 400:
        raise RuntimeError("Stripe TEST request failed")
    payload = response.json()
    if "livemode" in payload and payload["livemode"] is not False:
        raise RuntimeError("LIVE Stripe response rejected")
    return payload


def counts(service) -> dict[str, int]:
    result = {}
    for table in COUNT_TABLES:
        response = service.table(table).select("*", count="exact", head=True).execute()
        if not isinstance(response.count, int):
            raise RuntimeError("Count unavailable")
        result[table] = response.count
    return result


def signed_post(backend: str, secret: str, event: dict) -> requests.Response:
    raw = json.dumps(event, separators=(",", ":")).encode()
    stamp = str(int(time.time()))
    digest = hmac.new(secret.encode(), stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
    return requests.post(
        backend + "/billing/webhook", data=raw,
        headers={"content-type": "application/json", "stripe-signature": f"t={stamp},v1={digest}"},
        timeout=20,
    )


def wait_billing(service, company_id: str, expected: str, timeout: int = 60) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rows = service.table("company_billing").select("*").eq("company_id", company_id).execute().data or []
        if rows and rows[0].get("status") == expected:
            return rows[0]
        time.sleep(1)
    raise RuntimeError(f"Billing state did not reach {expected}")


def subscription_event(session: dict, cfg: dict[str, str]) -> dict:
    events = stripe("GET", "events?type=customer.subscription.created&limit=10", cfg).get("data", [])
    event = next((item for item in events if item.get("data", {}).get("object", {}).get("id") == session["subscription"]), None)
    if not event:
        raise RuntimeError("Real subscription event unavailable")
    return event


def cleanup(service, state: dict, cfg: dict[str, str], session: dict) -> bool:
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")
    if subscription_id:
        current = stripe("GET", "subscriptions/" + subscription_id, cfg)
        if current.get("status") != "canceled":
            stripe("DELETE", "subscriptions/" + subscription_id, cfg)
            wait_billing(service, state["company_id"], "canceled")
    if customer_id:
        stripe("DELETE", "customers/" + customer_id, cfg)
    job = service.rpc("request_account_deletion", {
        "p_user_id": state["user_id"], "p_retention_days": 1,
    }).execute().data
    job_id = job.get("id") if isinstance(job, dict) else None
    if not job_id:
        raise RuntimeError("Deletion job unavailable")
    service.table("account_deletion_jobs").update({"gmail_done": True, "billing_done": True}).eq(
        "id", job_id).eq("company_id", state["company_id"]).execute()
    service.rpc("purge_account_data", {"p_job_id": job_id}).execute()
    service.auth.admin.delete_user(state["user_id"])
    service.rpc("complete_account_deletion", {"p_job_id": job_id}).execute()
    return not service.table("companies").select("id").eq("id", state["company_id"]).execute().data


def main() -> int:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    cfg = config()
    status = local_status()
    if state.get("supabase_url") != status["API_URL"] or state.get("backend_url") != "http://127.0.0.1:8021":
        raise RuntimeError("Isolation state mismatch")
    service = create_client(status["API_URL"], status["SERVICE_ROLE_KEY"])
    headers = {"Authorization": "Bearer " + state["access_token"]}
    attempts = service.table("billing_checkout_attempts").select("session_id").eq(
        "company_id", state["company_id"]).execute().data or []
    if len(attempts) != 1 or not attempts[0].get("session_id"):
        raise RuntimeError("Checkout attempt missing")
    session = stripe("GET", "checkout/sessions/" + attempts[0]["session_id"], cfg)
    if session.get("status") != "complete" or session.get("payment_status") != "paid" or not session.get("subscription"):
        raise RuntimeError("Stripe TEST payment not complete")
    real_event = subscription_event(session, cfg)
    existing = service.table("company_billing").select("status").eq(
        "company_id", state["company_id"]).single().execute().data
    if existing.get("status") != "active":
        recovered = signed_post(state["backend_url"], cfg["STRIPE_WEBHOOK_SECRET"], real_event)
        if recovered.status_code != 200:
            raise RuntimeError("Signed subscription event recovery failed")
    billing = wait_billing(service, state["company_id"], "active")
    if billing.get("stripe_subscription_id") != session["subscription"] or not billing.get("paid_until"):
        raise RuntimeError("Subscription persistence mismatch")
    status_response = requests.get(state["backend_url"] + "/billing/status", headers=headers, timeout=10)
    paid_feature = requests.post(state["backend_url"] + "/self-evaluation/run", headers=headers, timeout=10)
    if status_response.status_code != 200 or status_response.json().get("allowed") is not True or paid_feature.status_code != 200:
        raise RuntimeError("Paid entitlement did not activate")

    before_duplicate = service.table("billing_webhook_events").select("event_id", count="exact").eq(
        "company_id", state["company_id"]).execute().count
    first = signed_post(state["backend_url"], cfg["STRIPE_WEBHOOK_SECRET"], real_event)
    second = signed_post(state["backend_url"], cfg["STRIPE_WEBHOOK_SECRET"], real_event)
    after_duplicate = service.table("billing_webhook_events").select("event_id", count="exact").eq(
        "company_id", state["company_id"]).execute().count
    if first.status_code != 200 or second.status_code != 200 or after_duplicate != before_duplicate:
        raise RuntimeError("Duplicate webhook was not idempotent")

    invalid = requests.post(
        state["backend_url"] + "/billing/webhook", data=b"{}",
        headers={"content-type": "application/json", "stripe-signature": "t=0,v1=invalid"}, timeout=10,
    )
    if invalid.status_code != 400:
        raise RuntimeError("Invalid signature was not rejected")

    out_of_order = deepcopy(real_event)
    out_of_order["id"] = "evt_local_out_of_order_" + uuid4().hex
    out_of_order["type"] = "customer.subscription.updated"
    out_of_order["data"]["object"]["status"] = "past_due"
    stale = signed_post(state["backend_url"], cfg["STRIPE_WEBHOOK_SECRET"], out_of_order)
    current = service.table("company_billing").select("status").eq("company_id", state["company_id"]).single().execute().data
    if stale.status_code != 200 or current.get("status") != "active":
        raise RuntimeError("Out-of-order event changed current state")

    cancel = requests.post(state["backend_url"] + "/billing/cancel", headers=headers, timeout=20)
    if cancel.status_code != 200 or cancel.json().get("cancel_at_period_end") is not True:
        raise RuntimeError("Application cancellation failed")
    provider = stripe("GET", "subscriptions/" + session["subscription"], cfg)
    if provider.get("cancel_at_period_end") is not True:
        raise RuntimeError("Provider cancellation state mismatch")
    retained = requests.get(state["backend_url"] + "/billing/status", headers=headers, timeout=10).json()
    if retained.get("allowed") is not True:
        raise RuntimeError("Paid-period entitlement was removed too early")

    cleanup_ok = cleanup(service, state, cfg, session)
    after = counts(service)
    if not cleanup_ok or after != state["before_counts"]:
        raise RuntimeError("Cleanup or count restoration failed")
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "isolated-test",
        "stripe_mode": "TEST",
        "checkout": "PASS",
        "test_payment": "PASS",
        "signed_webhook": "PASS",
        "subscription_persistence": "PASS",
        "entitlement": "PASS",
        "paid_feature_access": "PASS",
        "duplicate_idempotency": "PASS",
        "cancellation_at_period_end": "PASS",
        "invalid_signature": "PASS",
        "out_of_order": "PASS",
        "cleanup": "PASS",
        "production_side_effects": 0,
        "secret_values_recorded": 0,
    }
    RESULT_FILE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    STATE_FILE.unlink()
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
