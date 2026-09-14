from types import SimpleNamespace
from unittest.mock import Mock
from app.services import send_operations as operations


def test_transport_timeout_is_unknown_never_retried():
    db = Mock()
    db.table.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
    provider = Mock(side_effect=TimeoutError())
    result = operations.execute_once(db,"a","key",provider)
    assert result["status"] == "unknown" and result["sent"] is False
    assert provider.call_count == 1
    db.rpc.assert_not_called()


def test_provider_accepted_but_database_failure_is_unknown():
    db = Mock()
    db.rpc.return_value.execute.side_effect = RuntimeError("database unavailable")
    provider = Mock(return_value={"id":"message","threadId":"thread"})
    assert operations.execute_once(db,"a","key",provider)["status"] == "unknown"
    assert provider.call_count == 1


def test_success_requires_database_finalize():
    db = Mock()
    provider = Mock(return_value={"id":"message","threadId":"thread"})
    assert operations.execute_once(db,"a","key",provider)["sent"] is True
    db.rpc.assert_called_once()


def test_identity_is_tenant_bound_and_changes_with_content():
    key=operations.identity("a","event","test@example.invalid","subject","body")
    assert key==operations.identity("a","event","test@example.invalid","subject","body")
    assert key!=operations.identity("b","event","test@example.invalid","subject","body")
    assert key!=operations.identity("a","event","test@example.invalid","subject","edited")
