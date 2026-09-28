"""Legacy profit-event write compatibility boundary.

Financial records, not profit_events.actual_profit, are the canonical source
of confirmed revenue, cost, payments and gross profit. Keep the old route for
explicit rejection so older clients cannot silently create split-brain data.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.company_context import get_current_company_id
from app.core.supabase_client import get_supabase_client


router = APIRouter(prefix="/profit-events", tags=["profit-events"])


@router.patch("/{event_id}/actual-profit")
def update_actual_profit(
    event_id: str,
    payload: dict,
    company_id: str = Depends(get_current_company_id),
):
    """Reject legacy writes after tenant check; use PUT /financials/{id}."""
    _ = payload
    rows = (get_supabase_client().table("profit_events").select("id")
            .eq("company_id", company_id).eq("id", event_id).limit(1).execute().data or [])
    if not rows:
        raise HTTPException(status_code=404, detail="profit event not found")
    raise HTTPException(status_code=409,
                        detail="Legacy profit update is unavailable; use financial records")
