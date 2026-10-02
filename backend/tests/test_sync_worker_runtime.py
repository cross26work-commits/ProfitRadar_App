import json
import socket
from unittest.mock import Mock

import pytest

from scripts import sync_worker


def configured(monkeypatch):
    monkeypatch.setenv("SCHEDULER_BACKEND_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("GMAIL_SCHEDULER_SECRET", "fixture-secret")


def test_tick_success_tracks_heartbeat_without_secret(monkeypatch, capsys):
    configured(monkeypatch)
    response = Mock()
    response.json.return_value = {"processed": 2, "succeeded": 1, "failed": 1,
                                  "busy": 0, "deferred": 0, "ignored": "secret"}
    state = sync_worker.WorkerState()
    assert sync_worker.tick(state, request=Mock(return_value=response))
    snapshot = state.snapshot()
    assert snapshot["status"] == "degraded" and snapshot["last_batch_failed"] == 1
    assert snapshot["last_success_at"] is None
    output = capsys.readouterr().out
    assert "fixture-secret" not in output and "ignored" not in output
    assert json.loads(output)["event"] == "sync_batch"
    assert json.loads(output)["severity"] == "warning"


def test_tick_failure_is_bounded_and_redacted(monkeypatch, capsys):
    configured(monkeypatch)
    state = sync_worker.WorkerState()
    assert not sync_worker.tick(state, request=Mock(side_effect=RuntimeError("token-secret")))
    assert state.snapshot()["consecutive_failures"] == 1
    output = capsys.readouterr().out
    assert "token-secret" not in output
    assert json.loads(output)["severity"] == "error"
    assert sync_worker.backoff_seconds(1, 300, 3600) == 300
    assert sync_worker.backoff_seconds(8, 300, 3600) == 3600


@pytest.mark.parametrize("url", ["", "http://api.example.com", "https://user:pass@example.com"])
def test_scheduler_configuration_fails_closed(monkeypatch, url):
    monkeypatch.setenv("SCHEDULER_BACKEND_URL", url)
    monkeypatch.setenv("GMAIL_SCHEDULER_SECRET", "fixture")
    with pytest.raises(RuntimeError, match="Invalid scheduler"):
        sync_worker.scheduler_config()


def test_health_server_rejects_non_loopback(monkeypatch):
    monkeypatch.setenv("WORKER_HEALTH_HOST", "0.0.0.0")
    with pytest.raises(RuntimeError, match="exposure"):
        sync_worker.start_health_server(sync_worker.WorkerState())


def test_railway_private_health_requires_production_and_matching_port(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("WORKER_HEALTH_EXPOSURE", "railway-private")
    monkeypatch.setenv("WORKER_HEALTH_HOST", "0.0.0.0")
    monkeypatch.setenv("WORKER_HEALTH_PORT", "8025")
    monkeypatch.setenv("PORT", "8026")
    with pytest.raises(RuntimeError, match="must match PORT"):
        sync_worker.start_health_server(sync_worker.WorkerState())


def test_railway_private_health_binds_matching_platform_port(monkeypatch):
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("WORKER_HEALTH_EXPOSURE", "railway-private")
    monkeypatch.setenv("WORKER_HEALTH_HOST", "0.0.0.0")
    monkeypatch.setenv("WORKER_HEALTH_PORT", str(port))
    monkeypatch.setenv("PORT", str(port))
    server = sync_worker.start_health_server(sync_worker.WorkerState())
    try:
        assert server.server_address[1] == port
    finally:
        server.shutdown()
        server.server_close()
