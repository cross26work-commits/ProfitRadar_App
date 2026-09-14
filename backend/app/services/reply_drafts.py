"""Tenant-bound saved drafts; never calls Gmail or AI."""
from datetime import datetime, timezone
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field


class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(max_length=50000)
    subject: str = Field(max_length=998)


def save(db, company_id, event_id, payload):
    rows = db.table("profit_events").select("id").eq("company_id", company_id).eq("id", event_id).limit(1).execute().data
    if not rows:
        raise HTTPException(status_code=404, detail="profit event not found")
    if "\r" in payload.subject or "\n" in payload.subject:
        raise HTTPException(status_code=422, detail="Invalid subject")
    db.table("reply_drafts").upsert({
        "company_id": company_id, "profit_event_id": event_id,
        "body": payload.body, "subject": payload.subject,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="company_id,profit_event_id").execute()
    return {"saved": True}


def load(db, company_id, event_id):
    rows = db.table("reply_drafts").select("body,subject,updated_at").eq("company_id", company_id).eq("profit_event_id", event_id).limit(1).execute().data
    return rows[0] if rows else None
