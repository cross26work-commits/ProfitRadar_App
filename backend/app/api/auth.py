from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def current_user(user=Depends(get_current_user)):
    try:
        return {
            "authenticated": True,
            "user": user,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"/auth/me failed: {error}",
        )


@router.post("/login")
def login_stub():
    return {"message": "Login is handled by Supabase Auth on frontend."}


@router.post("/register")
def register_stub():
    return {"message": "Register is handled by Supabase Auth on frontend."}


@router.post("/logout")
def logout_stub():
    return {"message": "Logout is handled by Supabase Auth on frontend."}
