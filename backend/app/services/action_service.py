from app.engines.action_engine import generate_top_actions
from app.repositories.action_repository import (
    get_open_profit_events,
    get_ai_judgements,
    get_customers,
    get_recent_timeline,
)


def _build_customer_map(customers: list[dict]) -> dict:
    return {
        c.get("id"): c
        for c in customers
        if c.get("id")
    }


def _build_timeline_map(timeline: list[dict]) -> dict:
    timeline_map = {}

    for item in timeline:
        event_id = (
            item.get("profit_event_id")
            or item.get("event_id")
            or item.get("source_id")
        )

        if event_id and event_id not in timeline_map:
            timeline_map[event_id] = item

    return timeline_map


def _enrich_events(
    events: list[dict],
    customers: list[dict],
    timeline: list[dict],
) -> list[dict]:
    customer_map = _build_customer_map(customers)
    timeline_map = _build_timeline_map(timeline)

    enriched = []

    for event in events:
        e = dict(event)

        customer_id = e.get("customer_id")
        customer = customer_map.get(customer_id)

        if customer:
            e["customer_name"] = (
                customer.get("name")
                or customer.get("company_name")
                or customer.get("email")
                or ""
            )
        else:
            e["customer_name"] = (
                e.get("customer_name")
                or e.get("customer")
                or e.get("from_email")
                or e.get("email")
                or "顧客未設定"
            )

        latest = timeline_map.get(e.get("id"))

        if latest:
            e["latest_timeline"] = {
                "id": latest.get("id"),
                "type": latest.get("type") or latest.get("event_type"),
                "title": latest.get("title"),
                "body": latest.get("body") or latest.get("content"),
                "created_at": latest.get("created_at"),
            }
        else:
            e["latest_timeline"] = None

        enriched.append(e)

    return enriched


def get_today_top_actions(company_id: str, limit: int = 5) -> list[dict]:
    events = get_open_profit_events(company_id=company_id, limit=50)
    judgements = get_ai_judgements(company_id=company_id, limit=100)
    customers = get_customers(company_id=company_id, limit=500)
    timeline = get_recent_timeline(company_id=company_id, limit=300)

    enriched_events = _enrich_events(
        events=events,
        customers=customers,
        timeline=timeline,
    )

    return generate_top_actions(
        events=enriched_events,
        judgements=judgements,
        limit=limit,
    )
