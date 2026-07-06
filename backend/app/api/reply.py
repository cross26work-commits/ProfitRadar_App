from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase_client import get_supabase_client
from app.core.company_context import get_current_company_id
from app.services.customer_resolver_service import CustomerResolverService
from app.repositories.customer_repository import CustomerRepository
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.message import EmailMessage
import base64

router = APIRouter(prefix="/reply", tags=["reply"])


@router.get("/{event_id}/draft")
def build_reply_draft(
    event_id: str,
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    event_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", company_id)
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
            .eq("company_id", company_id)
            .eq("id", event.get("customer_id"))
            .limit(1)
            .execute()
        )
        rows = customer_res.data or []
        customer = rows[0] if rows else None

    judgement_res = (
        db.table("ai_judgements")
        .select("*")
        .eq("company_id", company_id)
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
        "company_id": company_id,
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
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    body = payload.get("body") or ""
    if not body:
        raise HTTPException(status_code=400, detail="body is required")

    event_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", company_id)
        .eq("id", event_id)
        .limit(1)
        .execute()
    )

    events = event_res.data or []
    if not events:
        raise HTTPException(status_code=404, detail="profit event not found")

    event = events[0]
    customer_id = event.get("customer_id")

    timeline_payload = {
        "company_id": company_id,
        "customer_id": customer_id,
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
        "company_id": company_id,
        "customer_id": customer_id,
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
    company_id: str = Depends(get_current_company_id),
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
        .eq("company_id", company_id)
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

    # Phase6-6: 送信先メールアドレスから顧客を自動解決
    if not customer_id and to_email:
        resolver = CustomerResolverService(
            repository=CustomerRepository(db=db)
        )
        customer = resolver.resolve(
            company_id=company_id,
            payload={
                "email": to_email,
                "name": to_email,
            },
        )
        if customer:
            customer_id = customer.get("id")
            db.table("profit_events").update({
                "customer_id": customer_id,
            }).eq("company_id", company_id).eq("id", event_id).execute()

    conn = (
        db.table("gmail_connections")
        .select("*")
        .eq("company_id", company_id)
        .eq("status", "connected")
        .limit(1)
        .execute()
    )

    rows = conn.data or []
    if not rows:
        raise HTTPException(status_code=400, detail="Gmail is not connected")

    token_json = rows[0]["token_json"]

    credentials = Credentials(
        token=token_json["token"],
        refresh_token=token_json["refresh_token"],
        token_uri=token_json["token_uri"],
        client_id=token_json["client_id"],
        client_secret=token_json["client_secret"],
        scopes=token_json["scopes"],
    )

    service = build("gmail", "v1", credentials=credentials)

    message = EmailMessage()
    message.set_content(body)
    message["To"] = to_email
    message["From"] = "me"
    message["Subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    gmail_result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": raw},
        )
        .execute()
    )

    gmail_message_id = gmail_result.get("id")
    gmail_thread_id = gmail_result.get("threadId")

    if gmail_thread_id:
        db.table("profit_events").update({
            "gmail_thread_id": gmail_thread_id,
            "last_gmail_message_id": gmail_message_id,
        }).eq("company_id", company_id).eq("id", event_id).execute()

    timeline_payload = {
        "company_id": company_id,
        "customer_id": customer_id,
        "profit_event_id": event_id,
        "event_type": "reply_sent_gmail",
        "channel": "gmail",
        "title": "Gmail返信を送信",
        "description": body[:500],
        "amount": 0,
        "metadata": {
            "mode": "gmail",
            "subject": subject,
            "to_email": to_email,
            "gmail_message_id": gmail_message_id,
            "gmail_thread_id": gmail_thread_id,
        },
    }

    timeline = db.table("timeline").insert(timeline_payload).execute()

    learning_payload = {
        "company_id": company_id,
        "customer_id": customer_id,
        "profit_event_id": event_id,
        "event_type": "reply_sent_gmail",
        "input_data": payload,
        "result_data": {
            "body": body,
            "subject": subject,
            "to_email": to_email,
            "mode": "gmail",
            "gmail_message_id": gmail_message_id,
            "gmail_thread_id": gmail_thread_id,
        },
        "success": True,
        "actual_profit": 0,
    }

    learning = db.table("learning_logs").insert(learning_payload).execute()

    return {
        "sent": True,
        "mode": "gmail",
        "message": "Gmailから送信しました。",
        "timeline_event": (timeline.data or [None])[0],
        "learning_event": (learning.data or [None])[0],
        "gmail_result": gmail_result,
    }
