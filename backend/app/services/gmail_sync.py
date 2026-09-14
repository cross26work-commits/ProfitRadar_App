"""Bounded page-at-a-time sync. Each page and its cursor commit in one DB RPC.

Initial import: previous 30 days (including read mail), excluding spam/trash.
At most 5 pages/run; remaining pages persist, so this is not a mailbox item cap.
No provider send, AI call, or mark-as-read operation occurs here.
"""
import base64
import re
import time
from datetime import datetime, timezone
from email.utils import getaddresses
from html.parser import HTMLParser
from googleapiclient.errors import HttpError
from fastapi import HTTPException

INITIAL_DAYS = 30
PAGE_SIZE = 100
PAGES_PER_RUN = 5
COMMIT_SIZE = 500
DETAILS_PER_RUN = 500


def plain_text(payload):
    if payload.get("mimeType")=="text/html":
        class TextOnly(HTMLParser):
            def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.hidden=0
            def handle_starttag(self,tag,attrs):
                if tag in {"script","style"}:self.hidden+=1
                elif tag in {"br","p","div","li"}:self.parts.append("\n")
            def handle_endtag(self,tag):
                if tag in {"script","style"}:self.hidden=max(0,self.hidden-1)
            def handle_data(self,data):
                if not self.hidden:self.parts.append(data)
        data=payload.get("body",{}).get("data","")
        parser=TextOnly();parser.feed(base64.urlsafe_b64decode(data+"===").decode("utf-8",errors="replace")[:120000])
        return "".join(parser.parts)[:30000]
    if payload.get("mimeType", "text/plain") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")[:30000] if data else ""
    parts=payload.get("parts", [])
    if payload.get("mimeType")=="multipart/alternative":
        plain=[p for p in parts if p.get("mimeType")=="text/plain"]
        if plain:parts=plain
    return "\n".join(plain_text(part) for part in parts)[:30000]


def normalize(detail, own_email):
    labels=set(detail.get("labelIds", []))
    headers={h["name"].lower():h.get("value", "") for h in detail.get("payload", {}).get("headers", [])}
    addresses=getaddresses([headers.get("from", "")])
    if len(addresses)!=1:
        return None
    sender=addresses[0][1].strip().lower()
    if not re.fullmatch(r"[^\s<>@]+@[^\s<>@]+",sender) or sender==own_email.lower() or labels & {"SENT","DRAFT","SPAM","TRASH"}:
        return None
    body=plain_text(detail.get("payload", {}))
    subject=headers.get("subject", "")[:998]
    text=subject+"\n"+body
    # Conservative transparent candidate rule, never a revenue/contract assertion.
    suppressed=bool(re.search(r"配信停止|連絡不要|営業お断り|失注|unsubscribe",text,re.I))
    automated=bool(headers.get("list-unsubscribe") or headers.get("auto-submitted", "no").lower()!="no")
    candidate=not suppressed and not automated and bool(re.search(r"見積|問い合わせ|お問合せ|相談|依頼|発注|提案|商談|quotation|inquiry",text,re.I))
    return {"message_id":detail["id"],"thread_id":detail["threadId"],"sender":sender,
            "sender_name":addresses[0][0][:200] or sender,"subject":subject,"body":body,
            "received_at":datetime.fromtimestamp(int(detail["internalDate"])/1000,timezone.utc).isoformat(),
            "candidate":candidate,"suppressed":suppressed or automated,
            "reason":"営業関連語を検出・要確認" if candidate else "既存案件の受信"}


def expand_candidate_threads(service, records, mailbox, initial_since):
    """Recover earlier non-keyword replies when a later page finds an inquiry.

    Gmail lists newest first. Only expand a positively identified thread, same
    sender and initial import window. SENT/opt-out filtering remains unchanged.
    One thread request per matching thread per page; no send or AI calls.
    """
    selected = {r["message_id"]: r for r in records}
    candidates = {}
    for record in records:
        if record["candidate"]:
            candidates.setdefault(record["thread_id"], set()).add(record["sender"])
    for thread_id, senders in candidates.items():
        try:
            thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        except HttpError as exc:
            if exc.resp.status == 404:
                continue
            raise HTTPException(503, "Gmail thread unavailable") from None
        for detail in thread.get("messages", []):
            if int(detail["internalDate"]) < int(initial_since) * 1000:
                continue
            record = normalize(detail, mailbox)
            if record and record["sender"] in senders and record["thread_id"] == thread_id:
                if not record["suppressed"]:
                    record["candidate"] = True
                    record["reason"] = "同一送信者の商談関連スレッド・要確認"
                selected[record["message_id"]] = record
    # Establish the candidate before suppressed messages, even across chunks.
    return sorted(selected.values(), key=lambda r: (not r["candidate"], r["received_at"], r["message_id"]))


def normalize_sent_inquiry(detail,own_email):
    """Import a sent proposal as outgoing evidence, never as a received reply.

    Only exactly one To and no Cc/Bcc is eligible for automatic association.
    Alias senders and multi-recipient messages require manual review, not a guess.
    """
    headers={h["name"].lower():h.get("value","") for h in detail.get("payload",{}).get("headers",[])}
    from_addresses=getaddresses([headers.get("from","")]);to_addresses=getaddresses([headers.get("to","")])
    labels=set(detail.get("labelIds",[]))
    if ("SENT" not in labels or labels & {"DRAFT","SPAM","TRASH"} or len(from_addresses)!=1
            or from_addresses[0][1].lower()!=own_email.lower() or len(to_addresses)!=1
            or headers.get("cc","").strip() or headers.get("bcc","").strip()):return None
    name,address=to_addresses[0]
    peer_headers=[h for h in detail.get("payload",{}).get("headers",[]) if h["name"].lower()!="from"]
    peer_headers.append({"name":"From","value":f"{name} <{address}>"})
    record=normalize({**detail,"labelIds":[],"payload":{**detail.get("payload",{}),"headers":peer_headers}},own_email)
    if not record or not record["candidate"]:return None
    return {**record,"direction":"outgoing","reason":"単一宛先への営業関連送信・返信待ち要確認"}


