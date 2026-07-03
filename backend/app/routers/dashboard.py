from fastapi import APIRouter, Header, HTTPException
from postgrest.exceptions import APIError

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_service() -> DashboardService:
    try:
        return DashboardService(DashboardRepository(db=get_supabase_client()))
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/summary")
def dashboard_summary(
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    service = get_service()

    try:
        return service.get_summary(company_id=x_company_id)
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
