from app.services.home_brief_service import build_home_brief
from app.repositories.action_repository import get_recent_timeline


def build_dashboard_home(company_id: str) -> dict:
    brief = build_home_brief(company_id=company_id)
    top_actions = brief.get("top_actions", [])

    reply_queue = [
        action for action in top_actions
        if action.get("next_action")
    ]

    risks = [
        {
            "event_id": action.get("event_id"),
            "title": action.get("title"),
            "customer_name": action.get("customer_name"),
            "risk_level": action.get("risk_level"),
            "reason": action.get("reason"),
            "estimated_profit": action.get("estimated_profit"),
            "next_action": action.get("next_action"),
        }
        for action in top_actions
        if str(action.get("risk_level") or "") in ["高", "high", "HIGH", "中", "medium", "MEDIUM"]
    ]

    recent_timeline = get_recent_timeline(company_id=company_id, limit=10)

    return {
        "company_id": company_id,
        "summary": brief.get("summary", {}),
        "ai_message": brief.get("ai_message", ""),
        "top_actions": top_actions,
        "reply_queue": reply_queue,
        "risks": risks,
        "recent_timeline": recent_timeline,
    }
