"""No provider/network requests. Exercises the public error boundary."""
import pytest
from types import SimpleNamespace
from unittest.mock import Mock
from fastapi import HTTPException
from app.api import gmail


def test_status_selects_only_safe_company_scoped_metadata(monkeypatch):
    projections = {
        "gmail_connections": "id,email,status,created_at",
        "gmail_sync_cursors": "mode,last_page_at,last_successful_sync",
        "gmail_company_sync_runs": "status,started_at,finished_at,detected_count,error_code",
    }
    queries = {}
    def table(name):
        query = Mock()
        for method in ("select", "eq", "order", "limit"):
            getattr(query, method).return_value = query
        query.execute.return_value = SimpleNamespace(data=[])
        queries[name] = query
        return query
    db = Mock()
    db.table.side_effect = table
    monkeypatch.setattr(gmail, "get_supabase_client", lambda: db)
    result = gmail.gmail_status("fixture-company-a")
    assert result["connected"] is False
    assert result["connection"] is None
    assert set(queries) == set(projections)
    for name, query in queries.items():
        query.select.assert_called_once_with(projections[name])
        query.eq.assert_any_call("company_id", "fixture-company-a")
    # Projection is an explicit allowlist; no token or message/cursor payload is read.
    assert "token" not in repr(result)


def test_callback_provider_exception_is_redacted(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    def fail(*args):
        raise RuntimeError("synthetic-private-provider-detail")
    monkeypatch.setattr(gmail, "_complete_gmail_callback", fail)
    response = gmail.gmail_callback("synthetic-code", "synthetic-state", None)
    assert response.status_code == 302
    assert response.headers["location"] == "http://localhost:3000/settings/mail?gmail=oauth_failed"
    assert "synthetic" not in str(response.headers)


@pytest.mark.parametrize("environment", [None, "production", "staging"])
def test_send_test_disabled_before_db_access(monkeypatch, environment):
    if environment is None:
        monkeypatch.delenv("APP_ENV", raising=False)
    else:
        monkeypatch.setenv("APP_ENV", environment)
    def fail():
        pytest.fail("Disabled endpoint accessed database")
    monkeypatch.setattr(gmail, "get_supabase_client", fail)
    with pytest.raises(HTTPException) as error:
        gmail.gmail_send_test({}, "fixture-company")
    assert error.value.status_code == 404
