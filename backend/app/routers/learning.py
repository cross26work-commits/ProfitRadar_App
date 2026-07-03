from fastapi import APIRouter, Header, HTTPException

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.repositories.learning_repository import LearningRepository
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


def get_service() -> LearningService:
    try:
        return LearningService(LearningRepository(db=get_supabase_client()))
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/events")
def record_learning_event(payload: dict, x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a")):
    service = get_service()
    return service.record(
        company_id=x_company_id,
        event_type=payload.get("event_type", "unknown"),
        payload=payload,
    )
