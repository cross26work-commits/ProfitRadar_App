from fastapi import APIRouter, Query

from app.services.dashboard_home_service import build_dashboard_home

router = APIRouter(prefix="/dashboard", tags=["dashboard-home"])


@router.get("/home")
def dashboard_home(company_id: str = Query(...)):
    return build_dashboard_home(company_id=company_id)
