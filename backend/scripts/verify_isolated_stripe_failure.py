"""Verify a real declined Stripe TEST Checkout and clean up its local fixture."""
from __future__ import annotations

from datetime import datetime, timezone
import json

import requests
from supabase import create_client

from verify_isolated_stripe_e2e import (
    RESULT_FILE,
    STATE_FILE,
    cleanup,
    config,
    counts,
    local_status,
    stripe,
)


def main() -> int:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    cfg = config()
    status = local_status()
    if state.get("supabase_url") != status["API_URL"] or state.get("backend_url") != "http://127.0.0.1:8021":
        raise RuntimeError("Isolation state mismatch")
    service = create_client(status["API_URL"], status["SERVICE_ROLE_KEY"])
    headers = {"Authorization": "Bearer " + state["access_token"]}
    attempts = service.table("billing_checkout_attempts").select("session_id").eq(
        "company_id", state["company_id"]
    ).execute().data or []
    if len(attempts) != 1 or not attempts[0].get("session_id"):
        raise RuntimeError("Checkout attempt missing")
    session = stripe("GET", "checkout/sessions/" + attempts[0]["session_id"], cfg)
    if session.get("status") != "open" or session.get("payment_status") != "unpaid":
        raise RuntimeError("Declined Checkout did not remain open and unpaid")
    if session.get("subscription"):
        raise RuntimeError("Declined Checkout created a subscription")

    rows = service.table("company_billing").select("status,stripe_subscription_id").eq(
        "company_id", state["company_id"]
    ).execute().data or []
    if len(rows) != 1 or rows[0].get("stripe_subscription_id"):
        raise RuntimeError("Declined Checkout persisted a subscription")
    billing_status = requests.get(state["backend_url"] + "/billing/status", headers=headers, timeout=10)
    paid_feature = requests.post(state["backend_url"] + "/self-evaluation/run", headers=headers, timeout=10)
    if billing_status.status_code != 200 or billing_status.json().get("allowed") is not False:
        raise RuntimeError("Declined Checkout enabled billing entitlement")
    if paid_feature.status_code != 402:
        raise RuntimeError("Declined Checkout enabled a paid feature")

    stripe("POST", "checkout/sessions/" + attempts[0]["session_id"] + "/expire", cfg)
    cleanup_ok = cleanup(service, state, cfg, session)
    after = counts(service)
    if not cleanup_ok or after != state["before_counts"]:
        raise RuntimeError("Declined Checkout cleanup or count restoration failed")

    result = json.loads(RESULT_FILE.read_text(encoding="utf-8")) if RESULT_FILE.exists() else {}
    result.update({
        "payment_failure": "PASS",
        "payment_failure_provider": "real Stripe TEST Checkout decline",
        "failure_subscription_created": False,
        "failure_entitlement_granted": False,
        "failure_paid_feature_status": 402,
        "failure_cleanup": "PASS",
        "failure_verified_at": datetime.now(timezone.utc).isoformat(),
    })
    RESULT_FILE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    STATE_FILE.unlink()
    print(json.dumps({
        "payment_failure": "PASS",
        "subscription_created": False,
        "entitlement_granted": False,
        "paid_feature_status": 402,
        "cleanup": "PASS",
        "production_side_effects": 0,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
