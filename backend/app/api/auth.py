from fastapi import APIRouter, Depends

from app.core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def current_user(user=Depends(get_current_user)):
    # Authentication errors are handled by the dependency.  Do not wrap this
    # value-only response in an exception handler that could echo provider or
    # token diagnostics to the client.
    return {
        "authenticated": True,
        "user": user,
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
