from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.api.auth as auth_api


class _ProfileQuery:
    def __init__(self, rows=None, error=None):
        self._rows = rows or []
        self._error = error

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self._error:
            raise self._error
        return SimpleNamespace(data=self._rows)


class _ProfileClient:
    def __init__(self, rows=None, error=None):
        self._query = _ProfileQuery(rows, error)

    def table(self, name):
        assert name == "profiles"
        return self._query


def test_auth_me_returns_authenticated_identity_and_completed_onboarding(monkeypatch):
    user = {"sub": "fixture-user", "email": "fixture@example.invalid"}
    monkeypatch.setattr(
        auth_api,
        "get_supabase_client",
        lambda: _ProfileClient([{"company_id": "fixture-company"}]),
    )

    assert auth_api.current_user(user) == {
        "authenticated": True,
        "user": user,
        "company_id": "fixture-company",
        "onboarding_completed": True,
    }


def test_auth_me_marks_onboarding_incomplete_when_profile_is_absent(monkeypatch):
    user = {"sub": "fixture-user", "email": "fixture@example.invalid"}
    monkeypatch.setattr(
        auth_api,
        "get_supabase_client",
        lambda: _ProfileClient([]),
    )

    response = auth_api.current_user(user)

    assert response["company_id"] is None
    assert response["onboarding_completed"] is False


def test_auth_me_fails_closed_without_exposing_database_error(monkeypatch):
    user = {"sub": "fixture-user", "email": "fixture@example.invalid"}
    monkeypatch.setattr(
        auth_api,
        "get_supabase_client",
        lambda: _ProfileClient(error=RuntimeError("synthetic secret diagnostic")),
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_api.current_user(user)

    assert exc_info.value.status_code == 503
    assert "synthetic" not in str(exc_info.value.detail)


def test_auth_route_does_not_embed_exception_text_in_client_detail():
    source = __import__("inspect").getsource(auth_api.current_user)

    assert "detail=f" not in source
    assert "str(" not in source
