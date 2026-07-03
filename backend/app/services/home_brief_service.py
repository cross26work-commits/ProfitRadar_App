from app.services.action_service import get_today_top_actions


def _yen(value: int | None) -> str:
    return f"{int(value or 0):,}円"


def _select_brief_top_action(actions: list[dict]) -> dict | None:
    if not actions:
        return None

    named_actions = [
        action for action in actions
        if action.get("customer_name") and action.get("customer_name") != "顧客未設定"
    ]

    if named_actions:
        return named_actions[0]

    return actions[0]


def build_home_brief(company_id: str) -> dict:
    actions = get_today_top_actions(company_id=company_id, limit=5)

    total_estimated_profit = sum(int(a.get("estimated_profit") or 0) for a in actions)
    total_recoverable_profit = sum(int(a.get("recoverable_profit") or 0) for a in actions)

    high_risk_count = len([
        a for a in actions
        if str(a.get("risk_level") or "") in ["高", "high", "HIGH"]
    ])

    top = _select_brief_top_action(actions)

    if top:
        customer_name = top.get("customer_name") or "顧客未設定"
        title = top.get("title") or "営業対応候補"
        estimated_profit = _yen(top.get("estimated_profit"))
        reason = top.get("reason") or "利益化の可能性があるため"
        next_action = top.get("next_action") or "状況確認"

        ai_message = (
            f"本日の注目案件は「{customer_name}」です。"
            f"件名は「{title}」。"
            f"期待利益は{estimated_profit}。"
            f"判断理由は「{reason}」。"
            f"次の行動は「{next_action}」です。"
        )
    else:
        ai_message = "本日すぐ対応すべき営業はまだ検出されていません。"

    return {
        "company_id": company_id,
        "summary": {
            "top_action_count": len(actions),
            "total_estimated_profit": total_estimated_profit,
            "total_recoverable_profit": total_recoverable_profit,
            "high_risk_count": high_risk_count,
        },
        "ai_message": ai_message,
        "top_actions": actions,
    }
