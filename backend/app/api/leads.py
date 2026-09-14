from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase_client import get_supabase_client
from app.core.company_context import get_current_company_id

router = APIRouter(prefix="/leads", tags=["leads"])


def _yen(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


@router.get("")
def list_leads(
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )

    rows = res.data or []
    customer_ids = [row.get("customer_id") for row in rows if row.get("customer_id")]
    customers_by_id = {}
    if customer_ids:
        customer_res = (
            db.table("customers")
            .select("id,name,company_name,email")
            .eq("company_id", company_id)
            .in_("id", customer_ids)
            .execute()
        )
        customers_by_id = {
            customer.get("id"): customer
            for customer in (customer_res.data or [])
        }

    return {
        "items": [
            {
                "id": row.get("id"),
                "customer": (
                    (customers_by_id.get(row.get("customer_id")) or {}).get("name")
                    or (customers_by_id.get(row.get("customer_id")) or {}).get("company_name")
                    or row.get("customer_name")
                    or "顧客未設定"
                ),
                "subject": row.get("title") or "利益候補",
                "priority": row.get("risk_level") or "未判定",
                "category": row.get("category") or "未分類",
                "status": row.get("status") or "open",
                "estimated_profit": _yen(row.get("estimated_profit")),
                "recoverable_profit": _yen(row.get("recoverable_profit")),
                "delay_days": int(row.get("neglected_days") or 0),
                "next_action": row.get("next_action") or "状況確認",
                "href": f"/leads/{row.get('id')}",
            }
            for row in rows
        ]
    }


@router.get("/{lead_id}")
def get_lead(
    lead_id: str,
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", company_id)
        .eq("id", lead_id)
        .limit(1)
        .execute()
    )

    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="lead not found")

    row = rows[0]

    customer_name = row.get("customer_name") or "顧客未設定"
    customer_id = row.get("customer_id")

    if customer_id:
        customer_res = (
            db.table("customers")
            .select("*")
            .eq("company_id", company_id)
            .eq("id", customer_id)
            .limit(1)
            .execute()
        )

        customer_rows = customer_res.data or []
        if customer_rows:
            customer = customer_rows[0]
            customer_name = (
                customer.get("name")
                or customer.get("company_name")
                or customer.get("email")
                or customer_name
            )

    judge_res = (
        db.table("ai_judgements")
        .select("*")
        .eq("company_id", company_id)
        .eq("profit_event_id", lead_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    judgement = (judge_res.data or [None])[0]

    return {
        "id": row.get("id"),
        "customer": customer_name,
        "subject": row.get("title") or "利益候補",
        "priority": row.get("risk_level") or "未判定",
        "category": row.get("category") or "未分類",
        "status": row.get("status") or "open",
        "estimated_profit": _yen(row.get("estimated_profit")),
        "recoverable_profit": _yen(row.get("recoverable_profit")),
        "delay_days": int(row.get("neglected_days") or 0),
        "next_action": row.get("next_action") or "状況確認",
        "body": row.get("description") or row.get("content") or "",
        "ai_judgement": judgement,
    }


@router.get("/{lead_id}/timeline")
def get_lead_timeline(
    lead_id: str,
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    res = (
        db.table("timeline")
        .select("*")
        .eq("company_id", company_id)
        .eq("profit_event_id", lead_id)
        .order("created_at", desc=True)
        .limit(30)
        .execute()
    )

    rows = res.data or []

    return {
        "items": [
            {
                "type": row.get("event_type") or row.get("type") or "system",
                "title": row.get("title") or "履歴",
                "body": row.get("description") or row.get("body") or "",
                "time": row.get("created_at") or row.get("occurred_at") or "",
            }
            for row in rows
        ]
    }
