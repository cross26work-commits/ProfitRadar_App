"""Validate production startup before accepting requests; no secret values in errors."""
import os
from urllib.parse import urlsplit


PRODUCTION_REQUIRED = (
    "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "FRONTEND_URL", "BACKEND_URL", "CORS_ORIGINS",
    "OAUTH_STATE_SECRET", "GMAIL_TOKEN_ENCRYPTION_KEYS", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI", "GMAIL_SCHEDULER_SECRET", "SCHEDULER_BACKEND_URL",
    "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID",
    "WORKER_HEALTH_HOST", "WORKER_HEALTH_PORT", "WORKER_HEALTH_URL", "WORKER_HEALTH_EXPOSURE",
    "GMAIL_SYNC_INTERVAL_SECONDS", "WORKER_MAX_BACKOFF_SECONDS",
    "MONITORING_WEBHOOK_URL", "ACCOUNT_AUDIT_RETENTION_DAYS",
    "SUPPORT_ADMIN_USER_IDS", "CONTACT_RATE_LIMIT_SECRET", "SUPPORT_RETENTION_DAYS",
    "SUPPORT_EMAIL_PROVIDER", "SUPPORT_EMAIL_FROM", "SUPPORT_EMAIL_VERIFIED_DOMAIN",
    "SUPPORT_EMAIL_SENDER_APPROVED", "SUPPORT_EMAIL_SMTP_HOST", "SUPPORT_EMAIL_SMTP_PORT",
    "SUPPORT_EMAIL_SMTP_USERNAME", "SUPPORT_EMAIL_SMTP_PASSWORD",
)
AI_MODEL_SETTINGS = (
    "OPENAI_MODEL_PRIMARY", "OPENAI_MODEL_ESCALATION", "OPENAI_MODEL_STANDARD",
)
AI_PRODUCTION_REQUIRED = (
    "OPENAI_API_KEY", "AI_MODEL_MAX_RATES_JSON", "AI_COMPANY_MONTHLY_TOKENS",
    "AI_COMPANY_MONTHLY_USD", "AI_MONTHLY_GENERATION_LIMIT", *AI_MODEL_SETTINGS,
)


def cors_origins():
    production = os.getenv("APP_ENV", "").lower() not in {"development","test"}
    raw = os.getenv("CORS_ORIGINS", "" if production else "http://localhost:3000,http://127.0.0.1:3000")
    origins = [value.strip() for value in raw.split(",") if value.strip()]
    if not origins:
        raise RuntimeError("CORS_ORIGINS must be explicitly configured")
    for origin in origins:
        parsed = urlsplit(origin)
        if (not parsed.hostname or parsed.username or parsed.password or parsed.query
                or parsed.fragment or parsed.path not in {"", "/"}
                or parsed.scheme not in ({"https"} if production else {"http", "https"})):
            raise RuntimeError("Invalid CORS origin configuration")
    return origins


