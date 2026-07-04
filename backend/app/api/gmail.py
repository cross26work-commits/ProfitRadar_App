import os
import traceback

from fastapi import APIRouter, Header, HTTPException
from app.core.supabase_client import get_supabase_client
from app.services.ai_judge_service import AIJudgeService
from app.repositories.ai_judgement_repository import AIJudgementRepository
from app.services.customer_resolver_service import CustomerResolverService
from app.repositories.customer_repository import CustomerRepository
from app.engines.sales_temperature import build_sales_update
from google_auth_oauthlib.flow import Flow

router = APIRouter(prefix="/gmail", tags=["gmail"])

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _client_config() -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth env is missing",
        )

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "config": {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
    }


@router.get("/status")
def gmail_status():
    return {
        "connected": False,
        "message": "gmail oauth api ready",
    }


@router.get("/auth-url")
def gmail_auth_url(
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    cfg = _client_config()

    flow = Flow.from_client_config(
        cfg["config"],
        scopes=SCOPES,
        redirect_uri=cfg["redirect_uri"],
        autogenerate_code_verifier=False,
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=x_company_id,
    )

    return {
        "auth_url": auth_url,
        "state": state,
        "company_id": x_company_id,
        "scopes": SCOPES,
    }


@router.get("/callback")
def gmail_callback(
    code: str | None = None,
    state: str | None = None,
):
    if not code:
        raise HTTPException(status_code=400, detail="code is required")

    cfg = _client_config()

    flow = Flow.from_client_config(
        cfg["config"],
        scopes=SCOPES,
        redirect_uri=cfg["redirect_uri"],
        autogenerate_code_verifier=False,
    )

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "stage": "fetch_token",
                "error": str(e),
                "trace": traceback.format_exc(),
            },
        )

    credentials = flow.credentials

    company_id = state
    if not company_id:
        raise HTTPException(status_code=400, detail="state/company_id is required")

    token_json = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }

    db = get_supabase_client()

    existing = (
        db.table("gmail_connections")
        .select("*")
        .eq("company_id", company_id)
        .limit(1)
        .execute()
    )

    payload = {
        "company_id": company_id,
        "email": "connected@gmail.com",
        "token_json": token_json,
        "status": "connected",
    }

    try:
        if existing.data:
            saved = (
                db.table("gmail_connections")
                .update(payload)
                .eq("company_id", company_id)
                .execute()
            )
        else:
            saved = db.table("gmail_connections").insert(payload).execute()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "stage": "supabase_save",
                "error": str(e),
                "trace": traceback.format_exc(),
            },
        )

    return {
        "connected": True,
        "mode": "token_saved",
        "company_id": company_id,
        "connection": (saved.data or [None])[0],
        "token_info": {
            "has_token": bool(credentials.token),
            "has_refresh_token": bool(credentials.refresh_token),
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        },
        "message": "Gmail token saved.",
    }


import base64
from email.utils import parseaddr
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@router.post("/send-test")
def gmail_send_test(
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    conn_res = (
        db.table("gmail_connections")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("status", "connected")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = conn_res.data or []
    if not rows:
        raise HTTPException(status_code=400, detail="Gmail is not connected")

    token_json = rows[0].get("token_json") or {}

    credentials = Credentials(
        token=token_json.get("token"),
        refresh_token=token_json.get("refresh_token"),
        token_uri=token_json.get("token_uri"),
        client_id=token_json.get("client_id"),
        client_secret=token_json.get("client_secret"),
        scopes=token_json.get("scopes"),
    )

    service = build("gmail", "v1", credentials=credentials)

    to_email = payload.get("to_email")
    subject = payload.get("subject") or "Profit Radar Gmail送信テスト"
    body = payload.get("body") or "Profit RadarからのGmail送信テストです。"

    if not to_email:
        raise HTTPException(status_code=400, detail="to_email is required")

    message = EmailMessage()
    message.set_content(body)
    message["To"] = to_email
    message["From"] = "me"
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    sent = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": encoded_message},
        )
        .execute()
    )

    return {
        "sent": True,
        "provider": "gmail",
        "to_email": to_email,
        "subject": subject,
        "gmail_result": sent,
    }


