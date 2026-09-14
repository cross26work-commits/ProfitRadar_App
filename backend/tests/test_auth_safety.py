import pytest
import requests
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.core import auth
from app.api.onboarding import OnboardingRequest
from pydantic import ValidationError
import jwt
import time


@pytest.mark.parametrize("authorization", [None, "Bearer invalid", "Basic invalid"])
def test_onboarding_http_rejection_before_any_database_or_provider(monkeypatch, authorization):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import onboarding

    monkeypatch.setattr(auth, "SUPABASE_JWT_SECRET", "synthetic-test-only-key-32-characters")
    monkeypatch.setattr(auth, "SUPABASE_URL", "http://localhost:54321")
    calls = []

    def forbidden(*args, **kwargs):
        calls.append("unexpected side effect")
        raise AssertionError("Rejected request must not access database or provider")

    monkeypatch.setattr(onboarding, "get_supabase_client", forbidden)
    monkeypatch.setattr(auth.requests, "get", forbidden)
    app = FastAPI()
    app.include_router(onboarding.router)
    headers = {"Authorization": authorization} if authorization else {}
    response = TestClient(app).post("/onboarding", headers=headers,
                                    json={"company_name": "Fixture", "name": "Fixture"})
    assert response.status_code == 401
    assert response.json() in ({"detail": "Not authenticated"}, {"detail": "Invalid token"})
    assert calls == []


def test_provider_errors_do_not_expose_details(monkeypatch):
    monkeypatch.setattr(auth, "SUPABASE_JWT_SECRET", "")
    monkeypatch.setattr(auth, "SUPABASE_URL", "http://localhost:54321")
    def fail(*args, **kwargs):
        raise requests.ConnectionError("PRIVATE_PROVIDER_DETAIL")
    monkeypatch.setattr(auth.requests, "get", fail)
    with pytest.raises(HTTPException) as error:
        auth.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials="fixture"))
    assert error.value.status_code == 503
    assert error.value.detail == "Authentication temporarily unavailable"


@pytest.mark.parametrize("field", ["company_id", "user_id", "role"])
def test_client_identity_fields_rejected(field):
    with pytest.raises(ValidationError):
        OnboardingRequest(company_name="Fixture", name="Fixture", **{field: "forbidden"})


@pytest.mark.parametrize("changed", [{"role": "service_role"}, {"aud": "other"}, {"iss": "https://other/auth/v1"}, {"exp": 1}, {"sub": ""}])
def test_signed_invalid_claims_rejected(monkeypatch, changed):
    monkeypatch.setattr(auth, "SUPABASE_JWT_SECRET", "synthetic-test-only-key-32-characters")
    monkeypatch.setattr(auth, "SUPABASE_URL", "http://localhost:54321")
    claims = {"sub": "test-user", "role": "authenticated", "aud": "authenticated", "iss": "http://localhost:54321/auth/v1", "exp": int(time.time())+60}
    claims.update(changed)
    token = jwt.encode(claims, "synthetic-test-only-key-32-characters", algorithm="HS256")
    with pytest.raises(HTTPException) as error:
        auth.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    assert error.value.status_code == 401


def test_hmac_requires_expiry_and_accepts_valid_subject(monkeypatch):
    key="synthetic-test-only-key-32-characters"
    monkeypatch.setattr(auth,"SUPABASE_JWT_SECRET",key);monkeypatch.setattr(auth,"SUPABASE_URL","http://localhost:54321")
    claims={"sub":"fixture","role":"authenticated","aud":"authenticated","iss":"http://localhost:54321/auth/v1"}
    credentials=lambda c:HTTPAuthorizationCredentials(scheme="Bearer",credentials=jwt.encode(c,key,algorithm="HS256"))
    with pytest.raises(HTTPException) as error:auth.get_current_user(credentials(claims))
    assert error.value.status_code==401
    assert auth.get_current_user(credentials({**claims,"exp":int(time.time())+60}))["sub"]=="fixture"


def test_oauth_state_requires_expiry_and_rejects_wrong_purpose(monkeypatch):
    from app.api.gmail import _decode_oauth_state,_create_oauth_state
    key="synthetic-test-only-key-32-characters"
    monkeypatch.setenv("OAUTH_STATE_SECRET",key)
    assert _decode_oauth_state(_create_oauth_state("fixture"))=="fixture"
    for claims in ({"company_id":"fixture","purpose":"gmail_oauth","iat":int(time.time())},
                   {"company_id":"fixture","purpose":"wrong","iat":int(time.time()),"exp":int(time.time())+60}):
        with pytest.raises(HTTPException) as error:_decode_oauth_state(jwt.encode(claims,key,algorithm="HS256"))
        assert error.value.status_code==400
