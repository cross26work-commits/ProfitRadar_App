from pathlib import Path
SQL=(Path(__file__).parents[2]/"supabase/migrations/20260928153027_legal_support_admin.sql").read_text(encoding="utf-8")
def test_support_tables_are_rls_and_service_only():
    for table in ("support_requests","support_messages","support_internal_notes","support_audit_logs"):
        assert f"alter table public.{table} enable row level security" in SQL
    assert "revoke all on public.company_business_consents" in SQL
    assert "from public, anon, authenticated, service_role" in SQL
def test_trial_and_support_rpc_contracts():
    assert "interval '7 days','trial_pending'" in SQL
    assert "security definer set search_path=pg_catalog,pg_temp" in SQL
    assert "pg_advisory_xact_lock" in SQL and "p_idempotency_key" in SQL
