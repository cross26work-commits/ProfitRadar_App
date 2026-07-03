from fastapi import APIRouter, Header, HTTPException
from postgrest.exceptions import APIError

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.repositories.learning_repository import LearningRepository
from app.repositories.profit_event_repository import ProfitEventRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.timeline_repository import TimelineRepository
from app.services.event_service import EventService
from app.services.revenue_service import RevenueService
from app.services.customer_resolver_service import CustomerResolverService

router = APIRouter(prefix="/revenue", tags=["revenue"])


@router.post("/analyze")
def analyze_revenue(
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    service = RevenueService()
    return service.analyze(company_id=x_company_id, payload=payload)


@router.post("/analyze-and-save")
def analyze_and_save_revenue(
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    try:
        db = get_supabase_client()

        event_service = EventService(
            timeline_repository=TimelineRepository(db=db),
            learning_repository=LearningRepository(db=db),
        )

        service = RevenueService(
            repository=ProfitEventRepository(db=db),
            event_service=event_service,
            customer_resolver=CustomerResolverService(
                repository=CustomerRepository(db=db),
            ),
        )

        return service.analyze_and_save(company_id=x_company_id, payload=payload)
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
