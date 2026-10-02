import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def test_railway_plan_is_three_services_and_never_runs_migrations():
    plan = json.loads((ROOT / "deploy/railway/service-plan.json").read_text(encoding="utf-8"))
    assert set(plan["services"]) == {"frontend", "backend", "worker"}
    assert plan["automaticMigrationOnDeploy"] is False
    assert plan["services"]["frontend"]["rootDirectory"] == "/frontend"
    assert "$PORT" in plan["services"]["frontend"]["startCommand"]
    assert plan["services"]["backend"]["healthcheckPath"] == "/ready"
    assert plan["services"]["worker"]["publicDomain"] is None
    assert plan["services"]["worker"]["healthcheckPath"] == "/health"
    assert all("migrat" not in service["startCommand"].lower() for service in plan["services"].values())


def test_production_scripts_are_gated_and_do_not_embed_provider_operations():
    scripts = ROOT / "scripts/production"
    smoke = (scripts / "Invoke-ProductionSmokeTest.ps1").read_text(encoding="utf-8")
    preflight = (scripts / "Invoke-ProductionPreflight.ps1").read_text(encoding="utf-8")
    migration = (scripts / "Test-MigrationSafety.ps1").read_text(encoding="utf-8")
    secret_scan = (scripts / "Test-RepositorySecrets.ps1").read_text(encoding="utf-8")
    fresh_migrations = (scripts / "Test-FreshSupabaseMigrations.ps1").read_text(encoding="utf-8")
    fresh_evidence = (scripts / "Test-FreshMigrationEvidence.ps1").read_text(encoding="utf-8")
    fresh_stage = (scripts / "Stage-FreshProductionMigrations.ps1").read_text(encoding="utf-8")
    assert "I_APPROVE_READ_ONLY_PRODUCTION_SMOKE_TEST" in smoke
    assert "Invoke-WebRequest" in smoke and "-Method Get" in smoke
    assert all(token not in smoke.lower() for token in ("railway up", "supabase db push", "stripe trigger"))
    assert "status --porcelain" in preflight and "Release working tree must be clean" in preflight
    assert "FreshMigrationEvidence" in preflight and "Test-FreshMigrationEvidence.ps1" in preflight
    assert "DROP\\s+TABLE" in migration and "TRUNCATE" in migration and "DELETE\\s+FROM" in migration
    approved = json.loads((ROOT / "deploy/migration-reviewed-delete-bodies.json").read_text(encoding="utf-8"))
    assert "202609150001_remote_schema_forward_v2.sql" in approved["files"]
    assert "PRIVATE KEY" in secret_scan and "whsec_" in secret_scan and "findings=0" in secret_scan
    assert "AllowDisposableDockerFixtures" in fresh_migrations
    assert "[ValidateRange(3,3)]" in fresh_migrations
    assert "no_historical_db_dependency='PASS'" in fresh_migrations
    assert "canonical_schema_parity='PASS'" in fresh_migrations
    assert "rls_runner='READY'" in fresh_migrations
    assert "supabase db push" not in fresh_migrations and "--linked" not in fresh_migrations
    assert "schema hash evidence is invalid or nondeterministic" in fresh_evidence
    assert "Fresh migration evidence run numbers are not exactly 1,2,3" in fresh_evidence
    assert "35 passed," in fresh_evidence and "skipped" in fresh_evidence
    assert "production_connections -ne 0" in fresh_stage
    assert "$LASTEXITCODE" not in fresh_stage


