import pytest

from app.core import supabase_client


@pytest.fixture(autouse=True)
def clear_client_caches():
    supabase_client.get_supabase_service_client.cache_clear()
    supabase_client.get_supabase_anon_client.cache_clear()
    yield
    supabase_client.get_supabase_service_client.cache_clear()
    supabase_client.get_supabase_anon_client.cache_clear()


def test_backend_client_fails_closed_without_service_role_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test-key")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    def unexpected_create_client(*args, **kwargs):
        raise AssertionError("create_client must not be called")

    monkeypatch.setattr(supabase_client, "create_client", unexpected_create_client)

    with pytest.raises(supabase_client.SupabaseConfigError, match="SERVICE_ROLE_KEY"):
        supabase_client.get_supabase_client()


def test_backend_client_uses_only_service_role_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-test-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test-key")
    sentinel = object()
    calls = []

    def fake_create_client(url, key):
        calls.append((url, key))
        return sentinel

    monkeypatch.setattr(supabase_client, "create_client", fake_create_client)

    assert supabase_client.get_supabase_client() is sentinel
    assert calls == [("https://example.supabase.co", "service-test-key")]


def test_anon_client_is_explicit_and_separate(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-test-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test-key")
    created = {}

    def fake_create_client(url, key):
        client = object()
        created[key] = client
        return client

    monkeypatch.setattr(supabase_client, "create_client", fake_create_client)

    service_client = supabase_client.get_supabase_service_client()
    anon_client = supabase_client.get_supabase_anon_client()

    assert service_client is created["service-test-key"]
    assert anon_client is created["anon-test-key"]
    assert service_client is not anon_client
