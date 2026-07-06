from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase_client import get_supabase_client
from app.core.company_context import get_current_company_id

router = APIRouter(prefix="/profit-events", tags=["profit-events"])


@router.patch("/{event_id}/actual-profit")
def update_actual_profit(
    event_id: str,
    payload: dict,
    company_id: str = Depends(get_current_company_id),
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
        .eq("company_id", company_id)
        .eq("id", event_id)
        .execute()
    )

    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="profit event not found")

    event = rows[0]

    # Phase6-6:
    # 実利益更新後、顧客単位の推定利益・実利益を再集計
    customer_id = event.get("customer_id")

    if customer_id:
        related_events = (
            db.table("profit_events")
            .select("estimated_profit,actual_profit")
            .eq("company_id", company_id)
            .eq("customer_id", customer_id)
            .execute()
        )

        customer_events = related_events.data or []

        total_estimated_profit = sum(
            int(row.get("estimated_profit") or 0)
            for row in customer_events
        )

        total_actual_profit = sum(
            int(row.get("actual_profit") or 0)
            for row in customer_events
        )

        db.table("customers").update({
            "total_estimated_profit": total_estimated_profit,
            "total_actual_profit": total_actual_profit,
        }).eq(
            "company_id", company_id
        ).eq(
            "id", customer_id
        ).execute()

    timeline_payload = {
        "company_id": company_id,
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
        "company_id": company_id,
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
