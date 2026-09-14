from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.services import ai_judge_service


def test_foreign_ai_reference_denied_before_provider(monkeypatch):
    db=Mock(); q=Mock(); db.table.return_value=q
    q.select.return_value=q;q.eq.return_value=q;q.limit.return_value=q
    q.execute.return_value=SimpleNamespace(data=[])
    provider=Mock(side_effect=AssertionError("Must not analyze foreign record"))
    monkeypatch.setattr(ai_judge_service,"judge_email",provider)
    service=ai_judge_service.AIJudgeService(SimpleNamespace(db=db))
    with pytest.raises(HTTPException) as exc:
        service.judge("a",{"body":"synthetic","customer_id":"b-customer"})
    assert exc.value.status_code==404
    provider.assert_not_called();db.rpc.assert_not_called()
