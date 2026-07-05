from fastapi import APIRouter, Depends, Query

from app.services.action_service import get_today_top_actions
from app.core.company_context import get_current_company_id

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/top")
def top_actions(
    company_id: str = Depends(get_current_company_id),
    limit: int = Query(5, ge=1, le=20),
):
    actions = get_today_top_actions(company_id=company_id, limit=limit)

    return {
        "company_id": company_id,
        "count": len(actions),
        "actions": actions,
    }
