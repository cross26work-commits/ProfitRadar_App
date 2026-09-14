from app.services.billing import require_ai_preview
import os
from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase_client import get_supabase_client
from app.core.company_context import get_current_company_id
from app.engines.ai_judge import generate_reply_draft, fallback_judge
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.message import EmailMessage
import base64
from app.services import reply_drafts
from app.services.gmail_credentials import credentials_for_connection
from app.services import send_operations
from app.services.gmail_work import company_lock
from app.services.billing import require_use

router = APIRouter(prefix="/reply", tags=["reply"])


@router.post("/{event_id}/reconcile")
def reconcile_reply(event_id: str, company_id: str = Depends(get_current_company_id)):
    db = get_supabase_client()
    with company_lock(db,company_id,"reconcile"):
        return _reconcile_reply(db,event_id,company_id)


def _reconcile_reply(db,event_id,company_id):
    operations = db.table("gmail_send_operations").select("*").eq("company_id",company_id).eq("profit_event_id",event_id).order("created_at",desc=True).limit(1).execute().data
    if not operations:
        raise HTTPException(404,"Send operation not found")
    connections = db.table("gmail_connections").select("*").eq("company_id",company_id).eq("status","connected").limit(1).execute().data
    if not connections:
        raise HTTPException(409,"Reconnect Gmail before reconciliation")
    credentials = credentials_for_connection(db,company_id,connections[0])
    service = build("gmail","v1",credentials=credentials)
    return send_operations.reconcile(db,company_id,operations[0],service,connections[0]["email"])


@router.post("/{event_id}/draft")
def save_reply_draft(event_id: str, payload: reply_drafts.DraftInput,
                     company_id: str = Depends(get_current_company_id)):
    return reply_drafts.save(get_supabase_client(), company_id, event_id, payload)


@router.get("/{event_id}/draft")
def build_reply_draft(
    event_id: str,
    company_id: str = Depends(get_current_company_id),
):
    return _draft_response(event_id,company_id,False)


@router.post("/{event_id}/generate")
def generate_reply(event_id: str,company_id: str=Depends(get_current_company_id)):
    from app.services.ai_usage import measured_generation
    db=get_supabase_client()
    require_ai_preview(db, company_id)
    # Resolve tenant resource before a usage reservation or provider call.
    if not db.table("profit_events").select("id").eq("company_id",company_id).eq("id",event_id).limit(1).execute().data:
        raise HTTPException(404,"profit event not found")
    with company_lock(db,company_id,"ai"):
        return measured_generation(db,company_id,lambda: _draft_response(event_id,company_id,True))


