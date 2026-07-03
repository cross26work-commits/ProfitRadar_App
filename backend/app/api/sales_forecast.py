from fastapi import APIRouter, Header
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/sales-forecast", tags=["sales-forecast"])


def _num(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


@router.get("/summary")
def sales_forecast_summary(
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .execute()
    )

    rows = res.data or []

    estimated_profit = sum(_num(r.get("estimated_profit")) for r in rows)
    actual_profit = sum(_num(r.get("actual_profit")) for r in rows)
    open_profit = sum(
        _num(r.get("estimated_profit"))
        for r in rows
        if r.get("status") == "open"
    )
    closed_profit = sum(
        _num(r.get("actual_profit"))
        for r in rows
        if r.get("status") == "closed"
    )

    hot_open_profit = sum(
        _num(r.get("estimated_profit"))
        for r in rows
        if r.get("status") == "open" and r.get("hot_lead") is True
    )

    conservative_forecast = actual_profit + int(open_profit * 0.25)
    standard_forecast = actual_profit + int(open_profit * 0.5)
    aggressive_forecast = actual_profit + int(hot_open_profit * 0.8)

    return {
        "company_id": x_company_id,
        "actual_profit": actual_profit,
        "estimated_profit": estimated_profit,
        "open_profit": open_profit,
        "closed_profit": closed_profit,
        "hot_open_profit": hot_open_profit,
        "forecast": {
            "conservative": conservative_forecast,
            "standard": standard_forecast,
            "aggressive": aggressive_forecast,
        },
        "message": (
            f"現時点の実回収は{actual_profit:,}円。"
            f"標準着地見込みは{standard_forecast:,}円です。"
        ),
    }
