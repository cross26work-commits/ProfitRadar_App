from fastapi import APIRouter, Header, Query
from app.repositories.timeline_repository import TimelineRepository
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("")
def list_timeline(
    customer_id: str | None = Query(default=None),
    x_company_id: str = Header(default="demo-company"),
):
    service = TimelineService(TimelineRepository(db=None))
    return service.list_timeline(company_id=x_company_id, customer_id=customer_id)


@router.post("")
def create_timeline_event(payload: dict, x_company_id: str = Header(default="demo-company")):
    service = TimelineService(TimelineRepository(db=None))
    return service.create_event(company_id=x_company_id, payload=payload)
