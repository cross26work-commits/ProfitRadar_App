from fastapi import APIRouter

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/gmail")
def gmail_settings():
    return {
        "connected": False,
        "label": "接続状態",
        "description": "Gmail OAuthは未接続です。",
        "provider": "gmail",
    }


@router.get("/sms")
def sms_settings():
    return {
        "connected": False,
        "label": "SMS状態",
        "description": "Twilio SMSは未接続です。",
        "provider": "twilio",
    }


@router.get("/app")
def app_settings():
    return {
        "company": "未設定",
        "plan": "未契約",
        "message": "settings loaded",
    }
