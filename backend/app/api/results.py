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


@router.get("/insights")
def results_insights():
    return {
        "items": [
            "高利益案件の返信速度が改善傾向",
            "見積段階の放置が利益損失に直結",
            "SMS切り替え候補あり"
        ],
        "message": "results insights loaded"
    }
