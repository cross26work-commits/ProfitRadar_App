from unittest.mock import Mock
import pytest
from app.services import support_email

def test_development_delivery_is_suppressed_without_network(monkeypatch):
    monkeypatch.setenv("APP_ENV","test");smtp=Mock();monkeypatch.setattr(support_email.smtplib,"SMTP_SSL",smtp)
    result=support_email.send_plain_text(recipient="fixture@example.invalid",subject="subject",body="body")
    assert result.status=="suppressed";smtp.assert_not_called()

def test_production_missing_or_unapproved_sender_fails_closed(monkeypatch):
    monkeypatch.setenv("APP_ENV","production");monkeypatch.setenv("SUPPORT_EMAIL_PROVIDER","smtp")
    monkeypatch.setenv("SUPPORT_EMAIL_SENDER_APPROVED","false")
    with pytest.raises(RuntimeError,match="not approved"):
        support_email.send_plain_text(recipient="fixture@example.invalid",subject="subject",body="body")
