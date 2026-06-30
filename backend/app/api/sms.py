from fastapi import APIRouter

router = APIRouter(prefix="/sms", tags=["sms"])

@router.get("/status")
def sms_status():
    return {
        "connected": False,
        "message": "sms api ready"
    }
