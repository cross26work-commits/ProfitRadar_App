import pytest
from app.core.runtime_settings import cors_origins, validate_production


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
