"""Supervised five-minute Gmail scheduler with a loopback health endpoint.

This process never holds a browser JWT. The backend endpoint owns per-company
retry policy and distributed locks. Process-level backoff is only for a failed
batch request (for example an unavailable backend); it never releases a DB lock.
"""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import signal
import threading
import time
from urllib.parse import urlsplit

import requests


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def emit(event, severity="info", **fields):
    # Only fixed operational fields are permitted. Never log URLs, headers,
    # provider bodies, customer identifiers, email, tokens, or secrets.
    print(json.dumps({"event": event, "severity": severity, "at": utcnow(), **fields},
                     sort_keys=True), flush=True)


def scheduler_config():
    base = os.getenv("SCHEDULER_BACKEND_URL", "").rstrip("/")
    secret = os.getenv("GMAIL_SCHEDULER_SECRET", "")
    target = urlsplit(base)
    if (not secret or target.username or target.password or target.query or target.fragment
            or target.path not in {"", "/"} or not target.hostname
            or (target.scheme != "https" and not (target.scheme == "http" and target.hostname in {"localhost", "127.0.0.1"}))):
        raise RuntimeError("Invalid scheduler configuration")
    return base, secret


class WorkerState:
    def __init__(self):
        self.lock = threading.Lock()
        self.values = {
            "status": "starting", "started_at": utcnow(), "last_attempt_at": None,
            "last_completion_at": None, "last_success_at": None,
            "consecutive_failures": 0, "last_batch_failed": None,
        }

    def update(self, **values):
        with self.lock:
            self.values.update(values)

    def snapshot(self):
        with self.lock:
            return dict(self.values)


def tick(state=None, request=requests.post):
    base, secret = scheduler_config()
    if state:
        state.update(status="running", last_attempt_at=utcnow())
    try:
        result = request(base + "/gmail/scheduled-sync",
                         headers={"X-Scheduler-Secret": secret}, timeout=60,
                         allow_redirects=False)
        result.raise_for_status()
        body = result.json()
        safe = {key: int(body.get(key, 0)) for key in
                ("processed", "succeeded", "failed", "busy", "deferred")}
        emit("sync_batch", severity="warning" if safe["failed"] else "info", **safe)
        if state:
            previous_success = state.snapshot()["last_success_at"]
            state.update(status="degraded" if safe["failed"] else "healthy",
                         last_completion_at=utcnow(),
                         last_success_at=previous_success if safe["failed"] else utcnow(),
                         consecutive_failures=0, last_batch_failed=safe["failed"])
        return True
    except Exception:
        failures = (state.snapshot()["consecutive_failures"] + 1) if state else 1
        if state:
            state.update(status="degraded", last_completion_at=utcnow(),
                         consecutive_failures=failures)
        emit("sync_batch_failed", severity="error", consecutive_failures=failures)
        return False


def health_handler(state):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in {"/health", "/ready"}:
                self.send_error(404)
                return
            snapshot = state.snapshot()
            ready = snapshot["last_completion_at"] is not None
            status = 200 if self.path == "/health" or ready else 503
            payload = {"service": "profit-radar-sync-worker", "alive": True,
                       "ready": ready, **snapshot}
            encoded = json.dumps(payload, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_args):
            return
    return Handler


def start_health_server(state):
    host = os.getenv("WORKER_HEALTH_HOST", "127.0.0.1")
    exposure = os.getenv("WORKER_HEALTH_EXPOSURE", "loopback")
    production = os.getenv("APP_ENV") == "production"
    railway_private = production and exposure == "railway-private" and host == "0.0.0.0"
    if host not in {"127.0.0.1", "localhost"} and not railway_private:
        raise RuntimeError("Worker health endpoint exposure is invalid")
    configured_port = os.getenv("WORKER_HEALTH_PORT", "8025")
    railway_port = os.getenv("PORT", "") if railway_private else ""
    if railway_private and (not railway_port or configured_port != railway_port):
        raise RuntimeError("Railway worker health port must match PORT")
    port = int(railway_port or configured_port)
    if not 1 <= port <= 65535:
        raise RuntimeError("Invalid worker health port")
    server = ThreadingHTTPServer((host, port), health_handler(state))
    thread = threading.Thread(target=server.serve_forever, name="worker-health", daemon=True)
    thread.start()
    return server


def backoff_seconds(failures, interval, maximum):
    return min(maximum, interval * (2 ** max(0, failures - 1)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run one batch for an isolated smoke test")
    args = parser.parse_args(argv)
    scheduler_config()  # Fail before advertising health.
    if os.getenv("APP_ENV") == "production" and any(not os.getenv(name, "").strip() for name in (
            "GMAIL_SYNC_INTERVAL_SECONDS", "WORKER_MAX_BACKOFF_SECONDS",
            "WORKER_HEALTH_HOST", "WORKER_HEALTH_PORT", "WORKER_HEALTH_EXPOSURE")):
        raise RuntimeError("Production worker settings must be explicit")
    interval = int(os.getenv("GMAIL_SYNC_INTERVAL_SECONDS", "300"))
    maximum = int(os.getenv("WORKER_MAX_BACKOFF_SECONDS", "3600"))
    if not 5 <= interval <= 3600 or maximum < interval:
        raise RuntimeError("Invalid worker interval configuration")
    state = WorkerState()
    stop = threading.Event()

    def stopping(_signum, _frame):
        state.update(status="stopping")
        stop.set()

    signal.signal(signal.SIGTERM, stopping)
    signal.signal(signal.SIGINT, stopping)
    server = start_health_server(state)
    emit("worker_started")
    try:
        while not stop.is_set():
            started = time.monotonic()
            ok = tick(state)
            if args.once:
                break
            failures = state.snapshot()["consecutive_failures"]
            delay = interval if ok else backoff_seconds(failures, interval, maximum)
            stop.wait(max(1, delay - (time.monotonic() - started)))
    finally:
        state.update(status="stopped")
        server.shutdown()
        server.server_close()
        emit("worker_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