def test_fresh_production_stream_is_hash_pinned_complete_and_fail_closed():
    manifest = json.loads((ROOT / "deploy/fresh-production/migration-stream.json").read_text(encoding="utf-8"))
    source_files = {path.name for path in (ROOT / "supabase/migrations").glob("*.sql")}
    included = {item["source"] for item in manifest["migrations"]}
    excluded = {item["source"] for item in manifest["excluded_remote_supplements"]}
    assert included | excluded == source_files
    assert included & excluded == set()
    assert excluded == {"202609140001_remote_schema_forward.sql",
                        "202609150001_remote_schema_forward_v2.sql"}
    assert manifest["target"] == "new-supabase-project-only"
    assert manifest["region"] == "ap-northeast-1"
    assert manifest["canonical_schema_sha256"] == "55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D"
    import hashlib
    for item in manifest["migrations"] + manifest["excluded_remote_supplements"]:
        assert hashlib.sha256((ROOT / "supabase/migrations" / item["source"]).read_bytes()).hexdigest().upper() == item["sha256"]
    for name in ("guard", "completion"):
        item = manifest[name]
        assert hashlib.sha256((ROOT / item["source"]).read_bytes()).hexdigest().upper() == item["sha256"]
    guard = (ROOT / manifest["guard"]["source"]).read_text(encoding="utf-8")
    completion = (ROOT / manifest["completion"]["source"]).read_text(encoding="utf-8")
    assert "migration history is not empty" in guard
    assert "profiles.full_name canonical contract mismatch" in completion
    for column in ("gmail_thread_id", "last_gmail_message_id", "recoverable_profit",
                   "neglected_days", "description"):
        assert f"add column {column}" in completion
    assert "grant update(status, actual_input_tokens, actual_output_tokens)" in completion
    assert "grant update(gmail_done, billing_done, billing_reference, last_error_code)" in completion


def test_production_document_set_and_dns_placeholders_are_complete():
    required = (
        "PRODUCTION_ARCHITECTURE.md", "PRODUCTION_ENVIRONMENT_MATRIX.md",
        "PRODUCTION_DEPLOYMENT_RUNBOOK.md", "PRODUCTION_OWNER_ACTIONS.md",
        "PRODUCTION_ROLLBACK_PLAN.md", "PRODUCTION_SMOKE_TEST.md",
        "PRODUCTION_SUPABASE_MIGRATION_DECISION.md",
    )
    for name in required:
        assert (ROOT / "docs" / name).is_file()
    runbook = (ROOT / "docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md").read_text(encoding="utf-8")
    assert "<RAILWAY_FRONTEND_TARGET>" in runbook
    assert "<RAILWAY_BACKEND_TARGET>" in runbook
    assert "blind `supabase db push`" in runbook


def test_env_schema_covers_worker_railway_private_contract():
    schema = json.loads((ROOT / "deploy/production-env.schema.json").read_text(encoding="utf-8"))
    required = {"APP_ENV", "WORKER_HEALTH_EXPOSURE", "WORKER_HEALTH_HOST",
                "WORKER_HEALTH_PORT", "WORKER_HEALTH_URL"}
    assert required.issubset(schema["worker_required"])
    assert (required - {"APP_ENV"}).issubset(schema["backend_required"])


def test_pytest_isolation_prevents_ignored_dotenv_remote_target():
    import os
    assert os.environ["APP_ENV"] == "test"
    assert os.environ["SUPABASE_URL"].startswith(("http://127.0.0.1:", "http://localhost:"))


def test_worker_environment_validator_accepts_only_explicit_private_contract(tmp_path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell, "PowerShell is required by the Production operator scripts"
    env_file = tmp_path / "worker.env"
    env_file.write_text("\n".join((
        "APP_ENV=production", "SCHEDULER_BACKEND_URL=https://api.profitradar.jp",
        "GMAIL_SCHEDULER_SECRET=synthetic-non-secret", "GMAIL_SYNC_INTERVAL_SECONDS=300",
        "WORKER_MAX_BACKOFF_SECONDS=3600", "WORKER_HEALTH_HOST=0.0.0.0",
        "WORKER_HEALTH_PORT=8080", "WORKER_HEALTH_URL=http://worker.railway.internal:8080",
        "WORKER_HEALTH_EXPOSURE=railway-private", "MONITORING_WEBHOOK_URL=https://alerts.corp",
    )) + "\n", encoding="utf-8")
    script = ROOT / "scripts/production/Test-ProductionEnvironment.ps1"
    result = subprocess.run((shell, "-NoProfile", "-File", str(script), "-Service", "worker",
                             "-EnvironmentFile", str(env_file)), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "PASS"
    assert "synthetic-non-secret" not in result.stdout
