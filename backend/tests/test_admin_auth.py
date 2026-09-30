from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.core import admin_auth

ADMIN="00000000-0000-4000-8000-000000000001"
USER="00000000-0000-4000-8000-000000000002"

def test_admin_authority_is_verified_subject_allowlist_not_profile_role(monkeypatch):
    monkeypatch.setenv("SUPPORT_ADMIN_USER_IDS",ADMIN)
    assert admin_auth.require_support_admin({"sub":ADMIN,"user_metadata":{"role":"user"}})==ADMIN
    with pytest.raises(HTTPException) as error:
        admin_auth.require_support_admin({"sub":USER,"user_metadata":{"role":"admin"},"role":"admin"})
    assert error.value.status_code==403

def test_missing_or_invalid_admin_configuration_fails_closed(monkeypatch):
    for value in ("", "not-a-uuid"):
        monkeypatch.setenv("SUPPORT_ADMIN_USER_IDS",value)
        with pytest.raises(HTTPException) as error:admin_auth.require_support_admin({"sub":ADMIN})
        assert error.value.status_code==503
