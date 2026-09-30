"""Public support intake and separately authorized support administration."""
from datetime import datetime, timezone
import hashlib
import hmac
import os
import re
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.admin_auth import require_support_admin
from app.core.supabase_client import get_supabase_client
from app.services.support_email import send_plain_text


public_router = APIRouter(prefix="/support", tags=["support"])
admin_router = APIRouter(prefix="/admin/support", tags=["admin-support"])
Category = Literal["general", "technical", "billing", "cancellation", "refund",
                   "commercial_disclosure", "privacy_deletion", "other"]
Status = Literal["unhandled", "in_progress", "completed"]
Priority = Literal["low", "normal", "high", "urgent"]
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ContactInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    company_name: str | None = Field(default=None, max_length=200)
    category: Category
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=10, max_length=5000)
    form_started_at: datetime
    website: str = Field(default="", max_length=200)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL.fullmatch(normalized):
            raise ValueError("invalid email")
        return normalized

    @field_validator("name", "subject", "body")
    @classmethod
    def visible_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or any(ord(char) < 32 and char not in "\n\t" for char in normalized):
            raise ValueError("invalid text")
        return normalized


class AdminUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status
    priority: Priority


class NoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=5000)


class ReplyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    idempotency_key: str = Field(min_length=16, max_length=100)


def _safe_origin(request: Request, intent: str | None) -> None:
    if intent != "public-form-v1":
        raise HTTPException(403, "Contact form validation failed")
    expected = os.getenv("FRONTEND_URL", "").rstrip("/")
    origin = (request.headers.get("origin") or "").rstrip("/")
    if os.getenv("APP_ENV") == "production" and (not expected or origin != expected):
        raise HTTPException(403, "Contact form validation failed")
    if origin and expected and origin != expected:
        raise HTTPException(403, "Contact form validation failed")


def _abuse_key(request: Request, email: str) -> str:
    secret = os.getenv("CONTACT_RATE_LIMIT_SECRET", "")
    if not secret and os.getenv("APP_ENV") in {"development", "test"}:
        secret = "development-contact-rate-limit"
    if len(secret) < 24:
        raise HTTPException(503, "Contact service unavailable")
    address = request.client.host if request.client else "unknown"
    return hmac.new(secret.encode(), f"{address}|{email}".encode(), hashlib.sha256).hexdigest()


def _request_dto(row: dict) -> dict:
    allowed = ("id", "public_request_id", "requester_name", "requester_email", "company_name",
               "category", "subject", "body", "status", "priority", "legal_disclosure",
               "started_at", "answered_at", "created_at", "updated_at")
    return {name: row.get(name) for name in allowed}


@public_router.post("/contact", status_code=201)
def create_contact(payload: ContactInput, request: Request,
                   x_contact_intent: str | None = Header(default=None)):
    _safe_origin(request, x_contact_intent)
    now = datetime.now(timezone.utc)
    started = payload.form_started_at
    if started.tzinfo is None:
        raise HTTPException(422, "Form timestamp required")
    elapsed = (now - started.astimezone(timezone.utc)).total_seconds()
    if payload.website or elapsed < 2 or elapsed > 7200:
        raise HTTPException(422, "Contact form validation failed")
    public_id = "PR-" + now.strftime("%Y%m%d") + "-" + uuid4().hex[:12].upper()
    args = {
        "p_public_request_id": public_id, "p_requester_user_id": None, "p_company_id": None,
        "p_requester_name": payload.name, "p_requester_email": payload.email,
        "p_company_name": payload.company_name, "p_category": payload.category,
        "p_subject": payload.subject, "p_body": payload.body,
        "p_abuse_key": _abuse_key(request, payload.email),
    }
    try:
        rows = get_supabase_client().rpc("create_support_request", args).execute().data or []
    except Exception as error:
        if getattr(error, "code", None) == "P0001":
            raise HTTPException(429, "Contact request limit reached") from None
        raise HTTPException(503, "Contact request could not be saved") from None
    if len(rows) != 1:
        raise HTTPException(503, "Contact request could not be saved")
    return {"accepted": True, "request_id": rows[0]["public_request_id"],
            "created_at": rows[0]["created_at"]}


