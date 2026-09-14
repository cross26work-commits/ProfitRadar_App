import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class SupabaseConfigError(RuntimeError):
    pass


@lru_cache
def get_supabase_service_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_role_key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for backend database access"
        )

    return create_client(url, service_role_key)


@lru_cache
def get_supabase_anon_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not anon_key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_ANON_KEY are required for anonymous Supabase access"
        )

    return create_client(url, anon_key)


def get_supabase_client() -> Client:
    """Return the service-role client used by backend database operations."""

    return get_supabase_service_client()


def get_table(table_name: str) -> Any:
    return get_supabase_client().table(table_name)
