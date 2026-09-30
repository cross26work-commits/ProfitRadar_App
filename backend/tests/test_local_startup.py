from pathlib import Path


ROOT = Path(__file__).parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"
BRIDGE = MIGRATIONS / "202609060001_reply_logs_gmail_bridge.sql"


def test_reply_log_bridge_precedes_first_gmail_index_consumer():
    names = sorted(path.name for path in MIGRATIONS.glob("*.sql"))
    assert names.index("202607020001_profit_radar_core.sql") < names.index(BRIDGE.name)
    assert names.index(BRIDGE.name) < names.index("202609070001_release_candidate_safety.sql")


def test_reply_log_bridge_is_additive_and_contract_checked():
    sql = BRIDGE.read_text(encoding="utf-8").lower()
    assert "add column if not exists gmail_message_id text" in sql
    assert "add column if not exists gmail_thread_id text" in sql
    assert "reply_logs gmail column contract mismatch" in sql
    for destructive in ("drop column", "drop table", "truncate ", "delete from", "update public"):
        assert destructive not in sql


def test_local_launcher_is_loopback_only_and_excludes_only_remote_forward_repairs():
    source = (ROOT / "scripts" / "start-profit-radar.ps1").read_text(encoding="utf-8")
    assert "supabase@2.117.0" in source
    assert "project=profit-radar-disposable" in source
    assert "127.0.0.1:54421" in source
    assert "127.0.0.1:8031" in source
    assert "127.0.0.1:3101" in source
    assert "^2026091[45]0001_remote_schema_forward" in source
    assert "*> $null" in source
    assert "function Invoke-NativeChecked" in source
    assert "$nativeExitCode = $LASTEXITCODE" in source
    assert "PSNativeCommandUseErrorActionPreference = $false" in source
    for forbidden in ("db push", "db reset", "system prune", "volume prune", "down -v"):
        assert forbidden not in source.lower()


def test_local_stop_preserves_volumes_and_targets_only_owned_processes():
    source = (ROOT / "scripts" / "stop-profit-radar.ps1").read_text(encoding="utf-8").lower()
    assert "--workdir $runtime" in source
    assert "commandline" in source
    for forbidden in ("--no-backup", "-v", "volume rm", "system prune", "remove-item"):
        assert forbidden not in source


def test_local_supabase_ports_are_separate_from_disposable_fixture():
    config = (ROOT / "supabase" / "config.toml").read_text(encoding="utf-8")
    assert 'project_id = "profit-radar-local"' in config
    assert "port = 54421" in config
    assert "port = 54422" in config
    assert "shadow_port = 54420" in config
