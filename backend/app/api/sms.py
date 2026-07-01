from fastapi import APIRouter

router = APIRouter(prefix="/sms", tags=["sms"])


@router.get("/status")
def sms_status():
    return {
        "enabled": False,
        "provider": "twilio",
        "status": "not_configured",
        "message": "SMS adapter is reserved for future Twilio integration"
    }


@router.get("/health")
def sms_health():
    return {
        "status": "ok",
        "service": "sms-adapter",
        "provider": "twilio",
        "enabled": False
    }
