from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_client


router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_name: str
    name: str


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

        return {
            "success": True,
            "result": result.data,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Onboarding temporarily unavailable",
        ) from None
