from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


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
        "message": "Auth is stubbed for Phase3"
    }
