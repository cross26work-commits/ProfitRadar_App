from unittest.mock import Mock

import pytest

from scripts import runtime_probe


def configure(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    monkeypatch.setenv("BACKEND_URL", "https://api.example.com")
    monkeypatch.setenv("WORKER_HEALTH_URL", "http://127.0.0.1:8025")


def test_probe_passes_only_when_all_targets_pass(monkeypatch):
    configure(monkeypatch)
    response = Mock(status_code=200)
    response.json.return_value = {"status": "healthy", "last_batch_failed": 0}
    get = Mock(return_value=response)
    result = runtime_probe.check(get)
    assert result["severity"] == "info"
    assert set(result["checks"].values()) == {"pass"}
    assert get.call_count == 5


def test_probe_reports_degraded_worker_as_failure(monkeypatch):
    configure(monkeypatch)
    response = Mock(status_code=200)
    response.json.return_value = {"status": "degraded", "last_batch_failed": 1}
    result = runtime_probe.check(Mock(return_value=response))
    assert result["severity"] == "critical"
    assert result["checks"]["worker_heartbeat"] == "fail"


def test_probe_redacts_failure_and_marks_critical(monkeypatch):
    configure(monkeypatch)
    result = runtime_probe.check(Mock(side_effect=RuntimeError("secret-value")))
    assert result["severity"] == "critical"
    assert "secret-value" not in str(result)
    assert set(result["checks"].values()) == {"fail"}


@pytest.mark.parametrize("name,value", [
    ("FRONTEND_URL", "http://app.example.com"),
    ("BACKEND_URL", "https://user:pass@api.example.com"),
    ("WORKER_HEALTH_URL", "http://remote.example.com"),
])
def test_probe_rejects_unsafe_endpoints(monkeypatch, name, value):
    configure(monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match="configuration invalid"):
        runtime_probe.check()


def test_notify_contains_only_fixed_results(monkeypatch):
    monkeypatch.setenv("MONITORING_WEBHOOK_URL", "https://alerts.example.com")
    post = Mock(return_value=Mock(status_code=204))
    runtime_probe.notify({"event": "runtime_probe", "severity": "critical",
                          "checks": {"backend_health": "fail"}}, post)
    payload = post.call_args.kwargs["json"]
    assert payload == {"event": "runtime_probe", "severity": "critical",
                       "checks": {"backend_health": "fail"}}
