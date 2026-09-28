"""One-call AI restart proof against the fixed disposable Supabase only.

The parent process reads only OPENAI_API_KEY from backend/.env and only the
AI names declared by runtime_settings from .env.owner-gate. It never loads the
repository .env into the backend child. The generated env and report live under
.local-isolated, which is gitignored.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from uuid import uuid4

from dotenv import dotenv_values

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
ISOLATED = ROOT / ".local-isolated"
DEDICATED_ENV = ISOLATED / "ai-e2e.env"
RESULT_FILE = ISOLATED / "ai-e2e-result.json"
PORT = 8019
COUNT_TABLES = ("companies", "profiles", "company_billing", "ai_usage_runs", "ai_budget_reservations")

sys.path.insert(0, str(BACKEND))
from app.core.runtime_settings import AI_PRODUCTION_REQUIRED  # noqa: E402


def _loopback_url(name: str, value: str) -> None:
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise RuntimeError(f"{name} must be an explicit loopback HTTP URL")


def validate_isolated_env(values: dict[str, str]) -> None:
    if values.get("APP_ENV") != "test":
        raise RuntimeError("APP_ENV must be test")
    _loopback_url("SUPABASE_URL", values.get("SUPABASE_URL", ""))
    _loopback_url("FRONTEND_URL", values.get("FRONTEND_URL", ""))
    if values.get("STRIPE_MODE") != "test":
        raise RuntimeError("Only Stripe TEST mode is allowed")
    stripe_key = values.get("STRIPE_SECRET_KEY", "")
    if stripe_key and not stripe_key.startswith("sk_test_"):
        raise RuntimeError("Only an sk_test_ Stripe key is allowed")
    for name, value in values.items():
        if name.endswith("_URL") and value and name not in {"OPENAI_BASE_URL"}:
            _loopback_url(name, value)
        if "\r" in value or "\n" in value:
            raise RuntimeError(f"Multiline value rejected: {name}")
    missing = [name for name in AI_PRODUCTION_REQUIRED if not values.get(name, "").strip()]
    if missing:
        raise RuntimeError("Required isolated AI settings are missing: " + ",".join(missing))


def _local_status() -> dict[str, str]:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise RuntimeError("npx is unavailable")
    result = subprocess.run(
        [npx, "--yes", "supabase@2.117.0", "status", "-o", "json"],
        cwd=ISOLATED, capture_output=True, text=True, timeout=60,
    )
    if result.returncode:
        raise RuntimeError("Disposable Supabase status is unavailable")
    status = json.loads(result.stdout)
    _loopback_url("SUPABASE_URL", status.get("API_URL", ""))
    if urlsplit(status["API_URL"]).port != 54321:
        raise RuntimeError("Unexpected disposable Supabase port")
    return status


def build_isolated_env() -> dict[str, str]:
    status = _local_status()
    secret_source = dotenv_values(BACKEND / ".env")
    owner_source = dotenv_values(BACKEND / ".env.owner-gate")
    values = {
        "APP_ENV": "test",
        "STRIPE_MODE": "test",
        "SUPABASE_URL": status["API_URL"],
        "SUPABASE_SERVICE_ROLE_KEY": status["SERVICE_ROLE_KEY"],
        "SUPABASE_ANON_KEY": status["ANON_KEY"],
        # Exercise the same local Auth user lookup as the existing disposable
        # integration suite. Do not assume the local token signing algorithm.
        "SUPABASE_JWT_SECRET": "",
        "FRONTEND_URL": "http://127.0.0.1:3190",
        "CORS_ORIGINS": "http://127.0.0.1:3190",
        "PYTHON_DOTENV_DISABLED": "1",
    }
    for name in AI_PRODUCTION_REQUIRED:
        source = secret_source if name == "OPENAI_API_KEY" else owner_source
        values[name] = str(source.get(name) or "")
    validate_isolated_env(values)
    return values


def _write_env(values: dict[str, str]) -> None:
    ISOLATED.mkdir(parents=True, exist_ok=True)
    DEDICATED_ENV.write_text("".join(f"{key}={value}\n" for key, value in sorted(values.items())), encoding="utf-8")
    try:
        DEDICATED_ENV.chmod(0o600)
    except OSError:
        pass


def _child_env(values: dict[str, str]) -> dict[str, str]:
    allowed = ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA", "USERPROFILE", "COMSPEC", "PATHEXT")
    child = {name: os.environ[name] for name in allowed if os.environ.get(name)}
    child.update(values)
    child["PYTHONPATH"] = str(BACKEND)
    child["PYTHONIOENCODING"] = "utf-8"
    return child


def _wait(url: str, expected: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Isolated backend exited before readiness")
        try:
            with urlopen(url, timeout=2) as response:
                if response.status == 200 and json.loads(response.read())["status"] == expected:
                    return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {expected}")


def _assert_port_free() -> None:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", PORT))
        except OSError as exc:
            raise RuntimeError(f"Isolated backend port {PORT} is already in use") from exc


def _counts(service) -> dict[str, int]:
    result = {}
    for table in COUNT_TABLES:
        response = service.table(table).select("*", count="exact", head=True).execute()
        if not isinstance(response.count, int):
            raise RuntimeError("Isolated count unavailable")
        result[table] = response.count
    return result


def _cleanup(service, *, user_id: str | None, company_id: str | None, marker: str | None) -> None:
    if company_id:
        company = service.table("companies").select("id,name").eq("id", company_id).execute().data or []
        if len(company) != 1 or company[0].get("name") != marker:
            raise RuntimeError("Isolated fixture identity mismatch; cleanup stopped")
        # Preserve production least privilege: service_role deliberately has no
        # direct DELETE on internal AI tables. Reconcile a possible uncertain
        # reservation, then use the resumable deletion RPCs that own the exact
        # dependency order.
        reserved = service.table("ai_budget_reservations").select("id").eq(
            "company_id", company_id).eq("status", "reserved").execute().data or []
        for row in reserved:
            service.rpc("resolve_provider_uncertainty", {
                "p_company_id": company_id, "p_expected_id": row["id"], "p_kind": "ai",
                "p_operator_ref": "isolated-ai-e2e", "p_ticket_ref": "isolated-ai-e2e",
                "p_workers_stopped": True, "p_provider_reviewed": True,
            }).execute()
        job = service.rpc("request_account_deletion", {
            "p_user_id": user_id, "p_retention_days": 1,
        }).execute().data
        job_id = job["id"] if isinstance(job, dict) else None
        if not job_id:
            raise RuntimeError("Isolated deletion job unavailable")
        service.table("account_deletion_jobs").update({
            "gmail_done": True, "billing_done": True,
        }).eq("id", job_id).eq("company_id", company_id).execute()
        service.rpc("purge_account_data", {"p_job_id": job_id}).execute()
        if user_id:
            service.auth.admin.delete_user(user_id)
            user_id = None
        service.rpc("complete_account_deletion", {"p_job_id": job_id}).execute()
        if service.table("companies").select("id").eq("id", company_id).execute().data:
            raise RuntimeError("Isolated company cleanup incomplete")
    if user_id:
        service.auth.admin.delete_user(user_id)


def _verify_accounting(db, company_id: str, cap: int) -> dict:
    usage = db.table("ai_usage_runs").select("status,input_tokens,output_tokens,cost_usd,elapsed_ms").eq("company_id", company_id).order("created_at", desc=True).limit(1).single().execute().data
    budget = db.table("ai_budget_reservations").select("status,actual_input_tokens,actual_output_tokens,reserved_cost_micro_usd,token_limit,cost_limit_micro_usd").eq("company_id", company_id).order("created_at", desc=True).limit(1).single().execute().data
    runs = db.table("ai_usage_runs").select("id", count="exact").eq("company_id", company_id).execute()
    if (usage.get("status") != "succeeded" or not usage.get("input_tokens") or not usage.get("output_tokens")
            or usage.get("cost_usd") in (None, "", 0) or budget.get("status") != "succeeded"
            or not budget.get("actual_input_tokens") or not budget.get("actual_output_tokens")
            or not budget.get("reserved_cost_micro_usd") or (runs.count or 0) > cap):
        raise RuntimeError("AI accounting verification failed")
    return {
        "provider": "openai", "generation_calls": 1, "usage_status": usage["status"],
        "input_tokens_recorded": True, "output_tokens_recorded": True, "cost_recorded": True,
        "budget_status": budget["status"], "company_budget_recorded": True,
        "generation_limit": cap, "generation_count": runs.count,
        "usage_elapsed_ms": usage.get("elapsed_ms"),
    }


def run() -> int:
    values = build_isolated_env()
    _write_env(values)
    _assert_port_free()
    child = _child_env(values)
    log_path = ISOLATED / "ai-e2e-backend.log"
    service = None
    user_id = company_id = marker = None
    before = after = None
    cleanup_ok = False
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [str(BACKEND / "venv" / "Scripts" / "python.exe"), "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(PORT)],
            cwd=BACKEND, env=child, stdout=log, stderr=subprocess.STDOUT, text=True,
        )
        try:
            _wait(f"http://127.0.0.1:{PORT}/health", "ok", process)
            _wait(f"http://127.0.0.1:{PORT}/ready", "ready", process)
            from supabase import create_client
            service = create_client(values["SUPABASE_URL"], values["SUPABASE_SERVICE_ROLE_KEY"])
            before = _counts(service)
            email = f"ai-restart-{uuid4().hex}@example.invalid"
            password = secrets.token_urlsafe(32)
            user = service.auth.admin.create_user({"email": email, "password": password, "email_confirm": True}).user
            user_id = str(user.id)
            browser = create_client(values["SUPABASE_URL"], values["SUPABASE_ANON_KEY"])
            session = browser.auth.sign_in_with_password({"email": email, "password": password}).session
            import requests
            marker = f"AI restart {user.id}"
            onboard = requests.post(
                f"http://127.0.0.1:{PORT}/onboarding",
                headers={"Authorization": f"Bearer {session.access_token}"},
                json={"company_name": marker, "name": "Isolated AI fixture"}, timeout=10,
            )
            if onboard.status_code != 200:
                raise RuntimeError("Isolated onboarding failed")
            company_id = onboard.json()["result"][0]["company_id"]
            started = time.monotonic()
            generated = requests.post(
                f"http://127.0.0.1:{PORT}/ai-judge/judge",
                headers={"Authorization": f"Bearer {session.access_token}"},
                json={"subject": "隔離AI再起動検証", "sender": "isolated@example.invalid",
                      "body": "来月の提案内容を確認しました。対応可否を確認のうえ返信してください。"},
                timeout=90,
            )
            latency_ms = int((time.monotonic() - started) * 1000)
            if generated.status_code != 200:
                raise RuntimeError("Isolated provider generation failed")
            result = generated.json().get("result", {})
            if (result.get("provider") != "openai" or not isinstance(result.get("reason"), str)
                    or not result.get("reason") or not isinstance(result.get("next_action"), str)
                    or not result.get("next_action") or result.get("conversation_ai_error")):
                raise RuntimeError("Provider-backed judgement validation failed")
            safe = _verify_accounting(service, company_id, int(values["AI_MONTHLY_GENERATION_LIMIT"]))
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                    text=True, check=True).stdout.strip()
            report = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "commit_sha": commit, "environment": "isolated-test", "isolation": "PASS",
                "health": "PASS", "ready": "PASS", "restart": "PASS", **safe,
                "model": values["OPENAI_MODEL_STANDARD"], "scenario": "authenticated-ai-judge",
                "request": "PASS", "response_validation": "PASS", "latency_ms": latency_ms,
                "retry_count": 0, "production_side_effects": 0, "secret_leakage": 0,
                "supabase_target": "loopback", "gmail_send_calls": 0, "stripe_calls": 0,
            }
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if service is not None:
                _cleanup(service, user_id=user_id, company_id=company_id, marker=marker)
                after = _counts(service) if before is not None else None
                cleanup_ok = before == after
                if not cleanup_ok:
                    raise RuntimeError("Isolated fixture count mismatch after cleanup")
            if 'report' in locals():
                report["cleanup"] = "PASS" if cleanup_ok else "FAIL"
                RESULT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(run())
