from unittest.mock import Mock
from types import SimpleNamespace
import pytest
from scripts.maintenance import run


def database():
    db=Mock();q=Mock();db.table.return_value=q
    for name in ('select','in_','neq','eq','lt','gte'):getattr(q,name).return_value=q
    q.execute.return_value=SimpleNamespace(count=0)
    return db


def test_maintenance_default_does_not_delete_or_call_provider(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL','http://localhost:54321')
    db=database();result=run(db,'http://localhost:54321')
    assert not result['retention_applied'] and not result['operator_review_required']
    db.rpc.assert_not_called()
    for call in db.table.return_value.select.call_args_list:assert call.kwargs=={'count':'exact','head':True}
    assert {'recent_sync_failures','stuck_sync_runs','recent_ai_failures'} <= result['counts'].keys()
    assert db.table.return_value.gte.call_count==2


def test_retention_requires_explicit_policy_and_target(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL','http://localhost:54321');monkeypatch.delenv('RETENTION_SWEEP_APPROVED',raising=False)
    db=database()
    with pytest.raises(ValueError,match='Target mismatch'):run(db,'https://wrong.invalid',True)
    with pytest.raises(ValueError,match='approval'):run(db,'http://localhost:54321',True)
    db.rpc.assert_not_called()
    monkeypatch.setenv('RETENTION_SWEEP_APPROVED','true');monkeypatch.setenv('SUPPORT_RETENTION_DAYS','365');db.rpc.return_value.execute.return_value.data=0
    assert run(db,'http://localhost:54321',True)['purged_audit_jobs']==0
    assert db.rpc.call_args_list[-2].args == ('purge_expired_deletion_audit',{})
    assert db.rpc.call_args_list[-1].args == ('purge_expired_support_records',{'p_retention_days':365})


def test_monitoring_emits_only_fixed_counts_without_secrets(monkeypatch):
    from scripts import maintenance
    monkeypatch.setenv('MONITORING_WEBHOOK_URL','https://receiver.invalid/private-fixture-path')
    sender=Mock(return_value=SimpleNamespace(status_code=204))
    monkeypatch.setattr(maintenance.requests,'post',sender)
    result={'operator_review_required':True,'counts':{key:1 for key in ('unresolved_sends','pending_deletions','reserved_ai','old_company_locks','recent_sync_failures','stuck_sync_runs','recent_ai_failures','unhandled_support','unknown_support_replies')},'private':'must-not-send'}
    maintenance.notify(result)
    payload=sender.call_args.kwargs['json']
    assert 'private' not in str(payload)
    assert sender.call_args.kwargs['allow_redirects'] is False
    assert sender.call_args.kwargs['timeout']==5
    sender.return_value.status_code=302
    with pytest.raises(ValueError,match='not confirmed'):maintenance.notify(result)


def test_monitoring_missing_destination_fails_without_network(monkeypatch):
    from scripts import maintenance
    monkeypatch.delenv('MONITORING_WEBHOOK_URL',raising=False)
    sender=Mock();monkeypatch.setattr(maintenance.requests,'post',sender)
    with pytest.raises(ValueError,match='HTTPS'):maintenance.notify({})
    sender.assert_not_called()
