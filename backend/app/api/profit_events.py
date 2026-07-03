from fastapi import APIRouter, Header, HTTPException
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/profit-events", tags=["profit-events"])


@router.patch("/{event_id}/actual-profit")
def update_actual_profit(
    event_id: str,
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    try:
        actual_profit = int(payload.get("actual_profit") or 0)
    except Exception:
        raise HTTPException(status_code=400, detail="actual_profit must be number")

    status = payload.get("status") or "closed"

    res = (
        db.table("profit_events")
        .update({
            "actual_profit": actual_profit,
            "status": status,
        })
        .eq("company_id", x_company_id)
        .eq("id", event_id)
        .execute()
    )

    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="profit event not found")

    event = rows[0]

    timeline_payload = {
        "company_id": x_company_id,
        "customer_id": event.get("customer_id"),
        "profit_event_id": event.get("id"),
        "event_type": "actual_profit_saved",
        "channel": "system",
        "title": "実利益を記録",
        "description": f"{event.get('title') or '案件'} / 実回収 ¥{actual_profit:,}",
        "amount": actual_profit,
        "metadata": {
            "source": "actual_profit_update",
            "status": status,
        },
    }

    timeline = db.table("timeline").insert(timeline_payload).execute()

    learning_payload = {
        "company_id": x_company_id,
        "customer_id": event.get("customer_id"),
        "profit_event_id": event.get("id"),
        "event_type": "actual_profit_saved",
        "input_data": event,
        "result_data": {
            "actual_profit": actual_profit,
            "status": status,
        },
        "success": True,
        "actual_profit": actual_profit,
    }

    learning = db.table("learning_logs").insert(learning_payload).execute()

    return {
        "saved": True,
        "profit_event": event,
        "timeline_event": (timeline.data or [None])[0],
        "learning_event": (learning.data or [None])[0],
    }
