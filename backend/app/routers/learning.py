from fastapi import APIRouter, Depends, HTTPException

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.core.company_context import get_current_company_id
from app.repositories.learning_repository import LearningRepository
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


def get_service() -> LearningService:
    try:
        return LearningService(LearningRepository(db=get_supabase_client()))
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/events")
def record_learning_event(payload: dict, company_id: str = Depends(get_current_company_id)):
    service = get_service()
    return service.record(
        company_id=company_id,
        event_type=payload.get("event_type", "unknown"),
        payload=payload,
    )
