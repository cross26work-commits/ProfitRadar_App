from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.core.company_context import get_current_company_id
from app.repositories.timeline_repository import TimelineRepository
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/timeline", tags=["timeline"])


def get_service() -> TimelineService:
    try:
        return TimelineService(TimelineRepository(db=get_supabase_client()))
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("")
def list_timeline(
    customer_id: str | None = Query(default=None),
    company_id: str = Depends(get_current_company_id),
):
    service = get_service()
    return service.list_timeline(company_id=company_id, customer_id=customer_id)


@router.post("")
def create_timeline_event(
    payload: dict,
    company_id: str = Depends(get_current_company_id),
):
    service = get_service()
    return service.create_event(company_id=company_id, payload=payload)
