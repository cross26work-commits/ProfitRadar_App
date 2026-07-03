from fastapi import APIRouter, Header
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/results", tags=["results"])


def _num(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


@router.get("/summary")
def results_summary(
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

    actual_profit = sum(_num(row.get("actual_profit")) for row in rows)
    estimated_profit = sum(_num(row.get("estimated_profit")) for row in rows)
    action_count = len(rows)

    recovery_rate = 0
    if estimated_profit > 0:
        recovery_rate = round((actual_profit / estimated_profit) * 100, 1)

    return {
        "actual_profit": actual_profit,
        "estimated_profit": estimated_profit,
        "action_count": action_count,
        "recovery_rate": recovery_rate,
        "message": "results summary loaded from Supabase",
    }


@router.get("/insights")
def results_insights(
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

    open_count = len([r for r in rows if r.get("status") == "open"])
    hot_count = len([r for r in rows if r.get("hot_lead") is True])
    high_risk_count = len([r for r in rows if str(r.get("risk_level")) == "高"])
    estimated_profit = sum(_num(r.get("estimated_profit")) for r in rows)

    items = [
        f"進行中の利益候補は{open_count}件",
        f"Hot Leadは{hot_count}件",
        f"高リスク案件は{high_risk_count}件",
        f"現在の見込利益は{estimated_profit:,}円",
    ]

    return {
        "items": items,
        "message": "results insights loaded from Supabase",
    }