class SyncStore:
    def __init__(self,db,company_id,connection):
        self.db,self.company_id,self.connection=db,company_id,connection
        locks=db.table("gmail_work_locks").select("owner_id").eq("company_id",company_id).eq("purpose","sync").execute().data or []
        if len(locks)!=1: raise HTTPException(409,"Sync lock required")
        self.owner_id=locks[0]["owner_id"]

    def load(self):
        rows=self.db.table("gmail_sync_cursors").select("*").eq("company_id",self.company_id).execute().data or []
        return rows[0] if rows else {"version":0}

    def commit(self,previous,next_state,records):
        persisted_state=dict(next_state)
        if persisted_state.get("pending_ids") is None:
            persisted_state["pending_ids"]=[]
        return self.db.rpc("commit_gmail_inbound_page",{
            "p_company_id":self.company_id,"p_owner_id":self.owner_id,
            "p_connection_id":self.connection["id"],"p_mailbox":self.connection["email"].lower(),
            "p_expected_version":previous["version"],"p_state":persisted_state,"p_records":records,
        }).execute().data


def synchronize(service,store,mailbox,max_pages=PAGES_PER_RUN,max_details=DETAILS_PER_RUN):
    state=store.load()
    count=0;processed=0
    def checkpoint(next_state,records):
        nonlocal state,count
        result=store.commit(state,next_state,records)
        count+=int(result["inserted"])
        state={**next_state,"version":result["version"],"mailbox":mailbox}
    def restart():
        anchor=service.users().getProfile(userId="me").execute()["historyId"]
        since=state.get("initial_since") if state.get("mailbox")==mailbox else None
        checkpoint({"mode":"full","history_id":anchor,"page_token":None,
                    "initial_since":since or int(time.time())-INITIAL_DAYS*86400},[])
    if not state.get("history_id") or state.get("mailbox")!=mailbox:
        restart()
    for _ in range(max_pages):
        try:
            if state.get("pending_ids"):
                ids=state["pending_ids"]
                page=state["pending_page"]
            elif state["mode"]=="full":
                page=service.users().messages().list(userId="me",maxResults=PAGE_SIZE,
                    q=f"after:{state['initial_since']}",includeSpamTrash=False,pageToken=state.get("page_token")).execute()
                ids=[item["id"] for item in page.get("messages",[])]
            else:
                page=service.users().history().list(userId="me",startHistoryId=state["history_id"],
                    historyTypes=["messageAdded"],maxResults=PAGE_SIZE,pageToken=state.get("page_token")).execute()
                ids=[item["message"]["id"] for h in page.get("history",[]) for item in h.get("messagesAdded",[])]
        except HttpError as exc:
            if (exc.resp.status==404 and state["mode"]=="delta") or (exc.resp.status==400 and state.get("page_token")):
                restart()
                continue
            raise HTTPException(503,"Gmail sync unavailable") from None
        ids=list(dict.fromkeys(ids))
        if ids and not state.get("pending_ids"):
            # Persist the exact listed IDs before taking an offset. Gmail pages
            # can change during retries; offsetting a re-fetched page loses mail.
            page={k:page[k] for k in ("nextPageToken","historyId") if k in page}
            checkpoint({**state,"pending_ids":ids,"pending_page":page,"caught_up":False},[])
        selected_ids=ids[:max_details-processed]
        records=[]
        for message_id in selected_ids:
            try:
                detail=service.users().messages().get(userId="me",id=message_id,format="full").execute()
            except HttpError as exc:
                if exc.resp.status==404: continue  # Deleted between list and get; do not pretend it was imported.
                raise HTTPException(503,"Gmail message unavailable") from None
            record=normalize(detail,mailbox) or normalize_sent_inquiry(detail,mailbox)
            if record: records.append(record)
        records = expand_candidate_threads(service, records, mailbox, state["initial_since"])
        remaining=ids[len(selected_ids):];processed+=len(selected_ids)
        next_state={**state,"page_token":page.get("nextPageToken"),"pending_ids":None,"pending_page":None}
        next_state["caught_up"]=state["mode"]=="delta" and not next_state["page_token"]
        if not next_state["page_token"]:
            if state["mode"]=="delta":
                next_state["history_id"]=page["historyId"]
            next_state["mode"]="delta"
        if remaining:
            next_state={**state,"pending_ids":remaining,"pending_page":page,"caught_up":False}
        # A history page can contain more messages than its history maxResults.
        # Partial chunks keep the old page cursor: retries replay the page and
        # receipt uniqueness removes already committed messages. Only the final
        # chunk advances it. A failed transaction cannot skip unsaved messages.
        for offset in range(0, max(1, len(records)), COMMIT_SIZE):
            chunk = records[offset:offset + COMMIT_SIZE]
            final_chunk = offset + COMMIT_SIZE >= len(records)
            checkpoint(next_state if final_chunk else {**state, "caught_up": False}, chunk)
        if not remaining and state["mode"]=="delta" and not state.get("page_token") and "historyId" in page:
            return {"checked":True,"count":count,"has_more":False,"mode":"incremental","items":[]}
        if processed>=max_details:break
    return {"checked":True,"count":count,"has_more":True,"mode":state["mode"],"items":[]}
