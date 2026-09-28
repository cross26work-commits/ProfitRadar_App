"""Read-only syntax checks and opt-in disposable PostgreSQL execution.

The source lacks exact inventory oracles: baseline FINAL must stay STOP, not a
synthetic PASS. Local fixture mutation is transactional and never targets remote.
"""
import os
import re
import hashlib
import json
from pathlib import Path
import pytest
from pglast import parse_sql, scan, parser
from scripts import validate_forward_local as validation

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / 'supabase/remote_schema_forward_final_gate.sql'


def test_select_only_and_no_mutating_tokens():
    source = GATE.read_text(encoding='utf-8')
    statements = parse_sql(source)
    assert len(statements) == 1
    assert all(type(s.stmt).__name__ == 'SelectStmt' for s in statements)
    forbidden = {'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE',
                 'DO', 'BEGIN', 'COMMIT', 'ROLLBACK', 'LOCK', 'SET', 'GRANT', 'REVOKE',
                 'CALL', 'COPY', 'INTO'}
    assert not ({t.name for t in scan(source)} & forbidden)
    from test_oracle_capture import walk
    tree = json.loads(parser.parse_sql_json(source))
    for node in walk(tree):
        if 'FuncCall' in node:
            names = [part['String']['sval'] for part in node['FuncCall']['funcname']]
            assert len(names) == 1 or names[0] == 'pg_catalog'
    assert 'pg_advisory' not in source


def test_authoritative_source_unchanged():
    assert hashlib.sha256((ROOT / 'supabase/remote_schema_forward_preflight.sql').read_bytes()).hexdigest() == 'ede597b72ee224447ffc8d6de835c3af90bfc8f439374cf2bdb34920d730d8d5'
    assert hashlib.sha256(validation.FORWARD_V2.read_bytes()).hexdigest() == 'b5152c99e1368989fb35203686db3d29cb395362c1e8282d6f1f9bbb8edc86f0'
    validation.remote_policy_oracle()
    validation.validate_canonical_capture()


@pytest.fixture(scope='module')
def disposable_db():
    if os.getenv('FINAL_GATE_LOCAL_TEST') != 'allow-disposable-fixtures':
        pytest.skip('Explicit disposable local fixture approval required')
    validation.validate_target(True)
    original = validation.sql
    captured = {}

    class BaselineReady(Exception):
        pass

    def intercept(db, source, *args, **kwargs):
        if '-- Profit Radar remote forward v2' in source:
            captured['db'] = db
            raise BaselineReady()
        return original(db, source, *args, **kwargs)

    # Reuse the existing guarded NEW database builder, stop BEFORE migration.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(validation, 'sql', intercept)
        with pytest.raises(BaselineReady):
            validation.run(True, v2=True)
    assert captured['db'].startswith('pr_forward_')
    return captured['db']


def evaluate(db, mutation='', source_override=None):
    source = (source_override or GATE.read_text(encoding='utf-8')).strip().removesuffix(';')
    before = validation.schema_fingerprint(db)
    result = validation.sql(db, 'begin; set role postgres; set local search_path=pg_catalog,public; ' + mutation +
                            " select json_agg(g) from (" + source + ") g; rollback;")
    assert validation.schema_fingerprint(db) == before
    rows = json.loads(result)
    assert all(set(row) == {'gate', 'status', 'detail'} for row in rows)
    assert len([row for row in rows if row['gate'] == 'FINAL']) == 1
    return {row['gate']: row['status'] for row in rows}


def test_baseline_cannot_fabricate_missing_approval(disposable_db):
    result = evaluate(disposable_db)
    assert result['V2-0 owner_user_id'] == 'PASS'
    assert result['V2-A checkout'] == 'PASS'
    assert result['V2-B onboarding'] == 'KNOWN_REMEDIABLE'
    assert result['policies'] == 'PASS'
    assert result['gmail_sync_runs columns/rows'] == 'PASS'
    assert result['gmail_sync_runs constraints'] == 'PASS'
    assert result['FINAL'] == 'STOP'  # Repository fixture is NOT the approved remote metadata.


@pytest.mark.parametrize('mutation,gate', [
    ('alter table public.companies alter column owner_user_id drop default;', 'V2-0 owner_user_id'),
    ('create policy unexpected on public.profiles for select to authenticated using(true);', 'policies'),
    ("insert into public.gmail_sync_runs(status) values('completed');", 'gmail_sync_runs columns/rows'),
    ('grant select on public.customers to authenticator;', 'ACL'),
    ('create table public.billing_checkout_attempts(unexpected text);', 'V2-A checkout'),
])
def test_known_drifts_stop(disposable_db, mutation, gate):
    result = evaluate(disposable_db, mutation)
    assert result[gate] == 'STOP'
    assert result['FINAL'] == 'STOP'


def test_canonical_whitespace_stops(disposable_db):
    definition = validation.sql(disposable_db, "select pg_get_functiondef('public.create_company_and_profile(text,text)'::regprocedure);")
    assert '\ndeclare\n' in definition
    result = evaluate(disposable_db, definition.replace('\ndeclare\n', '\ndeclare\n ', 1) + ';')
    assert result['V2-B onboarding'] == 'STOP'


def test_approved_checkout_structure(disposable_db):
    result = evaluate(disposable_db, """create table public.billing_checkout_attempts(
        company_id uuid primary key references public.companies(id),
        attempt_id uuid not null, session_id text, created_at timestamptz not null default now());""")
    assert result['V2-A checkout'] == 'PASS'
