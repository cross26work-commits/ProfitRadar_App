from argparse import Namespace
from unittest.mock import Mock
from uuid import uuid4
import pytest
from scripts.resolve_provider_uncertainty import run,validate


def args():
    return Namespace(company=str(uuid4()),expected_id=str(uuid4()),expected_url="http://localhost:54321",kind="gmail-revoke",apply=False,workers_stopped=False,provider_reviewed=False,operator=None,ticket=None)


def test_recovery_readonly_never_requests_tokens(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL","http://localhost:54321")
    db=Mock();db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data=[]
    assert run(db,args())["changed"] is False
    db.table.return_value.select.assert_called_once_with("id,status")
    db.rpc.assert_not_called()


def test_recovery_requires_exact_target_and_both_attestations(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL","http://localhost:54321")
    a=args();a.expected_url="https://other.invalid"
    with pytest.raises(ValueError,match="Target mismatch"):validate(a)
    a=args();a.apply=True;a.workers_stopped=True;a.operator="operator";a.ticket="ticket"
    db=Mock()
    with pytest.raises(ValueError,match="attestations"):run(db,a)
    db.rpc.assert_not_called()
    a.provider_reviewed=True;db.rpc.return_value.execute.return_value.data=True
    assert run(db,a)=={"resolved":True,"budget_refunded":False,"mail_sent":False}
