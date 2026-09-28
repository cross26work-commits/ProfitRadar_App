"""Start the local-only backend used to prepare Stripe TEST forwarding.

This launcher never loads backend/.env and never calls Stripe. It discovers
keys only from the already-running disposable Supabase project, requires the
fixed loopback ports, and writes no provider secret to logs or metadata.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
ISOLATED = ROOT / ".local-isolated"
PORT = 8021
PID_FILE = ISOLATED / "stripe-backend.pid"
META_FILE = ISOLATED / "stripe-backend.json"
STRIPE_ENV = ISOLATED / "stripe-test.env"


def _loopback(value: str, *, port: int) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port != port
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("Approved loopback target required")


def _status() -> dict[str, str]:
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
    _loopback(status.get("API_URL", ""), port=54321)
    if not status.get("SERVICE_ROLE_KEY") or not status.get("ANON_KEY"):
        raise RuntimeError("Disposable Supabase local keys unavailable")
    return status


def _port_free() -> None:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", PORT))
        except OSError as exc:
            raise RuntimeError(f"Port {PORT} is already in use") from exc


def _stripe_values() -> dict[str, str]:
    source = dotenv_values(STRIPE_ENV) if STRIPE_ENV.is_file() else {}
    values = {
        "STRIPE_SECRET_KEY": str(source.get("STRIPE_SECRET_KEY") or "").strip(),
        "STRIPE_WEBHOOK_SECRET": str(source.get("STRIPE_WEBHOOK_SECRET") or "").strip(),
        "STRIPE_PRICE_ID": str(source.get("STRIPE_PRICE_ID") or "").strip(),
    }
    present = [bool(value) for value in values.values()]
    if any(present) and not all(present):
        raise RuntimeError("All Stripe TEST values must be configured together")
    if all(present):
        if not values["STRIPE_SECRET_KEY"].startswith("sk_test_"):
            raise RuntimeError("Only an sk_test_ key is allowed")
        if not values["STRIPE_WEBHOOK_SECRET"].startswith("whsec_"):
            raise RuntimeError("Webhook signing secret must start with whsec_")
        if not values["STRIPE_PRICE_ID"].startswith("price_"):
            raise RuntimeError("Stripe TEST Price ID must start with price_")
        if any("\n" in value or "\r" in value for value in values.values()):
            raise RuntimeError("Multiline Stripe value rejected")
    return values


def _child_env(status: dict[str, str], stripe: dict[str, str]) -> dict[str, str]:
    allowed = (
        "PATH",
        "SystemRoot",
        "WINDIR",
        "TEMP",
        "TMP",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
        "COMSPEC",
        "PATHEXT",
    )
    env = {name: os.environ[name] for name in allowed if os.environ.get(name)}
    env.update(
        {
            "APP_ENV": "test",
            "STRIPE_MODE": "test",
            "SUPABASE_URL": status["API_URL"],
            "SUPABASE_SERVICE_ROLE_KEY": status["SERVICE_ROLE_KEY"],
            "SUPABASE_ANON_KEY": status["ANON_KEY"],
            "SUPABASE_JWT_SECRET": "",
            "FRONTEND_URL": "http://127.0.0.1:3190",
            "CORS_ORIGINS": "http://127.0.0.1:3190",
            "PYTHON_DOTENV_DISABLED": "1",
            "PYTHONPATH": str(BACKEND),
            "PYTHONIOENCODING": "utf-8",
        }
    )
    env.update(stripe)
    return env


def _wait(url: str, expected: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Isolated backend exited before readiness")
        try:
            with urlopen(url, timeout=2) as response:
                payload = json.loads(response.read())
                if response.status == 200 and payload.get("status") == expected:
                    return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {expected}")


def main() -> int:
    ISOLATED.mkdir(parents=True, exist_ok=True)
    _port_free()
    status = _status()
    stripe = _stripe_values()
    python = BACKEND / "venv" / "Scripts" / "python.exe"
    if not python.is_file():
        raise RuntimeError("Backend virtualenv is unavailable")
    log = (ISOLATED / "stripe-backend.log").open("wb")
    error = (ISOLATED / "stripe-backend-error.log").open("wb")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        [str(python), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND,
        env=_child_env(status, stripe),
        stdout=log,
        stderr=error,
        creationflags=creationflags,
    )
    try:
        _wait(f"http://127.0.0.1:{PORT}/health", "ok", process)
        _wait(f"http://127.0.0.1:{PORT}/ready", "ready", process)
    except Exception:
        process.terminate()
        raise
    PID_FILE.write_text(str(process.pid) + "\n", encoding="ascii")
    META_FILE.write_text(
        json.dumps(
            {
                "backend_url": f"http://127.0.0.1:{PORT}",
                "supabase_url": "http://127.0.0.1:54321",
                "stripe_mode": "test",
                "stripe_external_calls": 0,
                "stripe_credentials_configured": bool(stripe["STRIPE_SECRET_KEY"]),
                "purpose": "listener-preparation-only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "READY",
                "backend_url": f"http://127.0.0.1:{PORT}",
                "health": "PASS",
                "readiness": "PASS",
                "supabase_loopback": True,
                "stripe_mode": "test",
                "stripe_external_calls": 0,
                "stripe_credentials_configured": bool(stripe["STRIPE_SECRET_KEY"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
