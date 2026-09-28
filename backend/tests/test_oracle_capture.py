"""One-shot metadata capture safety; optional explicitly approved local DB check."""
import hashlib
import json
from pathlib import Path

import pytest
from pglast import parse_sql, parser, scan
from scripts import validate_forward_local as validation
from test_final_gate import disposable_db

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / 'supabase/remote_schema_forward_oracle_capture.sql'
ALLOWED_FUNCTIONS = {
    'pg_get_constraintdef', 'pg_get_indexdef', 'pg_get_function_identity_arguments',
    'pg_get_function_result', 'pg_get_userbyid', 'md5', 'has_function_privilege',
    'format', 'format_type', 'pg_get_triggerdef', 'pg_get_expr', 'to_regclass',
    'jsonb_agg', 'to_jsonb', 'jsonb_build_object', 'count',
}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def assert_safe(source):
    statements = parse_sql(source)
    assert len(statements) == 1 and type(statements[0].stmt).__name__ == 'SelectStmt'
    forbidden = {'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE',
                 'DO', 'CALL', 'BEGIN', 'COMMIT', 'ROLLBACK', 'LOCK', 'SET', 'GRANT',
                 'REVOKE', 'COPY', 'INTO', 'EXPLAIN'}
    assert not ({token.name for token in scan(source)} & forbidden)
    tree = json.loads(parser.parse_sql_json(source))
    calls = [node['FuncCall'] for node in walk(tree) if 'FuncCall' in node]
    for call in calls:
        names = [part['String']['sval'] for part in call['funcname']]
        assert len(names) == 2 and names[0] == 'pg_catalog'
        assert names[1] in ALLOWED_FUNCTIONS
        if names[1] == 'jsonb_agg':
            assert call.get('agg_order'), 'Every aggregate array needs explicit ordering'
    raw_refs = [node['ColumnRef'] for node in walk(tree) if 'ColumnRef' in node
                and any(part.get('String', {}).get('sval') == 'prosrc' for part in node['ColumnRef']['fields'])]
    md5_refs = [arg['ColumnRef'] for call in calls
                if call['funcname'][-1]['String']['sval'] == 'md5'
                for arg in call['args'] if 'ColumnRef' in arg]
    assert raw_refs == md5_refs, 'Raw body can only be the immediate argument of md5'
    assert statements[0].stmt.sortClause


def test_single_select_no_mutations_or_business_rpc():
    assert_safe(CAPTURE.read_text(encoding='utf-8'))


@pytest.mark.parametrize('unsafe', [
    'select public.onboard_user();',
    'select pg_catalog.pg_get_functiondef(1);',
    'select p.prosrc from pg_catalog.pg_proc p;',
    'with changed as (delete from public.profiles returning *) select * from changed;',
    'select pg_catalog.jsonb_agg(1);',
])
def test_safety_checker_rejects_unsafe_queries(unsafe):
    with pytest.raises(AssertionError):
        assert_safe(unsafe)


def test_protected_files_unchanged():
    expected = {
        'supabase/migrations/202609150001_remote_schema_forward_v2.sql':
            'B5152C99E1368989FB35203686DB3D29CB395362C1E8282D6F1F9BBB8EDC86F0',
        'supabase/remote_schema_forward_preflight.sql':
            'EDE597B72EE224447FFC8D6DE835C3AF90BFC8F439374CF2BDB34920D730D8D5',
    }
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper() == digest


def test_target_lists_match_authoritative_source():
    tree = json.loads(parser.parse_sql_json(CAPTURE.read_text(encoding='utf-8')))
    ctes = {n['CommonTableExpr']['ctename']: n['CommonTableExpr']
            for n in walk(tree) if 'CommonTableExpr' in n}
    def values(name):
        return {node['A_Const']['sval']['sval'] for node in walk(ctes[name]['ctequery'])
                if 'A_Const' in node and 'sval' in node['A_Const']}
    tables, functions = values('target_tables'), values('expected_functions')
    assert len(tables) == 31 and len(functions) == 25
    preflight = (ROOT / 'supabase/remote_schema_forward_preflight.sql').read_text(encoding='utf-8')
    import re
    expected_tables = set(re.findall(r"\('([^']+)'\)", preflight.split('WITH targets(name) AS (VALUES ', 1)[1].split('\nSELECT', 1)[0]))
    expected_functions = set(re.findall(r"\('([^']+)'\)", preflight.split('WITH expected(name) AS (VALUES ', 1)[1].split('\nSELECT', 1)[0]))
    assert tables == expected_tables and functions == expected_functions


def test_local_capture_stable_and_no_persistent_change(disposable_db):
    source = CAPTURE.read_text(encoding='utf-8').strip().removesuffix(';')
    before = validation.schema_fingerprint(disposable_db)
    def capture():
        return validation.sql(disposable_db, 'select pg_catalog.jsonb_agg(r order by oracle_name) from (' + source + ') r;')
    first = capture()
    assert capture() == first
    assert validation.schema_fingerprint(disposable_db) == before
    result = {r['oracle_name']: r['snapshot'] for r in json.loads(first)}
    assert len(result) == 11
    assert len(result['target_tables']) == 31
    assert len(result['functions']) == 25
    assert sum(not f['present'] for f in result['functions']) >= 14
    assert len(result['gmail_sync_runs']['columns']) == 9
    assert result['gmail_sync_runs']['total_rows'] == 0
    assert result['profiles_identity'] == {'null_user_id_count': 0, 'duplicate_user_id_groups': 0}
    assert result['billing_runtime_config'] == {'present': False}
    for f in result['functions']:
        assert 'prosrc' not in f
        assert f['prosrc_md5'] is None or len(f['prosrc_md5']) == 32
