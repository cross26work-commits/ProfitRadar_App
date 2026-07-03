from fastapi import APIRouter, Header
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/self-evaluation", tags=["self-evaluation"])


def _num(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


@router.post("/run")
def run_self_evaluation(
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    events_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .execute()
    )

    judgements_res = (
        db.table("ai_judgements")
        .select("*")
        .eq("company_id", x_company_id)
        .execute()
    )

    events = events_res.data or []
    judgements = judgements_res.data or []

    judgement_map = {}
    for judgement in judgements:
        event_id = judgement.get("profit_event_id")
        if event_id and event_id not in judgement_map:
            judgement_map[event_id] = judgement

    evaluated = []

    for event in events:
        actual_profit = _num(event.get("actual_profit"))
        estimated_profit = _num(event.get("estimated_profit"))
        judgement = judgement_map.get(event.get("id"))

        if actual_profit <= 0:
            continue

        diff = actual_profit - estimated_profit

        if estimated_profit <= 0:
            accuracy = 0
        else:
            accuracy = max(0, round(100 - (abs(diff) / estimated_profit * 100), 1))

        success = actual_profit > 0

        learning_payload = {
            "company_id": x_company_id,
            "customer_id": event.get("customer_id"),
            "profit_event_id": event.get("id"),
            "event_type": "ai_self_evaluation",
            "input_data": {
                "profit_event": event,
                "ai_judgement": judgement,
            },
            "result_data": {
                "estimated_profit": estimated_profit,
                "actual_profit": actual_profit,
                "diff": diff,
                "accuracy": accuracy,
                "success": success,
            },
            "success": success,
            "actual_profit": actual_profit,
        }

        learning = db.table("learning_logs").insert(learning_payload).execute()

        evaluated.append({
            "profit_event_id": event.get("id"),
            "estimated_profit": estimated_profit,
            "actual_profit": actual_profit,
            "diff": diff,
            "accuracy": accuracy,
            "success": success,
            "learning_event": (learning.data or [None])[0],
        })

    if not evaluated:
        message = "評価対象の実利益データはまだありません。"
    else:
        avg_accuracy = round(
            sum(item["accuracy"] for item in evaluated) / len(evaluated),
            1,
        )
        message = f"AI自己評価を{len(evaluated)}件実行しました。平均精度は{avg_accuracy}%です。"

    return {
        "company_id": x_company_id,
        "count": len(evaluated),
        "items": evaluated,
        "message": message,
    }


@router.get("/summary")
def self_evaluation_summary(
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    res = (
        db.table("learning_logs")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("event_type", "ai_self_evaluation")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )

    rows = res.data or []

    accuracies = []
    success_count = 0

    for row in rows:
        result = row.get("result_data") or {}
        if result.get("accuracy") is not None:
            accuracies.append(float(result.get("accuracy") or 0))
        if result.get("success") is True:
            success_count += 1

    avg_accuracy = round(sum(accuracies) / len(accuracies), 1) if accuracies else 0

    return {
        "company_id": x_company_id,
        "count": len(rows),
        "success_count": success_count,
        "avg_accuracy": avg_accuracy,
        "message": f"AI判断の平均精度は{avg_accuracy}%です。",
    }
