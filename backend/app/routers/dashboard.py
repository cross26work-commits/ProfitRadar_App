from fastapi import APIRouter, HTTPException, Depends
from postgrest.exceptions import APIError

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.core.company_context import get_current_company_id
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_service() -> DashboardService:
    try:
        return DashboardService(DashboardRepository(db=get_supabase_client()))
    except SupabaseConfigError:
        raise HTTPException(status_code=503, detail="Database configuration unavailable") from None


@router.get("/summary")
def dashboard_summary(
    company_id: str = Depends(get_current_company_id),
):
    service = get_service()

    try:
        return service.get_summary(company_id=company_id)
    except APIError:
        raise HTTPException(status_code=503, detail="Dashboard temporarily unavailable") from None
