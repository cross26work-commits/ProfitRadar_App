from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    company_name: str
    name: str
    email: str
    password: str


@router.get("/me")
def current_user():
    return {
        "user": {
            "id": 1,
            "email": "demo@example.com",
            "name": "Demo User",
        },
        "company": {
            "id": 1,
            "name": "Demo Company",
            "role": "owner",
        },
        "authenticated": False,
        "message": "Auth is stubbed for Phase3",
    }


@router.post("/login")
def login(payload: LoginRequest):
    return {
        "authenticated": False,
        "message": "Login endpoint is stubbed for Phase3",
        "email": payload.email,
    }


@router.post("/register")
def register(payload: RegisterRequest):
    return {
        "authenticated": False,
        "message": "Register endpoint is stubbed for Phase3",
        "user": {
            "name": payload.name,
            "email": payload.email,
        },
        "company": {
            "name": payload.company_name,
        },
    }


@router.post("/logout")
def logout():
    return {
        "authenticated": False,
        "message": "Logout endpoint is stubbed for Phase3",
    }
