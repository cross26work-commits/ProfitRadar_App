"""Exercise the scheduler and worker heartbeat against fixed local Supabase."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import requests

SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from scripts.run_local_regression import local_credentials
from scripts.validate_forward_local import validate_target
from scripts import sync_worker


BACKEND = "http://127.0.0.1:8022"


def child_environment(keys, scheduler_secret):
    keep = {key: value for key, value in os.environ.items() if key.upper() in {
        "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA",
        "USERPROFILE", "HOME", "PATHEXT", "COMSPEC",
    }}
    keep.update({
        "APP_ENV": "test", "PYTHON_DOTENV_DISABLED": "1",
        "SUPABASE_URL": "http://127.0.0.1:54321",
        "SUPABASE_SERVICE_ROLE_KEY": keys["service_role"],
        "SUPABASE_ANON_KEY": keys["anon"],
        "CORS_ORIGINS": "http://127.0.0.1:3190",
        "STRIPE_MODE": "test", "GMAIL_SCHEDULER_SECRET": scheduler_secret,
        "SCHEDULER_BACKEND_URL": BACKEND,
    })
    return keep


def run(approved=False):
    if not approved:
        raise RuntimeError("Explicit disposable fixture gate required")
    validate_target(True)
    keys = local_credentials()
    scheduler_secret = secrets.token_urlsafe(32)
    environment = child_environment(keys, scheduler_secret)
    backend_root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8022", "--log-level", "critical"],
        cwd=backend_root, env=environment, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    state = sync_worker.WorkerState()
    server = None
    previous = {name: os.environ.get(name) for name in
                ("SCHEDULER_BACKEND_URL", "GMAIL_SCHEDULER_SECRET", "WORKER_HEALTH_PORT")}
    try:
        for _ in range(40):
            if process.poll() is not None:
                raise RuntimeError("Isolated backend stopped")
            try:
                if requests.get(BACKEND + "/ready", timeout=1).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(.25)
        else:
            raise RuntimeError("Isolated backend readiness timeout")
        os.environ["SCHEDULER_BACKEND_URL"] = BACKEND
        os.environ["GMAIL_SCHEDULER_SECRET"] = scheduler_secret
        os.environ["WORKER_HEALTH_PORT"] = "8026"
        if not sync_worker.tick(state):
            raise RuntimeError("Isolated scheduler tick failed")
        server = sync_worker.start_health_server(state)
        health = requests.get("http://127.0.0.1:8026/health", timeout=2)
        ready = requests.get("http://127.0.0.1:8026/ready", timeout=2)
        if health.status_code != 200 or ready.status_code != 200:
            raise RuntimeError("Worker heartbeat verification failed")
        return {"status": "PASS", "backend_health": "PASS", "backend_readiness": "PASS",
                "scheduler_tick": "PASS", "worker_heartbeat": "PASS",
                "isolated_company_failures": state.snapshot().get("last_batch_failed"),
                "gmail_send_calls": 0, "production_contacts": 0}
    finally:
        if server:
            server.shutdown()
            server.server_close()
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-disposable-fixtures", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.allow_disposable_fixtures), sort_keys=True))
    except Exception:
        print('{"status":"BLOCKED","production_contacts":0}')
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
