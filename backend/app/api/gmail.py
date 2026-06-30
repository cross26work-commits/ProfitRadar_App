from fastapi import APIRouter

router = APIRouter(prefix="/gmail", tags=["gmail"])

@router.get("/status")
def gmail_status():
    return {
        "connected": False,
        "message": "gmail api ready"
    }
