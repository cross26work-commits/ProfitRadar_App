import json
from pathlib import Path

from app.core.runtime_settings import PRODUCTION_REQUIRED, AI_PRODUCTION_REQUIRED


SCHEMA = Path(__file__).resolve().parents[2] / "deploy" / "production-env.schema.json"


def test_production_environment_schema_covers_runtime_and_has_no_secret_public_names():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    backend = schema["backend_required"]
    assert len(backend) == len(set(backend))
    assert set(PRODUCTION_REQUIRED).issubset(set(backend) | set(schema["worker_required"]))
    assert set(AI_PRODUCTION_REQUIRED).issubset(backend)
    assert schema["production_constants"]["STRIPE_MODE"] == "live"
    assert all(not name.startswith("NEXT_PUBLIC_") for name in schema["server_secret_only"])
    assert {"BACKEND_ORIGIN", "NEXT_PUBLIC_API_BASE_URL"}.issubset(schema["frontend_required"])
    assert {"WORKER_HEALTH_URL", "MONITORING_WEBHOOK_URL"}.issubset(schema["worker_required"])
    assert {"PGPASSWORD", "BACKUP_AGE_IDENTITY_FILE"}.issubset(schema["backup_required"])
