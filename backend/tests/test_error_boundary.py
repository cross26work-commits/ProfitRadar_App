import pytest
from fastapi import FastAPI,HTTPException
from fastapi.testclient import TestClient
from app.core.error_boundary import install
from app.core.runtime_settings import validate_production


@pytest.mark.parametrize("error",[RuntimeError("private secret"),HTTPException(500,"private secret")])
def test_provider_error_not_in_response_or_log(error,caplog):
    app=FastAPI();install(app)
    @app.get("/failure")
    def fail():raise error
    response=TestClient(app,raise_server_exceptions=False).get("/failure?code=private-secret")
    assert response.status_code in {500,503}
    assert "private" not in response.text+caplog.text
    assert response.json()["correlation_id"]==response.headers["x-correlation-id"]


@pytest.mark.parametrize("environment",["","prod","staging"])
def test_unspecified_or_incomplete_environment_fails_closed(monkeypatch,environment):
    monkeypatch.setenv("APP_ENV",environment)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY",raising=False)
    with pytest.raises(RuntimeError):validate_production()
