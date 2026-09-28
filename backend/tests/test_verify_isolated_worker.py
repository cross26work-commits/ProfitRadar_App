from unittest.mock import Mock

import pytest

from scripts import verify_isolated_worker


def test_isolated_worker_requires_explicit_fixture_gate(monkeypatch):
    validate = Mock()
    monkeypatch.setattr(verify_isolated_worker, "validate_target", validate)
    with pytest.raises(RuntimeError, match="Explicit"):
        verify_isolated_worker.run(False)
    validate.assert_not_called()


def test_isolated_worker_environment_is_loopback_and_disables_dotenv():
    environment = verify_isolated_worker.child_environment(
        {"service_role": "service-fixture", "anon": "anon-fixture"}, "scheduler-fixture")
    assert environment["SUPABASE_URL"] == "http://127.0.0.1:54321"
    assert environment["SCHEDULER_BACKEND_URL"] == "http://127.0.0.1:8022"
    assert environment["PYTHON_DOTENV_DISABLED"] == "1"
    assert environment["APP_ENV"] == "test" and environment["STRIPE_MODE"] == "test"
