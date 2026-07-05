from fastapi import APIRouter, Depends

from app.services.dashboard_home_service import build_dashboard_home
from app.core.company_context import get_current_company_id

router = APIRouter(prefix="/dashboard", tags=["dashboard-home"])


@router.get("/home")
def dashboard_home(
    company_id: str = Depends(get_current_company_id),
):
    return build_dashboard_home(company_id=company_id)