def _extract_header(headers: list[dict], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _extract_text_from_payload(payload: dict) -> str:
    import base64

    def decode_body(data: str) -> str:
        if not data:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(data + "===")
            return decoded.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    if payload.get("body", {}).get("data"):
        return decode_body(payload["body"]["data"])

    for part in payload.get("parts", []) or []:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return decode_body(part["body"]["data"])

    return ""


def _strip_quoted_reply(text: str) -> str:
    """
    Gmail返信本文から、過去メール引用・署名・転送引用を除去する。
    AI解析には最新返信だけを渡す。
    """
    if not text:
        return ""

    markers = [
        "\nOn ",
        "\r\nOn ",
        "\n202",
        "\r\n202",
        "\n20",
        "\r\n20",
        "\n>",
        "\r\n>",
        "\n-----Original Message-----",
        "\r\n-----Original Message-----",
        "\n転送されたメッセージ",
        "\r\n転送されたメッセージ",
    ]

    cut = len(text)
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            cut = min(cut, idx)

    cleaned = text[:cut].strip()

    signature_markers = [
        "\n-- ",
        "\r\n-- ",
        "\nSent from my iPhone",
        "\r\nSent from my iPhone",
    ]

    cut = len(cleaned)
    for marker in signature_markers:
        idx = cleaned.find(marker)
        if idx != -1:
            cut = min(cut, idx)

    return cleaned[:cut].strip()


@router.post("/check-replies")
def gmail_check_replies(
    payload: dict | None = None,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    db = get_supabase_client()

    conn_res = (
        db.table("gmail_connections")
        .select("*")
        .eq("company_id", x_company_id)
        .eq("status", "connected")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = conn_res.data or []
    if not rows:
        raise HTTPException(status_code=400, detail="Gmail is not connected")

    token_json = rows[0].get("token_json") or {}

    credentials = Credentials(
        token=token_json.get("token"),
        refresh_token=token_json.get("refresh_token"),
        token_uri=token_json.get("token_uri"),
        client_id=token_json.get("client_id"),
        client_secret=token_json.get("client_secret"),
        scopes=token_json.get("scopes"),
    )

    service = build("gmail", "v1", credentials=credentials)

    max_events = int((payload or {}).get("max_events") or 50)

    connected_email = rows[0].get("email") or ""
    own_email = parseaddr(connected_email)[1].lower()

    events_res = (
        db.table("profit_events")
        .select("*")
        .eq("company_id", x_company_id)
        .not_.is_("gmail_thread_id", "null")
        .limit(max_events)
        .execute()
    )

    events = events_res.data or []
    detected = []

    for event in events:
        event_id = event.get("id")
        customer_id = event.get("customer_id")
        thread_id = event.get("gmail_thread_id")

        if not thread_id:
            continue

        thread = (
            service.users()
            .threads()
            .get(
                userId="me",
                id=thread_id,
                format="full",
            )
            .execute()
        )

        messages = thread.get("messages", []) or []

        for detail in messages:
            message_id = detail.get("id")
            payload_data = detail.get("payload") or {}
            headers = payload_data.get("headers") or []

            from_raw = _extract_header(headers, "From")
            from_email = parseaddr(from_raw)[1].lower()
            subject = _extract_header(headers, "Subject")
            date = _extract_header(headers, "Date")
            body = _extract_text_from_payload(payload_data)
            clean_body = _strip_quoted_reply(body) or body

            if not message_id:
                continue

            label_ids = detail.get("labelIds", []) or []
            last_sent_message_id = event.get("last_gmail_message_id")

            # 自分が送ったメールは除外
            # 1. Gmail SENTラベル
            # 2. 送信時に保存したlast_gmail_message_id
            # 3. Gmail接続emailとFrom一致
            if "SENT" in label_ids:
                continue

            if last_sent_message_id and message_id == last_sent_message_id:
                continue

            if own_email and from_email == own_email:
                continue

            exists = (
                db.table("reply_logs")
                .select("id")
                .eq("company_id", x_company_id)
                .or_(f"external_id.eq.{message_id},gmail_message_id.eq.{message_id}")
                .limit(1)
                .execute()
            )

            if exists.data:
                continue

            # Phase6-6: 外部返信メールアドレスから顧客を自動解決
            customer_id = event.get("customer_id")

            if not customer_id and from_email:
                resolver = CustomerResolverService(
                    repository=CustomerRepository(db=db)
                )

                customer = resolver.resolve(
                    company_id=x_company_id,
                    payload={
                        "email": from_email,
                        "sender": from_raw,
                    },
                )

                if customer:
                    customer_id = customer.get("id")

                    db.table("profit_events").update({
                        "customer_id": customer_id,
                    }).eq(
                        "company_id", x_company_id
                    ).eq(
                        "id", event.get("id")
                    ).execute()

                    event["customer_id"] = customer_id

            reply_payload = {
                "company_id": x_company_id,
                "customer_id": customer_id,
                "profit_event_id": event_id,
                "channel": "gmail",
                "reply_body": clean_body[:5000],
                "reply_at": None,
                "external_id": message_id,
                "thread_id": thread_id,
                "gmail_thread_id": thread_id,
                "gmail_message_id": message_id,
            }

            reply_log = db.table("reply_logs").insert(reply_payload).execute()

            timeline_payload = {
                "company_id": x_company_id,
                "customer_id": customer_id,
                "profit_event_id": event_id,
                "event_type": "gmail_reply_detected",
                "channel": "gmail",
                "title": "Gmail返信を検知",
                "description": f"{from_raw} / {subject}\n{clean_body[:500]}",
                "amount": 0,
                "metadata": {
                    "gmail_message_id": message_id,
                    "gmail_thread_id": thread_id,
                    "from": from_raw,
                    "from_email": from_email,
                    "subject": subject,
                    "date": date,
                },
            }

            timeline = db.table("timeline").insert(timeline_payload).execute()

            if customer_id:
                related_events = (
                    db.table("profit_events")
                    .select("estimated_profit,actual_profit")
                    .eq("company_id", x_company_id)
                    .eq("customer_id", customer_id)
                    .execute()
                )

                total_estimated_profit = sum(
                    int(row.get("estimated_profit") or 0)
                    for row in (related_events.data or [])
                )

                total_actual_profit = sum(
                    int(row.get("actual_profit") or 0)
                    for row in (related_events.data or [])
                )

                db.table("customers").update({
                    "total_estimated_profit": total_estimated_profit,
                    "total_actual_profit": total_actual_profit,
                    "last_contact_at": date,
                }).eq("company_id", x_company_id).eq("id", customer_id).execute()

            ai_result = None
            try:
                ai_service = AIJudgeService(
                    repository=AIJudgementRepository(db=db)
                )
                ai_result = ai_service.judge_and_save(
                    company_id=x_company_id,
                    payload={
                        "customer_id": customer_id,
                        "profit_event_id": event_id,
                        "subject": subject,
                        "sender": from_raw,
                        "body": clean_body,
                        "score": event.get("opportunity_score") or 0,
                    },
                )

                judgement_result = ai_result.get("result") or {}

                update_payload = {
                    "last_gmail_message_id": message_id,
                    **build_sales_update(judgement_result, event),
                }

                db.table("profit_events").update(update_payload).eq("company_id", x_company_id).eq("id", event_id).execute()

            except Exception as e:
                ai_result = {
                    "saved": False,
                    "error": str(e),
                }
                db.table("profit_events").update({
                    "last_gmail_message_id": message_id,
                }).eq("company_id", x_company_id).eq("id", event_id).execute()

            detected.append({
                "profit_event_id": event_id,
                "customer_id": customer_id,
                "message_id": message_id,
                "thread_id": thread_id,
                "from": from_raw,
                "subject": subject,
                "date": date,
                "body": clean_body[:1000],
                "reply_log": (reply_log.data or [None])[0],
                "timeline_event": (timeline.data or [None])[0],
                "ai_result": ai_result,
            })

    return {
        "checked": True,
        "mode": "thread_based",
        "events_checked": len(events),
        "count": len(detected),
        "items": detected,
    }
