from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def current_user(user=Depends(get_current_user)):
    # Authentication errors are handled by the dependency.  Do not wrap this
    # value-only response in an exception handler that could echo provider or
    # token diagnostics to the client.
    user_id = user.get("sub") or user.get("id") or ""
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    try:
        rows = (
            get_supabase_client()
            .table("profiles")
            .select("company_id")
            .eq("user_id", user_id)
            .limit(2)
            .execute()
            .data
            or []
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Account state temporarily unavailable") from None
    company_id = rows[0].get("company_id") if len(rows) == 1 else None
    return {
        "authenticated": True,
        "user": user,
        "company_id": company_id,
        "onboarding_completed": bool(company_id),
    }


@router.post("/login")
def login_stub():
    return {"message": "Login is handled by Supabase Auth on frontend."}


@router.post("/register")
def register_stub():
    return {"message": "Register is handled by Supabase Auth on frontend."}


@router.post("/logout")
def logout_stub():
    return {"message": "Logout is handled by Supabase Auth on frontend."}
