from datetime import datetime, timezone


def _num(value, default=0):
    try:
        return int(value or default)
    except Exception:
        return default


def calculate_action_score(event: dict, judgement: dict | None = None) -> int:
    """
    今日やる営業の優先度を数値化する。
    単なる金額順ではなく、
    利益・温度感・放置・危険度・AI判断を合算する。
    """

    score = 0

    estimated_profit = _num(event.get("estimated_profit"))
    recoverable_profit = _num(event.get("recoverable_profit"))
    opportunity_score = _num(event.get("opportunity_score"))
    neglected_days = _num(event.get("neglected_days"))

    score += min(estimated_profit // 10000, 30)
    score += min(recoverable_profit // 10000, 30)
    score += min(opportunity_score, 30)

    if event.get("hot_lead"):
        score += 20

    if neglected_days >= 7:
        score += 20
    elif neglected_days >= 3:
        score += 10
    elif neglected_days >= 1:
        score += 5

    risk = str(event.get("risk_level") or "")
    if risk in ["高", "high", "HIGH"]:
        score += 20
    elif risk in ["中", "medium", "MEDIUM"]:
        score += 10
    elif risk in ["低", "low", "LOW"]:
        score += 3

    if judgement:
        decision = str(judgement.get("decision") or judgement.get("judgement") or "")
        if "最優先" in decision or "urgent" in decision.lower():
            score += 20
        elif "対応" in decision or "reply" in decision.lower():
            score += 10

    return max(score, 0)


def build_action_reason(event: dict, judgement: dict | None = None) -> str:
    reasons = []

    if event.get("hot_lead"):
        reasons.append("利益化の可能性が高い")

    if _num(event.get("estimated_profit")) > 0:
        reasons.append(f"推定利益が{_num(event.get('estimated_profit')):,}円")

    if _num(event.get("recoverable_profit")) > 0:
        reasons.append(f"回収可能利益が{_num(event.get('recoverable_profit')):,}円")

    if _num(event.get("neglected_days")) >= 3:
        reasons.append(f"{_num(event.get('neglected_days'))}日放置されている")

    risk = event.get("risk_level")
    if risk:
        reasons.append(f"リスク判定:{risk}")

    if judgement:
        ai_reason = judgement.get("reason") or judgement.get("summary")
        if ai_reason:
            reasons.append(f"AI判断:{ai_reason}")

    if not reasons:
        reasons.append("営業対応候補として優先順位付け")

    return " / ".join(reasons)


def build_next_action(event: dict, judgement: dict | None = None) -> str:
    # profit_events は Gmail返信解析後に最新状態へ更新されるため最優先
    if event.get("next_action"):
        return str(event["next_action"])

    # event側に値がない場合のみAI判定を使用
    if judgement:
        for key in ["next_action", "recommended_action", "action"]:
            if judgement.get(key):
                return str(judgement[key])

    category = str(event.get("category") or "")

    if "見積" in category or "提案" in category:
        return "検討状況を確認し、次の意思決定を促す"
    if "請求" in category or "入金" in category:
        return "入金予定日を確認する"
    if "契約" in category:
        return "契約手続きの進行状況を確認する"
    if "採用" in category or "面談" in category:
        return "面談・稼働に向けた次アクションを確認する"

    return "相手に状況確認の連絡を入れる"


def build_action_item(event: dict, judgement: dict | None = None) -> dict:
    score = calculate_action_score(event, judgement)

    return {
        "event_id": event.get("id"),
        "customer_id": event.get("customer_id"),
        "company_id": event.get("company_id"),
        "title": event.get("subject") or event.get("title") or "営業対応候補",
        "customer_name": event.get("customer_name") or event.get("customer") or "",
        "estimated_profit": _num(event.get("estimated_profit")),
        "recoverable_profit": _num(event.get("recoverable_profit")),
        "risk_level": event.get("risk_level") or "未判定",
        "category": event.get("category") or "未分類",
        "priority_score": score,
        "reason": build_action_reason(event, judgement),
        "next_action": build_next_action(event, judgement),
        "latest_timeline": event.get("latest_timeline"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_top_actions(events: list[dict], judgements: list[dict] | None = None, limit: int = 5) -> list[dict]:
    judgement_map = {}

    for j in judgements or []:
        event_id = j.get("profit_event_id") or j.get("event_id")
        if event_id and event_id not in judgement_map:
            judgement_map[event_id] = j

    actions = []

    for event in events:
        status = str(event.get("status") or event.get("stage") or "").lower()

        if status in ["done", "closed", "completed", "対応済み", "完了", "失注"]:
            continue

        event_id = event.get("id")
        judgement = judgement_map.get(event_id)

        action = build_action_item(event, judgement)
        actions.append(action)

    actions.sort(key=lambda x: x["priority_score"], reverse=True)

    return actions[:limit]