@admin_router.get("")
def list_requests(status: Status | None = None, category: Category | None = None,
                  priority: Priority | None = None, search: str | None = Query(default=None, max_length=100),
                  _actor: str = Depends(require_support_admin)):
    query = get_supabase_client().table("support_requests").select("*").order("created_at", desc=True).limit(250)
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)
    if priority:
        query = query.eq("priority", priority)
    rows = query.execute().data or []
    if search:
        needle = search.casefold().strip()
        rows = [row for row in rows if any(needle in str(row.get(name) or "").casefold()
                for name in ("public_request_id", "requester_name", "requester_email", "company_name", "subject"))]
    return {"requests": [_request_dto(row) for row in rows]}


@admin_router.get("/{request_id}")
def request_detail(request_id: UUID, _actor: str = Depends(require_support_admin)):
    db = get_supabase_client()
    rows = db.table("support_requests").select("*").eq("id", str(request_id)).limit(1).execute().data or []
    if not rows:
        raise HTTPException(404, "Support request not found")
    return {
        "request": _request_dto(rows[0]),
        "messages": db.table("support_messages").select("id,direction,subject,body,recipient_email,thread_reference,sent_at,delivery_status,provider_message_id,failure_reason,admin_actor,created_at").eq("request_id", str(request_id)).order("created_at").execute().data or [],
        "notes": db.table("support_internal_notes").select("id,body,admin_actor,created_at").eq("request_id", str(request_id)).order("created_at").execute().data or [],
        "audit": db.table("support_audit_logs").select("id,action,admin_actor,metadata,created_at").eq("request_id", str(request_id)).order("created_at").execute().data or [],
    }


@admin_router.patch("/{request_id}")
def update_request(request_id: UUID, payload: AdminUpdate,
                   actor: str = Depends(require_support_admin)):
    rows = get_supabase_client().rpc("update_support_request_admin", {
        "p_request_id": str(request_id), "p_status": payload.status,
        "p_priority": payload.priority, "p_actor": actor,
    }).execute().data or []
    if len(rows) != 1:
        raise HTTPException(404, "Support request not found")
    return _request_dto(rows[0])


@admin_router.post("/{request_id}/notes", status_code=201)
def add_note(request_id: UUID, payload: NoteInput,
             actor: str = Depends(require_support_admin)):
    note_id = get_supabase_client().rpc("add_support_note_admin", {
        "p_request_id": str(request_id), "p_body": payload.body, "p_actor": actor,
    }).execute().data
    return {"created": True, "note_id": note_id}


@admin_router.post("/{request_id}/replies")
def reply(request_id: UUID, payload: ReplyInput,
          actor: str = Depends(require_support_admin)):
    db = get_supabase_client()
    reserved = db.rpc("reserve_support_reply", {
        "p_request_id": str(request_id), "p_subject": payload.subject,
        "p_body": payload.body, "p_actor": actor,
        "p_idempotency_key": payload.idempotency_key,
    }).execute().data or []
    if len(reserved) != 1:
        raise HTTPException(503, "Support reply could not be reserved")
    row = reserved[0]
    if not row["created"]:
        return {"duplicate": True, "delivery_status": row["delivery_status"]}
    try:
        delivery = send_plain_text(recipient=row["recipient_email"], subject=payload.subject,
                                   body=payload.body, thread_reference=row.get("thread_reference"))
        final_status, provider_id, reason = delivery.status, delivery.provider_message_id, None
    except Exception:
        final_status, provider_id, reason = "unknown", None, "PROVIDER_OUTCOME_UNKNOWN"
    saved = db.rpc("finalize_support_reply", {
        "p_message_id": row["message_id"], "p_status": final_status,
        "p_provider_message_id": provider_id, "p_failure_reason": reason,
        "p_actor": actor,
    }).execute().data
    if saved is not True:
        raise HTTPException(503, "Support reply result was not saved")
    if final_status == "unknown":
        raise HTTPException(503, "Support reply outcome requires review")
    return {"duplicate": False, "delivery_status": final_status}
