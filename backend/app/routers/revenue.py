from fastapi import APIRouter, Header
from app.services.revenue_service import RevenueService

router = APIRouter(prefix="/revenue", tags=["revenue"])


@router.post("/analyze")
def analyze_revenue(payload: dict, x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a")):
    service = RevenueService()
    return service.analyze(company_id=x_company_id, payload=payload)
