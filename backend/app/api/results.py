from fastapi import APIRouter
from app.schemas.result import ResultSummaryResponse

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/summary", response_model=ResultSummaryResponse)
def results_summary():
    return ResultSummaryResponse(
        actual_profit=240000,
        estimated_profit=820000,
        action_count=31,
        recovery_rate=29.2,
    )
