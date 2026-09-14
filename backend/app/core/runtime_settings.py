"""Validate production startup before accepting requests; no secret values in errors."""
import os
from urllib.parse import urlsplit


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


def validate_production():
    from app.core.billing_mode import configured_mode
    configured_mode()  # A live gate is invalid in development/test, too.
    environment=os.getenv("APP_ENV", "").strip().lower()
    if environment not in {"development","test","staging","production"}:
        raise RuntimeError("APP_ENV must be explicitly configured")
    if environment in {"development","test"}:
        return
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "FRONTEND_URL", "CORS_ORIGINS", "OAUTH_STATE_SECRET", "GMAIL_TOKEN_ENCRYPTION_KEYS")
    if any(not os.getenv(name, "").strip() for name in required):
        raise RuntimeError("Required production settings are missing")
    if any(urlsplit(os.environ[name]).scheme != "https" for name in ("SUPABASE_URL", "FRONTEND_URL")):
        raise RuntimeError("Production endpoints require HTTPS")
    cors_origins()
