from fastapi import APIRouter, Header, HTTPException, Query

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
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
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    service = get_service()
    return service.list_timeline(company_id=x_company_id, customer_id=customer_id)


@router.post("")
def create_timeline_event(payload: dict, x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a")):
    service = get_service()
    return service.create_event(company_id=x_company_id, payload=payload)