def _draft_response(event_id,company_id,generate):
    from app.engines.event_conversation import (
        build_event_conversation,
    )
    from app.engines.conversation_intelligence import (
        ConversationIntelligenceEngine,
        facts_to_dict,
    )
    from app.engines.conversation_reply import (
        ConversationReplyGenerator,
        reply_result_to_dict,
    )

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
        raise HTTPException(
            status_code=404,
            detail="profit event not found",
        )

    event = events[0]

    customer = None

    customer_id = event.get(
        "customer_id"
    )

    if customer_id:
        customer_res = (
            db.table("customers")
            .select("*")
            .eq(
                "company_id",
                company_id,
            )
            .eq(
                "id",
                customer_id,
            )
            .limit(1)
            .execute()
        )

        customer_rows = (
            customer_res.data
            or []
        )

        customer = (
            customer_rows[0]
            if customer_rows
            else None
        )

    saved = reply_drafts.load(db, company_id, event_id)
    operations=db.table("gmail_send_operations").select("status").eq("company_id",company_id).eq("profit_event_id",event_id).order("created_at",desc=True).limit(1).execute().data or []
    send_status=operations[0]["status"] if operations else ""
    if saved is not None and not generate:
        return {"company_id": company_id, "event_id": event_id, "event": event,
                "customer": customer, "draft": saved["body"], "subject": saved["subject"],
                "draft_provider": "saved", "updated_at": saved["updated_at"], "send_status":send_status}

    if not generate:
        try:
            snapshots = (
                db.table("conversation_analysis_snapshots")
                .select("payload,created_at")
                .eq("company_id", company_id)
                .eq("profit_event_id", event_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )
        except Exception:
            raise HTTPException(503,"Saved analysis storage unavailable") from None
        if snapshots:
            return {**snapshots[0]["payload"],"customer":customer,"event":event,"analysis_saved_at":snapshots[0]["created_at"],"send_status":send_status}
        return {"company_id":company_id,"event_id":event_id,"customer":customer,"event":event,"draft":"","draft_provider":"none","send_status":send_status}
    require_use(db,company_id)
    reply_res = (
        db.table("reply_logs")
        .select("*")
        .eq(
            "company_id",
            company_id,
        )
        .eq(
            "profit_event_id",
            event_id,
        )
        .eq(
            "channel",
            "gmail",
        )
        .execute()
    )

    reply_rows = (
        reply_res.data
        or []
    )

    timeline_res = (
        db.table("timeline")
        .select("*")
        .eq(
            "company_id",
            company_id,
        )
        .eq(
            "profit_event_id",
            event_id,
        )
        .execute()
    )

    timeline_rows = (
        timeline_res.data
        or []
    )

    history = build_event_conversation(
        timeline_rows=timeline_rows,
        reply_rows=reply_rows,
    )
    if len(history.get("transcript", ""))>30000:
        raise HTTPException(413,"Conversation exceeds generation input limit")

    latest_reply = None

    if reply_rows:
        ordered_replies = sorted(
            reply_rows,
            key=lambda row: (
                row.get("created_at")
                or ""
            ),
        )

        latest_reply = (
            ordered_replies[-1]
        )

    judgement_res = (
        db.table("ai_judgements")
        .select("*")
        .eq(
            "company_id",
            company_id,
        )
        .eq(
            "profit_event_id",
            event_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    judgement_rows = (
        judgement_res.data
        or []
    )

    judgement = (
        judgement_rows[0]
        if judgement_rows
        else None
    )

    important = bool(
        event.get("hot_lead")
        or event.get("risk_level")
        == "高"
        or int(
            event.get(
                "estimated_profit"
            )
            or 0
        )
        >= 100000
    )

    analysis = {}
    draft = ""
    draft_provider = "fallback"
    draft_model = ""
    conversation_ai_error = None

    if history.get(
        "message_count",
        0,
    ) > 0:
        try:
            intelligence = (
                ConversationIntelligenceEngine()
            )

            facts = intelligence.analyze(
                conversation_text=history[
                    "transcript"
                ],
                important=important,
            )

            analysis = facts_to_dict(
                facts
            )

            generator = (
                ConversationReplyGenerator()
            )

            generated = generator.generate(
                conversation_text=history[
                    "transcript"
                ],
                facts=analysis,
                important=important,
            )

            generated_dict = (
                reply_result_to_dict(
                    generated
                )
            )

            draft = (
                generated_dict.get(
                    "body"
                )
                or ""
            )

            draft_provider = (
                generated_dict.get(
                    "provider"
                )
                or "fallback"
            )

            draft_model = (
                generated_dict.get(
                    "model"
                )
                or ""
            )

        except HTTPException:
            raise
        except Exception as exc:
            conversation_ai_error = (
                exc.__class__.__name__
            )

    if not draft:
        customer_name = (
            (customer or {}).get(
                "name"
            )
            or "ご担当者様"
        )

        latest_body = (
            (latest_reply or {}).get(
                "reply_body"
            )
            or ""
        )

        if latest_body:
            draft = (
                "お疲れ様です。\n"
                "ご連絡ありがとうございます。\n\n"
                "内容を確認いたしました。"
                "確認のうえ、"
                "改めてご連絡いたします。\n\n"
                "よろしくお願いいたします。"
            )
        else:
            draft = (
                f"{customer_name} 様\n\n"
                "お世話になっております。\n"
                "ご連絡ありがとうございます。\n\n"
                "内容を確認のうえ、"
                "改めてご連絡いたします。\n\n"
                "よろしくお願いいたします。"
            )

        draft_provider = "fallback"

    result = {
        "company_id": company_id,
        "event_id": event_id,
        "customer": customer,
        "event": event,
        "ai_judgement": judgement,
        "latest_reply": latest_reply,

        "conversation": {
            "message_count": history.get(
                "message_count",
                0,
            ),
            "messages": history.get(
                "messages",
                [],
            ),
        },

        "analysis": analysis,

        "draft_provider": (
            draft_provider
        ),

        "draft_model": (
            draft_model
        ),

        "draft": draft,

        "conversation_ai_error": (
            conversation_ai_error
        ),
    }
    db.table("conversation_analysis_snapshots").insert({"company_id":company_id,"profit_event_id":event_id,"payload":result,"provider":draft_provider,"model":draft_model}).execute()
    return result


@router.post("/{event_id}/send")
def send_reply(
    event_id: str,
    payload: dict,
    company_id: str = Depends(get_current_company_id),
):
    with company_lock(get_supabase_client(),company_id,"send"):
        return _send_reply(event_id,payload,company_id)


def _send_reply(event_id, payload, company_id):
    require_use(get_supabase_client(),company_id)
    """Send a human-confirmed reply only to the event's registered customer."""
    db = get_supabase_client()

    body = payload.get("body") or ""
    requested_customer_id = payload.get("customer_id")
    requested_to_email = (payload.get("to_email") or "").strip().lower()
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

    customer_id = event.get("customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="event customer is required before sending")
    if requested_customer_id and requested_customer_id != customer_id:
        raise HTTPException(status_code=403, detail="customer does not match the event")

    customer = None

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
        customer = customer_rows[0] if customer_rows else None

    if not customer:
        raise HTTPException(status_code=404, detail="event customer not found")
    to_email = ((customer or {}).get("email") or "").strip().lower()
    if not to_email:
        raise HTTPException(
            status_code=400,
            detail="customer email is required",
        )
    if requested_to_email and requested_to_email != to_email:
        raise HTTPException(status_code=403, detail="recipient does not match the event customer")
    if any(char in to_email + subject for char in "\r\n") or len(body)>50000 or len(subject)>998:
        raise HTTPException(status_code=422, detail="Invalid mail content")

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

    credentials = credentials_for_connection(db, company_id, rows[0])

    service = build("gmail", "v1", credentials=credentials)

    message = EmailMessage()
    message.set_content(body)
    message["To"] = to_email
    message["From"] = rows[0]["email"]
    message["Subject"] = subject

    existing_thread_id = event.get(
        "gmail_thread_id"
    )

    gmail_send_body = {}

    if existing_thread_id:
        try:
            thread = (
                service.users()
                .threads()
                .get(
                    userId="me",
                    id=existing_thread_id,
                    format="metadata",
                    metadataHeaders=[
                        "Message-ID",
                        "References",
                    ],
                )
                .execute()
            )

            thread_messages = (
                thread.get("messages", [])
                or []
            )

            if thread_messages:
                latest_message = (
                    thread_messages[-1]
                )

                latest_headers = (
                    latest_message
                    .get("payload", {})
                    .get("headers", [])
                    or []
                )

                def _header_value(
                    name: str,
                ) -> str:
                    for header in latest_headers:
                        if (
                            header.get("name", "")
                            .lower()
                            == name.lower()
                        ):
                            return (
                                header.get(
                                    "value",
                                    "",
                                )
                                or ""
                            )

                    return ""

                parent_message_id = (
                    _header_value(
                        "Message-ID"
                    )
                )

                previous_references = (
                    _header_value(
                        "References"
                    )
                )

                if parent_message_id:
                    message[
                        "In-Reply-To"
                    ] = parent_message_id

                    references = (
                        (
                            previous_references
                            + " "
                            + parent_message_id
                        )
                        .strip()
                    )

                    message[
                        "References"
                    ] = references

        except Exception:
            # ヘッダー取得に失敗しても
            # threadIdを使った送信は試行する。
            pass

    operation_id, claimed, operation_status = send_operations.claim(db, company_id, event_id, to_email, subject, body, customer_id)
    if not claimed:
        return {"sent": operation_status == "sent", "status": operation_status, "operation_id": operation_id}
    message["Message-ID"] = f"<pr-{operation_id}@profitradar.invalid>"

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    gmail_send_body["raw"] = raw

    if existing_thread_id:
        gmail_send_body[
            "threadId"
        ] = existing_thread_id

    return send_operations.execute_once(db, company_id, operation_id,
        lambda: service.users().messages().send(userId="me", body=gmail_send_body).execute())
