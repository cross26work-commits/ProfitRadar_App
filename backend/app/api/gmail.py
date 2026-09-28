import os
from app.core.token_vault import encrypt, decrypt
from app.services.gmail_credentials import credentials_for_connection
from app.services.gmail_reconnection import merge_refresh
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import PyJWTError as JWTError

from fastapi import APIRouter, Depends, HTTPException, Header
import secrets
from app.services import gmail_work
from fastapi.responses import RedirectResponse
from app.core.supabase_client import get_supabase_client
from app.core.company_context import get_current_company_id
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
]


def _oauth_state_secret() -> str:
    secret = (
        os.getenv("OAUTH_STATE_SECRET")
        or os.getenv("SUPABASE_JWT_SECRET")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="OAuth state secret is not configured",
        )

    return secret


def _create_oauth_state(company_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "company_id": company_id,
        "purpose": "gmail_oauth",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }

    return jwt.encode(
        payload,
        _oauth_state_secret(),
        algorithm="HS256",
    )


def _decode_oauth_state(state: str) -> str:
    try:
        payload = jwt.decode(
            state,
            _oauth_state_secret(),
            algorithms=["HS256"],
            options={"verify_aud": False,"require":["exp","iat","company_id","purpose"]},
        )
    except JWTError:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state",
        )

    if payload.get("purpose") != "gmail_oauth":
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state purpose",
        )

    company_id = payload.get("company_id")

    if not company_id:
        raise HTTPException(
            status_code=400,
            detail="OAuth state company_id is missing",
        )

    return company_id


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
def gmail_status(
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    res = (
        db.table("gmail_connections")
        .select("id,email,status,created_at")
        .eq("company_id", company_id)
        .eq("status", "connected")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = res.data or []

    cursor = db.table("gmail_sync_cursors").select("mode,last_page_at,last_successful_sync").eq("company_id",company_id).limit(1).execute().data or []
    runs = db.table("gmail_company_sync_runs").select("status,started_at,finished_at,detected_count,error_code").eq("company_id",company_id).order("started_at",desc=True).limit(1).execute().data or []
    return {
        "connected": bool(rows),
        "connection": rows[0] if rows else None,
        "sync": cursor[0] if cursor else None,
        "last_run": runs[0] if runs else None,
        "message": "gmail connection status loaded",
    }


@router.get("/auth-url")
def gmail_auth_url(
    company_id: str = Depends(get_current_company_id),
):
    from app.services.billing import require_use
    require_use(get_supabase_client(),company_id)
    cfg = _client_config()

    flow = Flow.from_client_config(
        cfg["config"],
        scopes=SCOPES,
        redirect_uri=cfg["redirect_uri"],
        autogenerate_code_verifier=False,
    )

    oauth_state = _create_oauth_state(company_id)

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=oauth_state,
    )

    return {
        "auth_url": auth_url,
        "state": state,
        "company_id": company_id,
        "scopes": SCOPES,
    }


@router.get("/callback")
def gmail_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    # Cover provider construction, token exchange, profile lookup and DB storage.
    # Never log exception strings, request URLs, authorization codes or traceback.
    try:
        if code and state and not error:
            company_id = _decode_oauth_state(state)
            from app.services.billing import require_use
            require_use(get_supabase_client(),company_id)
            with gmail_work.company_lock(get_supabase_client(),company_id,"oauth"):
                return _complete_gmail_callback(code,state,error)
        return _complete_gmail_callback(code, state, error)
    except Exception:
        frontend_url = (os.getenv("FRONTEND_URL") or "http://localhost:3000").rstrip("/")
        return RedirectResponse(url=f"{frontend_url}/settings/mail?gmail=oauth_failed", status_code=302)


def _complete_gmail_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    frontend_url = (
        os.getenv("FRONTEND_URL")
        or "http://localhost:3000"
    ).rstrip("/")

    if error:
        return RedirectResponse(
            url=f"{frontend_url}/settings/mail?gmail=cancelled",
            status_code=302,
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{frontend_url}/settings/mail?gmail=error",
            status_code=302,
        )

    company_id = _decode_oauth_state(state)

    cfg = _client_config()

    flow = Flow.from_client_config(
        cfg["config"],
        scopes=SCOPES,
        redirect_uri=cfg["redirect_uri"],
        autogenerate_code_verifier=False,
    )

    try:
        flow.fetch_token(code=code)
    except Exception:
        return RedirectResponse(url=f"{frontend_url}/settings/mail?gmail=oauth_failed", status_code=302)

    credentials = flow.credentials

    gmail_service = build(
        "gmail",
        "v1",
        credentials=credentials,
    )

    gmail_profile = (
        gmail_service.users()
        .getProfile(userId="me")
        .execute()
    )

    connected_email = (
        gmail_profile.get("emailAddress") or ""
    ).strip()

    if not connected_email:
        raise HTTPException(
            status_code=400,
            detail="Connected Gmail address could not be determined",
        )

    token_json = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
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

    token_json=merge_refresh(company_id,connected_email,token_json,(existing.data or [None])[0])
    payload = {
        "company_id": company_id,
        "email": connected_email,
        "token_json": encrypt(company_id, token_json),
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
    except Exception:
        return RedirectResponse(url=f"{frontend_url}/settings/mail?gmail=oauth_failed", status_code=302)

    return RedirectResponse(
        url=f"{frontend_url}/settings/mail?gmail=connected",
        status_code=302,
    )


import base64
from email.utils import parseaddr
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@router.delete("/disconnect")
def gmail_disconnect(
    company_id: str = Depends(get_current_company_id),
):
    from app.services.gmail_revocation import disconnect
    db=get_supabase_client()
    with gmail_work.company_lock(db,company_id,"disconnect"):
        return disconnect(db, company_id)


@router.post("/send-test")
def gmail_send_test(
    payload: dict,
    company_id: str = Depends(get_current_company_id),
):
    if os.getenv("APP_ENV", "").lower() not in {"development", "test"}:
        raise HTTPException(status_code=404, detail="Not found")
    db = get_supabase_client()

    conn_res = (
        db.table("gmail_connections")
        .select("*")
        .eq("company_id", company_id)
        .eq("status", "connected")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = conn_res.data or []
    if not rows:
        raise HTTPException(status_code=400, detail="Gmail is not connected")

    credentials = credentials_for_connection(db, company_id, rows[0])

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



@router.get("/replies")
def gmail_replies(
    limit: int = 20,
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()

    safe_limit = max(1, min(int(limit or 20), 100))

    # 履歴そのものはDBにすべて保持する。
    # UI用の /gmail/replies では、
    # 1案件につき最新の受信返信1件だけを返す。
    #
    # safe_limit をDB取得前に適用すると、
    # 同一案件の古い返信だけで枠を消費して
    # 他案件が取得できない可能性があるため、
    # まず十分な件数を新しい順で取得する。
    fetch_limit = min(
        max(safe_limit * 10, 100),
        500,
    )

    reply_res = (
        db.table("reply_logs")
        .select("*")
        .eq("company_id", company_id)
        .eq("channel", "gmail")
        .order("created_at", desc=True)
        .limit(fetch_limit)
        .execute()
    )

    all_reply_rows = reply_res.data or []

    latest_by_event = {}
    orphan_replies = []

    for row in all_reply_rows:
        event_id = row.get(
            "profit_event_id"
        )

        if event_id:
            # created_at DESC で取得しているので、
            # 最初に見つかったものがその案件の最新返信。
            if event_id not in latest_by_event:
                latest_by_event[event_id] = row
        else:
            # 案件に紐付いていない返信は
            # 誤って別返信と統合せず個別に残す。
            orphan_replies.append(row)

    reply_rows = (
        list(latest_by_event.values())
        + orphan_replies
    )

    reply_rows.sort(
        key=lambda row: (
            row.get("created_at")
            or row.get("reply_at")
            or ""
        ),
        reverse=True,
    )

    reply_rows = reply_rows[:safe_limit]

    timeline_res = (
        db.table("timeline")
        .select("*")
        .eq("company_id", company_id)
        .eq("event_type", "gmail_reply_detected")
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )

    timeline_rows = timeline_res.data or []

    timeline_by_message = {}

    for row in timeline_rows:
        metadata = row.get("metadata") or {}

        if not isinstance(metadata, dict):
            metadata = {}

        message_id = metadata.get("gmail_message_id")

        if message_id:
            timeline_by_message[message_id] = row

    event_cache = {}
    customer_cache = {}
    judgement_cache = {}

    items = []

    for reply in reply_rows:
        event_id = reply.get("profit_event_id")
        customer_id = reply.get("customer_id")
        message_id = (
            reply.get("gmail_message_id")
            or reply.get("external_id")
        )

        timeline = (
            timeline_by_message.get(message_id)
            or {}
        )

        metadata = timeline.get("metadata") or {}

        if not isinstance(metadata, dict):
            metadata = {}

        event = None

        if event_id:
            if event_id not in event_cache:
                event_res = (
                    db.table("profit_events")
                    .select("*")
                    .eq("company_id", company_id)
                    .eq("id", event_id)
                    .limit(1)
                    .execute()
                )

                event_cache[event_id] = (
                    (event_res.data or [None])[0]
                )

            event = event_cache.get(event_id)

        if not customer_id and event:
            customer_id = event.get("customer_id")

        judgement = None

        if event_id:
            if event_id not in judgement_cache:
                judgement_res = (
                    db.table("ai_judgements")
                    .select("*")
                    .eq("company_id", company_id)
                    .eq("profit_event_id", event_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )

                judgement_cache[event_id] = (
                    (judgement_res.data or [None])[0]
                )

            judgement = judgement_cache.get(event_id)

        customer = None

        if customer_id:
            if customer_id not in customer_cache:
                customer_res = (
                    db.table("customers")
                    .select("*")
                    .eq("company_id", company_id)
                    .eq("id", customer_id)
                    .limit(1)
                    .execute()
                )

                customer_cache[customer_id] = (
                    (customer_res.data or [None])[0]
                )

            customer = customer_cache.get(customer_id)

        items.append({
            "id": reply.get("id"),
            "profit_event_id": event_id,
            "customer_id": customer_id,

            "customer_name": (
                (customer or {}).get("name")
                or (customer or {}).get("company_name")
                or metadata.get("from")
                or metadata.get("from_email")
                or "顧客"
            ),

            "customer_email": (
                (customer or {}).get("email")
                or metadata.get("from_email")
                or ""
            ),

            "subject": (
                metadata.get("subject")
                or (event or {}).get("title")
                or "Gmail返信"
            ),

            "body": reply.get("reply_body") or "",

            "received_at": (
                timeline.get("created_at")
                or reply.get("reply_at")
                or reply.get("created_at")
                or ""
            ),

            "gmail_message_id": message_id,

            "gmail_thread_id": (
                reply.get("gmail_thread_id")
                or reply.get("thread_id")
            ),

            "event_title": (
                (event or {}).get("title")
                or "案件"
            ),

            "next_action": (
                (event or {}).get("next_action")
                or ""
            ),

            "estimated_profit": int(
                (event or {}).get("estimated_profit")
                or 0
            ),

            "risk_level": (
                (event or {}).get("risk_level")
                or ""
            ),

            "ai_judgement": judgement,

            "analysis": (
                (judgement or {}).get("raw_output")
                or {}
            ),
        })

    items.sort(
        key=lambda item: item.get("received_at") or "",
        reverse=True,
    )

    return {
        "count": len(items),
        "items": items,
    }


@router.post("/check-replies")
def gmail_check_replies(
    payload: dict | None = None,
    company_id: str = Depends(get_current_company_id),
):
    db = get_supabase_client()
    return gmail_work.sync_company(db,company_id,lambda: _check_replies(payload,company_id))


@router.post("/scheduled-sync")
def scheduled_sync(x_scheduler_secret: str | None = Header(default=None)):
    expected=os.getenv("GMAIL_SCHEDULER_SECRET", "")
    if not expected:
        raise HTTPException(503,"Scheduler is not configured")
    if not x_scheduler_secret or not secrets.compare_digest(expected,x_scheduler_secret):
        raise HTTPException(401,"Invalid scheduler credentials")
    db=get_supabase_client()
    connections=db.table("gmail_connections").select("company_id").eq("status","connected").order("company_id").limit(100).execute().data or []
    ids=list(dict.fromkeys(row["company_id"] for row in connections))
    def work(cid):
        recent=(db.table("gmail_company_sync_runs").select("status,started_at,finished_at")
                .eq("company_id",cid).order("started_at",desc=True).limit(5).execute().data or [])
        if not gmail_work.retry_due(recent):
            return {"deferred":True}
        return gmail_work.sync_company(db,cid,lambda: _check_replies({"max_events":50},cid))
    return gmail_work.batch(ids,work)


def _check_replies(payload, company_id):
    from app.services.gmail_sync import SyncStore, synchronize
    db=get_supabase_client()
    rows=db.table("gmail_connections").select("*").eq("company_id",company_id).eq("status","connected").execute().data or []
    if len(rows)!=1:
        raise HTTPException(409,"Exactly one connected Gmail account is required")
    connection=rows[0]
    credentials=credentials_for_connection(db,company_id,connection)
    service=build("gmail","v1",credentials=credentials)
    return synchronize(service,SyncStore(db,company_id,connection),connection["email"].lower())
