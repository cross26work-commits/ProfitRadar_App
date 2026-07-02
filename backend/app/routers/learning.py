from fastapi import APIRouter, Header
from app.repositories.learning_repository import LearningRepository
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post("/events")
def record_learning_event(payload: dict, x_company_id: str = Header(default="demo-company")):
    service = LearningService(LearningRepository(db=None))
    return service.record(
        company_id=x_company_id,
        event_type=payload.get("event_type", "unknown"),
        payload=payload,
    )
