from fastapi import APIRouter, Query

from app.services.action_service import get_today_top_actions

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/top")
def top_actions(
    company_id: str = Query(...),
    limit: int = Query(5, ge=1, le=20),
):
    actions = get_today_top_actions(company_id=company_id, limit=limit)

    return {
        "company_id": company_id,
        "count": len(actions),
        "actions": actions,
    }
