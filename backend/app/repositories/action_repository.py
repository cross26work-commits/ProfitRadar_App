from app.core.supabase_client import get_supabase_client


def get_open_profit_events(company_id: str, limit: int = 50) -> list[dict]:
    db = get_supabase_client()

    result = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data or []


def get_ai_judgements(company_id: str, limit: int = 100) -> list[dict]:
    db = get_supabase_client()

    result = (
        db.table("ai_judgements")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data or []


def get_customers(company_id: str, limit: int = 500) -> list[dict]:
    db = get_supabase_client()

    result = (
        db.table("customers")
        .select("*")
        .eq("company_id", company_id)
        .limit(limit)
        .execute()
    )

    return result.data or []


def get_recent_timeline(company_id: str, limit: int = 300) -> list[dict]:
    db = get_supabase_client()

    result = (
        db.table("timeline")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data or []
