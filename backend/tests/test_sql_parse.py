"""Postgres grammar only, NOT schema/RLS/PLpgSQL runtime evidence."""
from pathlib import Path
import pytest
pglast=pytest.importorskip("pglast",reason="Optional PostgreSQL grammar parser absent")
ROOT=Path(__file__).resolve().parents[2]
FILES=sorted((ROOT/"supabase/migrations").glob("*.sql"))+[ROOT/"supabase/release_readonly_tenant_audit.sql",ROOT/"backend/tests/isolated/baseline.sql"]


@pytest.mark.parametrize("path",FILES,ids=lambda p:p.name)
def test_sql_grammar(path):
    assert pglast.parse_sql(path.read_text(encoding="utf-8"))
