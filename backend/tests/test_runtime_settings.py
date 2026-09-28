import pytest
from app.core.runtime_settings import cors_origins, validate_production


def production_values():
    return {
        "APP_ENV": "production", "STRIPE_MODE": "live",
        "BILLING_LIVE_APPROVED": "true", "BILLING_LIVE_APPROVAL_REF": "release-123",
        "SUPABASE_URL": "https://project.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "fixture",
        "SUPABASE_ANON_KEY": "fixture", "FRONTEND_URL": "https://app.example.com",
        "BACKEND_URL": "https://api.example.com", "CORS_ORIGINS": "https://app.example.com",
        "OAUTH_STATE_SECRET": "fixture", "GMAIL_TOKEN_ENCRYPTION_KEYS": "fixture",
        "OPENAI_API_KEY": "fixture", "GOOGLE_CLIENT_ID": "fixture", "GOOGLE_CLIENT_SECRET": "fixture",
        "GOOGLE_REDIRECT_URI": "https://api.example.com/gmail/callback",
        "GMAIL_SCHEDULER_SECRET": "fixture", "SCHEDULER_BACKEND_URL": "https://api.example.com",
        "STRIPE_SECRET_KEY": "sk_live_fixture", "STRIPE_WEBHOOK_SECRET": "whsec_fixture",
        "STRIPE_PRICE_ID": "price_fixture", "OPENAI_MODEL_PRIMARY": "terra",
        "WORKER_HEALTH_HOST": "127.0.0.1", "WORKER_HEALTH_PORT": "8025",
        "WORKER_HEALTH_URL": "http://127.0.0.1:8025", "GMAIL_SYNC_INTERVAL_SECONDS": "300",
        "WORKER_MAX_BACKOFF_SECONDS": "3600", "MONITORING_WEBHOOK_URL": "https://alerts.example.com",
        "ACCOUNT_AUDIT_RETENTION_DAYS": "365",
        "OPENAI_MODEL_ESCALATION": "sol", "OPENAI_MODEL_STANDARD": "sol",
        "AI_COMPANY_MONTHLY_TOKENS": "10000", "AI_COMPANY_MONTHLY_USD": "5",
        "AI_MONTHLY_GENERATION_LIMIT": "100",
        "AI_MODEL_MAX_RATES_JSON": '{"terra":{"input":2,"output":12},"sol":{"input":4,"output":20}}',
    }


def set_production(monkeypatch):
    for name, value in production_values().items():
        monkeypatch.setenv(name, value)


@pytest.mark.parametrize("origin", ["*", "http://example.com", "https://example.com/path", "https://user:pass@example.com", ""])
def test_production_cors_rejects_unsafe_origin(monkeypatch, origin):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", origin)
    with pytest.raises(RuntimeError):
        cors_origins()


def test_production_missing_settings_stops(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="settings are missing"):
        validate_production()


def test_production_ai_budget_requires_every_configured_model(monkeypatch):
    set_production(monkeypatch)
    monkeypatch.setenv("AI_MODEL_MAX_RATES_JSON", '{"terra":{"input":2,"output":12}}')
    with pytest.raises(RuntimeError, match="AI production budget settings are invalid"):
        validate_production()
    monkeypatch.setenv("AI_MODEL_MAX_RATES_JSON", '{"terra":{"input":2,"output":12},"sol":{"input":4,"output":20}}')
    validate_production()
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fixture")
    with pytest.raises(RuntimeError, match="Production billing settings are invalid"):
        validate_production()
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_fixture")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://api.example.com/gmail/callback")
    with pytest.raises(RuntimeError, match="Production provider endpoints are invalid"):
        validate_production()
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://api.example.com/gmail/callback")
    monkeypatch.setenv("AI_MONTHLY_GENERATION_LIMIT", "0")
    with pytest.raises(RuntimeError, match="AI production budget settings are invalid"):
        validate_production()
    monkeypatch.setenv("AI_MONTHLY_GENERATION_LIMIT", "100")
    monkeypatch.delenv("AI_COMPANY_MONTHLY_USD")
    with pytest.raises(RuntimeError, match="Required AI production settings are missing"):
        validate_production()


def test_production_provider_settings_fail_closed(monkeypatch):
    set_production(monkeypatch)
    names = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "FRONTEND_URL", "BACKEND_URL", "CORS_ORIGINS",
             "OAUTH_STATE_SECRET", "GMAIL_TOKEN_ENCRYPTION_KEYS", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
             "GOOGLE_REDIRECT_URI", "GMAIL_SCHEDULER_SECRET", "SCHEDULER_BACKEND_URL",
             "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID",
             "WORKER_HEALTH_HOST", "WORKER_HEALTH_PORT", "WORKER_HEALTH_URL",
             "GMAIL_SYNC_INTERVAL_SECONDS", "WORKER_MAX_BACKOFF_SECONDS",
             "MONITORING_WEBHOOK_URL", "ACCOUNT_AUDIT_RETENTION_DAYS")
    for name in ("GOOGLE_CLIENT_ID", "GMAIL_SCHEDULER_SECRET", "STRIPE_WEBHOOK_SECRET"):
        old = production_values()[name]
        monkeypatch.delenv(name)
        with pytest.raises(RuntimeError, match="Required production settings are missing"):
            validate_production()
        monkeypatch.setenv(name, old)


@pytest.mark.parametrize("name,value", [
    ("SUPABASE_URL", "https://127.0.0.1"),
    ("FRONTEND_URL", "https://localhost"),
    ("BACKEND_URL", "https://127.0.0.1"),
    ("GOOGLE_REDIRECT_URI", "https://localhost/gmail/callback"),
    ("SCHEDULER_BACKEND_URL", "http://127.0.0.1:8000"),
])
def test_production_rejects_loopback_and_mismatched_endpoints(monkeypatch, name, value):
    set_production(monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError):
        validate_production()


def test_production_rejects_test_billing_and_extra_cors(monkeypatch):
    set_production(monkeypatch)
    monkeypatch.setenv("STRIPE_MODE", "test")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fixture")
    with pytest.raises(RuntimeError, match="approved live billing"):
        validate_production()
    set_production(monkeypatch)
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://other.example.com")
    with pytest.raises(RuntimeError, match="only FRONTEND_URL"):
        validate_production()


def test_production_rejects_missing_monitoring_and_unsafe_worker_defaults(monkeypatch):
    set_production(monkeypatch)
    monkeypatch.setenv("MONITORING_WEBHOOK_URL", "http://alerts.example.com")
    with pytest.raises(RuntimeError, match="monitoring endpoints"):
        validate_production()
    set_production(monkeypatch)
    monkeypatch.setenv("GMAIL_SYNC_INTERVAL_SECONDS", "0")
    with pytest.raises(RuntimeError, match="operational limits"):
        validate_production()
