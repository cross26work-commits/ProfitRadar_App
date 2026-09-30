import pytest
from fastapi import HTTPException

import app.api.gmail as gmail_api


def _clear_oauth_environment(monkeypatch):
    for name in (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
    ):
        monkeypatch.delenv(name, raising=False)


def test_missing_local_oauth_configuration_has_a_safe_distinct_status(monkeypatch):
    _clear_oauth_environment(monkeypatch)
    monkeypatch.setenv("APP_ENV", "development")

    with pytest.raises(HTTPException) as exc_info:
        gmail_api._client_config()

    assert exc_info.value.status_code == 501
    assert "secret" not in str(exc_info.value.detail).lower()


def test_missing_production_oauth_configuration_has_a_safe_distinct_status(monkeypatch):
    _clear_oauth_environment(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(HTTPException) as exc_info:
        gmail_api._client_config()

    assert exc_info.value.status_code == 424
    assert "secret" not in str(exc_info.value.detail).lower()


def test_oauth_provider_construction_failure_is_redacted(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fixture-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fixture-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/gmail/callback")
    monkeypatch.setattr(gmail_api, "get_supabase_client", lambda: object())

    import app.services.billing as billing_service

    monkeypatch.setattr(billing_service, "require_use", lambda _db, _company: None)
    monkeypatch.setattr(
        gmail_api.Flow,
        "from_client_config",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("synthetic provider secret diagnostic")
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        gmail_api.gmail_auth_url("fixture-company")

    assert exc_info.value.status_code == 502
    assert "synthetic" not in str(exc_info.value.detail)
    assert "secret" not in str(exc_info.value.detail).lower()
