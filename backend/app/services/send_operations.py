import hashlib
import json
from fastapi import HTTPException
from postgrest.exceptions import APIError
from email.utils import getaddresses


def identity(company_id, event_id, recipient, subject, body):
    raw = json.dumps([company_id,event_id,recipient,subject,body], ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def claim(db, company_id, event_id, recipient, subject, body, customer_id):
    # Content-addressed identity survives browser reload and HTTP retries.
    key = identity(company_id,event_id,recipient,subject,body)
    row = {"company_id": company_id, "profit_event_id": event_id, "customer_id":customer_id, "operation_id": key,
           "request_hash": key, "status": "sending", "recipient": recipient, "subject": subject, "body": body}
    try:
        db.table("gmail_send_operations").insert(row).execute()
        return key, True, "sending"
    except APIError as exc:
        if exc.code != "23505":
            raise HTTPException(503, "Send preparation unavailable; nothing sent") from None
        rows = db.table("gmail_send_operations").select("status").eq("company_id",company_id).eq("operation_id",key).execute().data
        return key, False, rows[0]["status"] if rows else "unknown"


def finalize(db, company_id, key, result):
    db.rpc("finalize_gmail_send", {"p_company_id":company_id,"p_operation_id":key,
        "p_message_id":result.get("id"),"p_thread_id":result.get("threadId")}).execute()


def execute_once(db, company_id, key, send):
    try:
        result = send()
        finalize(db, company_id, key, result)
    except Exception:
        # A timeout cannot establish whether Gmail accepted the message.
        try:
            db.table("gmail_send_operations").update({"status":"unknown"}).eq("company_id",company_id).eq("operation_id",key).eq("status","sending").execute()
        except Exception:
            pass  # Persisted 'sending' is also unresolved and cannot be resent.
        return {"sent":False,"status":"unknown","operation_id":key}
    return {"sent":True,"status":"sent","operation_id":key}


def reconcile(db, company_id, row, service, connected_email):
    key = row["operation_id"]
    if row["status"] == "sent":
        return {"sent": True, "status": "sent"}
    message_id = f"<pr-{key}@profitradar.invalid>"
    try:
        response = service.users().messages().list(userId="me", q=f"in:sent rfc822msgid:{message_id}", maxResults=2).execute()
        matches = response.get("messages", [])
        if len(matches) != 1:
            return {"sent":False,"status":"unknown"}
        detail = service.users().messages().get(userId="me", id=matches[0]["id"], format="metadata", metadataHeaders=["Message-ID","From","To","Subject"]).execute()
        headers = {h["name"].lower(): h["value"] for h in detail.get("payload",{}).get("headers",[])}
        recipients = [addr.lower() for _,addr in getaddresses([headers.get("to","")])]
        senders = [addr.lower() for _,addr in getaddresses([headers.get("from","")])]
        if (headers.get("message-id") != message_id or "SENT" not in detail.get("labelIds",[])
                or recipients != [row["recipient"]] or senders != [connected_email.lower()]
                or headers.get("subject") != row["subject"]):
            return {"sent":False,"status":"unknown"}
        finalize(db,company_id,key,detail)
        return {"sent":True,"status":"sent"}
    except Exception:
        return {"sent":False,"status":"unknown"}
