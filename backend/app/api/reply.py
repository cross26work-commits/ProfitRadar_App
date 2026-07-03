from fastapi import APIRouter, Header, HTTPException
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/reply", tags=["reply"])


@router.get("/{event_id}/draft")
def build_reply_draft(
    event_id: str,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    event_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("id", event_id)
        .limit(1)
        .execute()
    )

    events = event_res.data or []
    if not events:
        raise HTTPException(status_code=404, detail="profit event not found")

    event = events[0]

    customer = None
    if event.get("customer_id"):
        customer_res = (
            db.table("customers")
            .select("*")
            .eq("company_id", x_company_id)
            .eq("id", event.get("customer_id"))
            .limit(1)
            .execute()
        )
        rows = customer_res.data or []
        customer = rows[0] if rows else None

    judgement_res = (
        db.table("ai_judgements")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("profit_event_id", event_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    judgement = (judgement_res.data or [None])[0]

    customer_name = (
        (customer or {}).get("name")
        or "ご担当者様"
    )

    next_action = (
        (judgement or {}).get("next_action")
        or event.get("next_action")
        or "状況確認"
    )

    title = event.get("title") or "ご確認事項"

    draft = (
        f"{customer_name}\n\n"
        f"お世話になっております。\n\n"
        f"「{title}」の件でご連絡いたしました。\n"
        f"{next_action}のため、現在のご状況を確認させていただけますでしょうか。\n\n"
        f"進行可能であれば、次の手続きへ進めさせていただきます。\n"
        f"ご確認のほど、よろしくお願いいたします。"
    )

    return {
        "company_id": x_company_id,
        "event_id": event_id,
        "customer": customer,
        "event": event,
        "ai_judgement": judgement,
        "draft": draft,
    }


@router.post("/{event_id}/save-draft")
def save_reply_draft(
    event_id: str,
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    body = payload.get("body") or ""
    if not body:
        raise HTTPException(status_code=400, detail="body is required")

    timeline_payload = {
        "company_id": x_company_id,
        "customer_id": payload.get("customer_id"),
        "profit_event_id": event_id,
        "event_type": "reply_draft_saved",
        "channel": "system",
        "title": "返信下書きを保存",
        "description": body[:500],
        "amount": 0,
        "metadata": {
            "source": "reply_draft",
        },
    }

    timeline = db.table("timeline").insert(timeline_payload).execute()

    learning_payload = {
        "company_id": x_company_id,
        "customer_id": payload.get("customer_id"),
        "profit_event_id": event_id,
        "event_type": "reply_draft_saved",
        "input_data": payload,
        "result_data": {
            "body": body,
        },
        "success": True,
        "actual_profit": 0,
    }

    learning = db.table("learning_logs").insert(learning_payload).execute()

    return {
        "saved": True,
        "timeline_event": (timeline.data or [None])[0],
        "learning_event": (learning.data or [None])[0],
    }


@router.post("/{event_id}/send")
def send_reply_mock(
    event_id: str,
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    """
    Phase6-1: Gmail本接続前の安全な疑似送信API。
    実送信はまだ行わず、送信履歴・Timeline・Learningへ保存する。
    """
    db = get_supabase_client()

    body = payload.get("body") or ""
    customer_id = payload.get("customer_id")
    to_email = payload.get("to_email") or ""
    subject = payload.get("subject") or "Profit Radar 返信"

    if not body:
        raise HTTPException(status_code=400, detail="body is required")

    event_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("id", event_id)
        .limit(1)
        .execute()
    )

    events = event_res.data or []
    if not events:
        raise HTTPException(status_code=404, detail="profit event not found")

    event = events[0]

    if not customer_id:
        customer_id = event.get("customer_id")

    # NOTE:
    # actionsテーブルは現時点のSupabaseに未確定のため保存しない。
    # Phase6-1では timeline + learning_logs へ疑似送信履歴を保存する。

    timeline_payload = {
        "company_id": x_company_id,
        "customer_id": customer_id,
        "profit_event_id": event_id,
        "event_type": "reply_sent_mock",
        "channel": "gmail",
        "title": "返信を疑似送信",
        "description": body[:500],
        "amount": 0,
        "metadata": {
            "mode": "mock",
            "subject": subject,
            "to_email": to_email,
        },
    }

    timeline = db.table("timeline").insert(timeline_payload).execute()

    learning_payload = {
        "company_id": x_company_id,
        "customer_id": customer_id,
        "profit_event_id": event_id,
        "event_type": "reply_sent_mock",
        "input_data": payload,
        "result_data": {
            "body": body,
            "subject": subject,
            "to_email": to_email,
            "mode": "mock",
        },
        "success": True,
        "actual_profit": 0,
    }

    learning = db.table("learning_logs").insert(learning_payload).execute()

    return {
        "sent": True,
        "mode": "mock",
        "message": "Gmail未接続のため疑似送信として保存しました。",
        "timeline_event": (timeline.data or [None])[0],
        "learning_event": (learning.data or [None])[0],
    }
