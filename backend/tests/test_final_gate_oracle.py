"""Approved remote metadata fixtures against the unchanged SQL comparison logic.

Only observed_oracle is supplied from independent JSON; owners/columns/policies/ACL
checks still query the isolated DB. This is not a real remote-equivalent DB proof:
capture contains body digests, not reconstructable source for all functions.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from test_final_gate import disposable_db, evaluate, GATE

ROOT = Path(__file__).resolve().parents[2]
ORACLE = ROOT / 'docs/remote_schema_forward_oracle_snapshot_20260916.json'
DIGEST = '1819D3032106DF74FC7709CC0C88EE6D0C0992F941BF74A16617A65515E751E9'


def oracle():
    raw = ORACLE.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == DIGEST
    return json.loads(raw)


def fixture_query(observed):
    source = GATE.read_text(encoding='utf-8')
    before, rest = source.split('observed_oracle AS (', 1)
    _, after = rest.split('\n),\nq0 AS (', 1)
    return (before + "observed_oracle AS (SELECT key AS oracle_name,value AS snapshot "
            "FROM pg_catalog.jsonb_each($fixture$" + json.dumps(observed) +
            "$fixture$::jsonb)\n),\nq0 AS (" + after)


def test_exact_embedded_independent_oracle():
    expected = oracle()
    source = GATE.read_text(encoding='utf-8')
    assert json.loads(source.split('$remote_oracle$')[1]) == expected
    assert len(expected['security_definers']) == 11
    assert sum(f['present'] for f in expected['functions']) == 11
    assert len(expected['functions']) == 25
    assert sum(t['present'] for t in expected['target_tables']) == 20
    assert len(expected['target_tables']) == 31


def test_approved_metadata_baseline_final_pass(disposable_db):
    result = evaluate(disposable_db, source_override=fixture_query(oracle()))
    assert result['FINAL'] == 'PASS'
    assert result['V2-B onboarding'] == 'KNOWN_REMEDIABLE'


@pytest.mark.parametrize('kind', [
    'constraint', 'index', 'function_md5', 'function_config', 'function_acl',
    'new_function', 'security_definer', 'view', 'trigger', 'event',
    'sync_row', 'table_presence', 'table_absence', 'billing_presence',
    'sync_column', 'sync_constraint', 'sync_index', 'profiles_identity',
])
def test_exact_oracle_drift_stops(disposable_db, kind):
    data = copy.deepcopy(oracle())
    if kind == 'constraint':
        data['constraints'][0]['convalidated'] = False
    elif kind == 'index':
        data['indexes'][0]['indisvalid'] = False
    elif kind.startswith('function_'):
        row = next(f for f in data['functions'] if f['present'])
        key = {'function_md5':'prosrc_md5', 'function_config':'proconfig', 'function_acl':'proacl'}[kind]
        row[key] = 'unexpected'
    elif kind == 'new_function':
        next(f for f in data['functions'] if not f['present'])['present'] = True
    elif kind == 'security_definer':
        data['security_definers'].append({'function_signature':'public.unexpected()'})
    elif kind in ('view', 'trigger'):
        data[{'view':'views', 'trigger':'triggers'}[kind]].append({'name':'unexpected'})
    elif kind == 'event':
        data['event_trigger'][0]['evtenabled'] = 'D'
    elif kind == 'sync_row':
        data['gmail_sync_runs']['total_rows'] = 1
    elif kind in ('table_presence', 'table_absence'):
        row = next(t for t in data['target_tables'] if t['present'] == (kind == 'table_absence'))
        row['present'] = not row['present']
    elif kind == 'billing_presence':
        data['billing_runtime_config']['present'] = True
    elif kind == 'sync_column':
        data['gmail_sync_runs']['columns'][0]['is_nullable'] = True
    elif kind == 'sync_constraint':
        data['gmail_sync_runs']['constraints'][0]['convalidated'] = False
    elif kind == 'sync_index':
        data['gmail_sync_runs']['indexes'][0]['indisready'] = False
    elif kind == 'profiles_identity':
        data['profiles_identity']['null_user_id_count'] = 1
    result = evaluate(disposable_db, source_override=fixture_query(data))
    assert result['FINAL'] == 'STOP'
    assert any(status == 'STOP' for key,status in result.items() if key.startswith('oracle '))
