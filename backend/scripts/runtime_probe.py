"""Independent availability probe for the public app, API and local worker.

It emits fixed status names only. URLs, response bodies, credentials and
provider errors are never logged or sent to the optional alert receiver.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from urllib.parse import urlsplit

import requests


def endpoint(name, *, loopback=False, railway_private=False):
    raw = os.getenv(name, "").rstrip("/")
    parsed = urlsplit(raw)
    private_allowed = (railway_private and os.getenv("WORKER_HEALTH_EXPOSURE") == "railway-private"
                       and parsed.scheme == "http" and bool(parsed.hostname)
                       and parsed.hostname.endswith(".railway.internal"))
    allowed = parsed.scheme == "https" or private_allowed or (loopback and parsed.scheme == "http"
                                                                and parsed.hostname in {"localhost", "127.0.0.1"})
    if (not allowed or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
        raise ValueError("Monitoring endpoint configuration invalid")
    return raw


def check(get=requests.get):
    targets = {
        "frontend": (endpoint("FRONTEND_URL"), "/"),
        "backend_health": (endpoint("BACKEND_URL"), "/health"),
        "backend_readiness": (endpoint("BACKEND_URL"), "/ready"),
        "worker_heartbeat": (endpoint("WORKER_HEALTH_URL", loopback=True, railway_private=True), "/health"),
        "worker_readiness": (endpoint("WORKER_HEALTH_URL", loopback=True, railway_private=True), "/ready"),
    }
    statuses = {}
    for name, (base, path) in targets.items():
        try:
            response = get(base + path, timeout=5, allow_redirects=False)
            passed = 200 <= response.status_code < 300
            if passed and name.startswith("worker_"):
                body = response.json()
                passed = body.get("status") == "healthy" and int(body.get("last_batch_failed", 0) or 0) == 0
            statuses[name] = "pass" if passed else "fail"
        except Exception:
            statuses[name] = "fail"
    return {"event": "runtime_probe", "severity": "info" if all(x == "pass" for x in statuses.values()) else "critical",
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checks": statuses}


def notify(result, post=requests.post):
    target = endpoint("MONITORING_WEBHOOK_URL")
    payload = {"event": result["event"], "severity": result["severity"],
               "checks": dict(result["checks"])}
    try:
        response = post(target, json=payload, timeout=5, allow_redirects=False)
        if not 200 <= response.status_code < 300:
            raise ValueError()
    except Exception:
        raise ValueError("Monitoring delivery not confirmed") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args(argv)
    result = check()
    print(json.dumps(result, sort_keys=True))
    if args.notify:
        notify(result)
    return 0 if result["severity"] == "info" else 1


if __name__ == "__main__":
    raise SystemExit(main())
