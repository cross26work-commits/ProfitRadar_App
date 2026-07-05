from typing import Any

from fastapi import Depends, HTTPException

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_client


def _extract_user_id(user: dict[str, Any]) -> str:
    return (
        user.get("sub")
        or user.get("id")
        or user.get("user", {}).get("id")
        or ""
    )


def get_current_company_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    user_id = _extract_user_id(user)

    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")

    db = get_supabase_client()

    res = (
        db.table("profiles")
        .select("company_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=403, detail="Company profile not found")

    company_id = rows[0].get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company ID not found")

    return company_id
