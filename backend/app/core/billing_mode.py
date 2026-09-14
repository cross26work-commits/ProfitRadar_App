"""Deployment-only billing gate. No key or provider access in this module."""
import os
import re
from urllib.parse import urlsplit
from fastapi import HTTPException


def configured_mode():
    mode = os.getenv("STRIPE_MODE", "test")
    if mode not in {"test", "live"}:
        raise HTTPException(503, "Billing mode configuration invalid")
    if mode == "live":
        url = urlsplit(os.getenv("FRONTEND_URL", ""))
        if (os.getenv("APP_ENV") != "production"
                or os.getenv("BILLING_LIVE_APPROVED") != "true"
                or not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", os.getenv("BILLING_LIVE_APPROVAL_REF", ""))
                or url.scheme != "https" or not url.hostname or url.username
                or url.password or url.query or url.fragment or url.path not in {"", "/"}):
            raise HTTPException(503, "Live billing deployment approval required")
    return mode


def require_database_mode(db):
    mode = configured_mode()
    try:
        rows = db.table("billing_runtime_config").select("mode,approval_ref").eq("singleton", True).execute().data
        if len(rows) != 1 or rows[0]["mode"] != mode:
            raise ValueError()
        if mode == "live" and rows[0]["approval_ref"] != os.getenv("BILLING_LIVE_APPROVAL_REF"):
            raise ValueError()
    except Exception:
        raise HTTPException(503, "Billing deployment mode mismatch") from None
    return mode
