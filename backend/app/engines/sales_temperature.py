from typing import Any


def build_sales_update(ai_result: dict[str, Any], current_event: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Phase6-5:
    AI判定結果を profit_events 更新用データへ変換する。
    DBカラム追加なしで既存構造に反映する。
    """
    current_event = current_event or {}

    is_lead = bool(ai_result.get("is_lead"))
    risk_level = ai_result.get("risk_level") or current_event.get("risk_level") or "中"
    next_action = ai_result.get("next_action") or current_event.get("next_action") or "状況確認"
    estimated_profit = int(ai_result.get("estimated_profit") or current_event.get("estimated_profit") or 0)

    hot_lead = False
    status = current_event.get("status") or "open"

    if is_lead and risk_level == "高":
        hot_lead = True
        status = "open"
    elif is_lead and risk_level == "中":
        hot_lead = bool(current_event.get("hot_lead")) or False
        status = "open"

    if not is_lead and next_action == "保存不要":
        status = current_event.get("status") or "open"

    return {
        "risk_level": risk_level,
        "next_action": next_action,
        "estimated_profit": estimated_profit,
        "hot_lead": hot_lead,
        "status": status,
    }
