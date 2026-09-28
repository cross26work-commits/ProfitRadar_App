"""Prepare one real Stripe TEST Checkout through the Profit Radar API.

All credentials and transient identifiers stay under the gitignored
.local-isolated directory. Console output is deliberately non-sensitive.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import requests
from dotenv import dotenv_values
from supabase import create_client


ROOT = Path(__file__).resolve().parents[2]
ISOLATED = ROOT / ".local-isolated"
SECRET_FILE = ISOLATED / "stripe-test.env"
STATE_FILE = ISOLATED / "stripe-e2e-state.json"
BACKEND_URL = "http://127.0.0.1:8021"
COUNT_TABLES = (
    "companies",
    "profiles",
    "company_billing",
    "billing_checkout_attempts",
    "billing_webhook_events",
)


def _local_status() -> dict[str, str]:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise RuntimeError("npx is unavailable")
    result = subprocess.run(
        [npx, "--yes", "supabase@2.117.0", "status", "-o", "json"],
        cwd=ISOLATED,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError("Disposable Supabase status unavailable")
    status = json.loads(result.stdout)
    parsed = urlsplit(status.get("API_URL", ""))
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.port != 54321:
        raise RuntimeError("Approved disposable Supabase required")
    return status


def _stripe_config() -> dict[str, str]:
    source = dotenv_values(SECRET_FILE)
    values = {name: str(source.get(name) or "").strip() for name in (
        "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID"
    )}
    expected = {
        "STRIPE_SECRET_KEY": "sk_test_",
        "STRIPE_WEBHOOK_SECRET": "whsec_",
        "STRIPE_PRICE_ID": "price_",
    }
    for name, prefix in expected.items():
        if not values[name].startswith(prefix) or "\n" in values[name] or "\r" in values[name]:
            raise RuntimeError(f"Invalid isolated Stripe TEST configuration: {name}")
    return values


def _counts(service) -> dict[str, int]:
    result: dict[str, int] = {}
    for table in COUNT_TABLES:
        response = service.table(table).select("*", count="exact", head=True).execute()
        if not isinstance(response.count, int):
            raise RuntimeError("Isolated table count unavailable")
        result[table] = response.count
    return result


def main() -> int:
    if STATE_FILE.exists():
        raise RuntimeError("Existing Stripe E2E state requires review or cleanup")
    _stripe_config()
    status = _local_status()
    health = requests.get(BACKEND_URL + "/health", timeout=3)
    ready = requests.get(BACKEND_URL + "/ready", timeout=3)
    if health.status_code != 200 or health.json().get("status") != "ok":
        raise RuntimeError("Isolated Backend health failed")
    if ready.status_code != 200 or ready.json().get("status") != "ready":
        raise RuntimeError("Isolated Backend readiness failed")

    service = create_client(status["API_URL"], status["SERVICE_ROLE_KEY"])
    browser = create_client(status["API_URL"], status["ANON_KEY"])
    before = _counts(service)
    marker = f"Stripe E2E {uuid4().hex}"
    email = f"stripe-e2e-{uuid4().hex}@example.invalid"
    password = secrets.token_urlsafe(32)
    user_id = company_id = None
    try:
        user = service.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        ).user
        user_id = str(user.id)
        session = browser.auth.sign_in_with_password({"email": email, "password": password}).session
        if not session:
            raise RuntimeError("Local Auth login failed")
        token = session.access_token
        headers = {"Authorization": f"Bearer {token}"}
        onboard = requests.post(
            BACKEND_URL + "/onboarding",
            headers=headers,
            json={"company_name": marker, "name": "Stripe isolated fixture"},
            timeout=10,
        )
        if onboard.status_code != 200:
            raise RuntimeError("Application onboarding failed")
        company_id = onboard.json()["result"][0]["company_id"]
        service.rpc("ensure_company_billing", {"p_company_id": company_id}).execute()
        expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        updated = service.table("company_billing").update(
            {"status": "trial", "trial_ends_at": expired, "paid_until": None}
        ).eq("company_id", company_id).execute().data
        if not updated:
            raise RuntimeError("Isolated trial expiry setup failed")
        denied = requests.post(BACKEND_URL + "/self-evaluation/run", headers=headers, timeout=10)
        if denied.status_code != 402:
            raise RuntimeError("Paid feature was not denied before subscription")
        checkout = requests.post(
            BACKEND_URL + "/billing/checkout",
            headers=headers,
            json={"expected_mode": "test"},
            timeout=30,
        )
        if checkout.status_code != 200:
            raise RuntimeError("Application Checkout creation failed")
        payload = checkout.json()
        checkout_url = str(payload.get("url") or "")
        parsed = urlsplit(checkout_url)
        if payload.get("test_mode") is not True or parsed.scheme != "https" or parsed.hostname != "checkout.stripe.com":
            raise RuntimeError("Unexpected Checkout result")
        state = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backend_url": BACKEND_URL,
            "supabase_url": status["API_URL"],
            "marker": marker,
            "email": email,
            "password": password,
            "user_id": user_id,
            "company_id": company_id,
            "access_token": token,
            "checkout_url": checkout_url,
            "before_counts": before,
            "pre_subscription_paid_feature_status": denied.status_code,
        }
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        try:
            STATE_FILE.chmod(0o600)
        except OSError:
            pass
        print(json.dumps({
            "status": "READY_FOR_TEST_CHECKOUT",
            "stripe_mode": "test",
            "application_checkout": "PASS",
            "pre_subscription_entitlement_denied": True,
            "checkout_url_stored": True,
            "production_contacts": 0,
        }))
        return 0
    except Exception:
        if company_id:
            service.table("billing_checkout_attempts").delete().eq("company_id", company_id).execute()
            service.table("company_billing").delete().eq("company_id", company_id).execute()
            service.table("profiles").delete().eq("company_id", company_id).execute()
            service.table("companies").delete().eq("id", company_id).execute()
        if user_id:
            service.auth.admin.delete_user(user_id)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
