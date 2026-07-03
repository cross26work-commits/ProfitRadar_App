from fastapi import APIRouter, Header, HTTPException
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/customers", tags=["customers"])


def _yen(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


@router.get("")
def list_customers(
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    customers_res = (
        db.table("customers")
        .select("*")
        .eq("company_id", x_company_id)
        .order("updated_at", desc=True)
        .limit(100)
        .execute()
    )

    events_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .execute()
    )

    customers = customers_res.data or []
    events = events_res.data or []

    event_map = {}
    for event in events:
        customer_id = event.get("customer_id")
        if not customer_id:
            continue
        event_map.setdefault(customer_id, []).append(event)

    items = []
    for customer in customers:
        customer_events = event_map.get(customer.get("id"), [])
        estimated_profit = sum(_yen(e.get("estimated_profit")) for e in customer_events)

        items.append({
            "id": customer.get("id"),
            "name": customer.get("name") or customer.get("company_name") or "顧客未設定",
            "leads": len(customer_events),
            "profit": estimated_profit,
            "last": customer.get("last_contact_at") or customer.get("updated_at") or "",
            "href": f"/customers/{customer.get('id')}",
        })

    return {
        "items": items,
        "message": "customers loaded from Supabase",
    }


@router.get("/{customer_id}")
def get_customer(
    customer_id: str,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    res = (
        db.table("customers")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("id", customer_id)
        .limit(1)
        .execute()
    )

    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="customer not found")

    customer = rows[0]

    return {
        "id": customer.get("id"),
        "name": customer.get("name") or customer.get("company_name") or "顧客未設定",
        "contact": customer.get("name") or "",
        "email": customer.get("email") or "",
        "status": customer.get("status") or "active",
        "next_action": "利益候補を確認",
    }


@router.get("/{customer_id}/leads")
def get_customer_leads(
    customer_id: str,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )

    rows = res.data or []

    return {
        "items": [
            {
                "id": row.get("id"),
                "customer": "顧客",
                "subject": row.get("title") or "利益候補",
                "priority": row.get("risk_level") or "未判定",
                "status": row.get("status") or "open",
                "estimated_profit": _yen(row.get("estimated_profit")),
                "recoverable_profit": 0,
                "delay_days": 0,
                "href": f"/leads/{row.get('id')}",
            }
            for row in rows
        ],
        "message": "customer leads loaded from Supabase",
    }


@router.get("/{customer_id}/timeline")
def get_customer_timeline(
    customer_id: str,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    res = (
        db.table("timeline")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .limit(30)
        .execute()
    )

    rows = res.data or []

    return {
        "items": [
            {
                "type": row.get("event_type") or "system",
                "title": row.get("title") or "履歴",
                "body": row.get("description") or "",
                "time": row.get("created_at") or row.get("occurred_at") or "",
            }
            for row in rows
        ]
    }
