from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (ROOT / "supabase/migrations/202609090001_p0_tenant_rls_onboarding.sql").read_text(encoding="utf-8")


def test_p0_migration_enables_rls_and_restricts_browser_business_access():
    assert "alter table public.customers enable row level security" in MIGRATION
    assert "revoke all on table public.companies, public.profiles, public.customers" in MIGRATION
    assert "on all tables in schema public" not in MIGRATION
    assert "grant select, insert, update, delete on table public.companies" in MIGRATION


def test_onboarding_rpc_is_service_role_only_and_has_safe_search_path():
    assert "security definer set search_path = pg_catalog, pg_temp" in MIGRATION
    assert "revoke all on function public.onboard_user" in MIGRATION
    assert "to service_role" in MIGRATION
    assert "pg_advisory_xact_lock" in MIGRATION
    assert "create unique index if not exists uq_profiles_user_id" in MIGRATION
    assert "i.indisvalid and i.indisready" in MIGRATION
    assert "i.indkey[0]=a.attnum" in MIGRATION
