from typing import Any
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_client


router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_name: str
    name: str
    business_use_confirmed: bool


def _extract_user_id(user: dict[str, Any]) -> str:
    return (
        user.get("sub")
        or user.get("id")
        or user.get("user", {}).get("id")
        or ""
    )


def _extract_email(user: dict[str, Any]) -> str:
    return (
        user.get("email")
        or user.get("user", {}).get("email")
        or ""
    )


@router.post("")
def onboard(
    payload: OnboardingRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    user_id = _extract_user_id(user)
    email = _extract_email(user)

    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")

    company_name = payload.company_name.strip()
    name = payload.name.strip()

    if not company_name:
        raise HTTPException(
            status_code=400,
            detail="Company name is required",
        )
    if payload.business_use_confirmed is not True:
        raise HTTPException(status_code=422, detail="Business use confirmation is required")

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required",
        )

    db = get_supabase_client()

    try:
        result = db.rpc(
            "onboard_user",
            {
                "p_user_id": user_id,
                "p_company_name": company_name,
                "p_name": name,
                "p_email": email,
            },
        ).execute()

        rows = result.data or []
        if not rows:
            raise RuntimeError("Onboarding result unavailable")
        company_id = rows[0].get("company_id") if isinstance(rows, list) else None
        if not company_id:
            raise RuntimeError("Onboarding result unavailable")
        db.table("company_business_consents").upsert({
            "company_id": company_id,
            "user_id": user_id,
            "terms_version": os.getenv("TERMS_VERSION", "2026-09-29"),
        }, on_conflict="company_id").execute()
        return {
            "success": True,
            "result": rows,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Onboarding temporarily unavailable",
        ) from None