def _origin(name, *, https_only, reject_loopback=False):
    parsed = urlsplit(os.environ[name])
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {"", "/"}
            or (https_only and parsed.scheme != "https")
            or (not https_only and parsed.scheme not in {"http", "https"})
            or (reject_loopback and parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"})):
        raise RuntimeError("Production endpoint configuration is invalid")
    return parsed


def validate_production():
    from app.core.billing_mode import configured_mode
    configured_mode()  # A live gate is invalid in development/test, too.
    environment=os.getenv("APP_ENV", "").strip().lower()
    if environment not in {"development","test","staging","production"}:
        raise RuntimeError("APP_ENV must be explicitly configured")
    if environment in {"development","test"}:
        return
    if any(not os.getenv(name, "").strip() for name in PRODUCTION_REQUIRED):
        raise RuntimeError("Required production settings are missing")
    production = environment == "production"
    supabase = _origin("SUPABASE_URL", https_only=True, reject_loopback=production)
    frontend = _origin("FRONTEND_URL", https_only=True, reject_loopback=production)
    backend = _origin("BACKEND_URL", https_only=True, reject_loopback=production)
    cors_origins()
    callback = urlsplit(os.environ["GOOGLE_REDIRECT_URI"])
    scheduler = urlsplit(os.environ["SCHEDULER_BACKEND_URL"])
    monitoring = urlsplit(os.environ["MONITORING_WEBHOOK_URL"])
    worker_health = urlsplit(os.environ["WORKER_HEALTH_URL"])
    private_worker = (os.environ["WORKER_HEALTH_EXPOSURE"] == "railway-private"
                      and os.environ["WORKER_HEALTH_HOST"] == "0.0.0.0"
                      and worker_health.scheme == "http"
                      and bool(worker_health.hostname)
                      and worker_health.hostname.endswith(".railway.internal"))
    if (callback.scheme != "https" or not callback.hostname or callback.path != "/gmail/callback"
            or callback.username or callback.password or callback.query or callback.fragment
            or not scheduler.hostname or scheduler.username or scheduler.password or scheduler.query or scheduler.fragment
            or scheduler.path not in {"", "/"}
            or (scheduler.scheme != "https" and not (scheduler.scheme == "http" and scheduler.hostname in {"localhost", "127.0.0.1"}))):
        raise RuntimeError("Production provider endpoints are invalid")
    if (monitoring.scheme != "https" or not monitoring.hostname or monitoring.username
            or monitoring.password or monitoring.query or monitoring.fragment
            or (not private_worker and (worker_health.scheme != "http" or worker_health.hostname not in {"localhost", "127.0.0.1"}))
            or worker_health.username or worker_health.password or worker_health.query or worker_health.fragment
            or worker_health.path not in {"", "/"}
            or (not private_worker and os.environ["WORKER_HEALTH_HOST"] not in {"localhost", "127.0.0.1"})):
        raise RuntimeError("Production monitoring endpoints are invalid")
    if production:
        for endpoint in (callback, scheduler):
            if endpoint.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
                raise RuntimeError("Production provider endpoints are invalid")
        if callback.scheme != backend.scheme or callback.netloc != backend.netloc:
            raise RuntimeError("Production Google callback must use BACKEND_URL")
        if scheduler.scheme != backend.scheme or scheduler.netloc != backend.netloc:
            raise RuntimeError("Production scheduler must use BACKEND_URL")
        if set(cors_origins()) != {frontend.geturl().rstrip("/")}:
            raise RuntimeError("Production CORS must contain only FRONTEND_URL")
    mode = os.getenv("STRIPE_MODE", "test")
    if production and mode != "live":
        raise RuntimeError("Production requires approved live billing mode")
    expected_prefixes = (f"sk_{mode}_", f"rk_{mode}_")
    if (not os.environ["STRIPE_SECRET_KEY"].startswith(expected_prefixes)
            or not os.environ["STRIPE_WEBHOOK_SECRET"].startswith("whsec_")
            or not os.environ["STRIPE_PRICE_ID"].startswith("price_")):
        raise RuntimeError("Production billing settings are invalid")
    # Paid AI calls must never start with an unpriced or unbounded model.
    from app.services.ai_budget import settings as ai_budget_settings
    from fastapi import HTTPException
    if any(not os.getenv(name, "").strip() for name in AI_PRODUCTION_REQUIRED):
        raise RuntimeError("Required AI production settings are missing")
    try:
        from uuid import UUID
        worker_port = int(os.environ["WORKER_HEALTH_PORT"])
        worker_interval = int(os.environ["GMAIL_SYNC_INTERVAL_SECONDS"])
        worker_backoff = int(os.environ["WORKER_MAX_BACKOFF_SECONDS"])
        retention_days = int(os.environ["ACCOUNT_AUDIT_RETENTION_DAYS"])
        support_retention_days = int(os.environ["SUPPORT_RETENTION_DAYS"])
        if (not 1 <= worker_port <= 65535 or not 5 <= worker_interval <= 3600
                or worker_backoff < worker_interval or worker_backoff > 86400
                or not 1 <= retention_days <= 3650 or not 1 <= support_retention_days <= 3650):
            raise ValueError()
        if private_worker and worker_health.port != worker_port:
            raise ValueError()
        admin_ids = [value.strip() for value in os.environ["SUPPORT_ADMIN_USER_IDS"].split(",") if value.strip()]
        if not admin_ids or any(str(UUID(value)) != value.lower() for value in admin_ids):
            raise ValueError()
    except ValueError:
        raise RuntimeError("Production operational limits are invalid") from None
    sender = os.environ["SUPPORT_EMAIL_FROM"].strip().lower()
    sender_domain = os.environ["SUPPORT_EMAIL_VERIFIED_DOMAIN"].strip().lower()
    if (len(os.environ["CONTACT_RATE_LIMIT_SECRET"]) < 24
            or os.environ["SUPPORT_EMAIL_PROVIDER"] != "smtp"
            or os.environ["SUPPORT_EMAIL_SENDER_APPROVED"] != "true"
            or "@" not in sender or sender.rsplit("@", 1)[1] != sender_domain
            or not sender_domain or os.environ["SUPPORT_EMAIL_SMTP_PORT"] not in {"465", "587"}):
        raise RuntimeError("Production support settings are invalid")
    try:
        generation_limit = int(os.environ["AI_MONTHLY_GENERATION_LIMIT"])
        if not 1 <= generation_limit <= 10000:
            raise ValueError()
        for name in AI_MODEL_SETTINGS:
            ai_budget_settings(os.environ[name])
    except (HTTPException, ValueError):
        raise RuntimeError("AI production budget settings are invalid") from None
