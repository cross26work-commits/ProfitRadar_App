from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/judge")
def ai_judge():
    return {
        "message": "ai judge api ready"
    }
