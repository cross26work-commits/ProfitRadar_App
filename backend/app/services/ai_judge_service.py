from app.engines.ai_judge import judge_email
from app.repositories.ai_judgement_repository import AIJudgementRepository
from app.core.supabase_client import get_supabase_client
from app.services.billing import require_use
from app.services.ai_usage import measured_generation
from fastapi import HTTPException


class AIJudgeService:
    def __init__(self, repository: AIJudgementRepository | None = None):
        self.repository = repository

    def judge(self, company_id: str, payload: dict):
        if not company_id:
            raise ValueError("company_id is required")

        subject = payload.get("subject", "")
        sender = payload.get("sender", "")
        body = payload.get("body", "") or payload.get("content", "")
        if not isinstance(body,str) or len(body)>30000:
            raise HTTPException(413,"Analysis input exceeds limit")
        db=self.repository.db if self.repository else get_supabase_client()
        event=None
        for table,key in (("customers","customer_id"),("profit_events","profit_event_id")):
            if payload.get(key):
                rows=db.table(table).select("*").eq("company_id",company_id).eq("id",payload[key]).limit(1).execute().data
                if not rows: raise HTTPException(404,"Analysis resource not found")
                if table=="profit_events": event=rows[0]
        if event and payload.get("customer_id") and event.get("customer_id")!=payload["customer_id"]:
            raise HTTPException(403,"Analysis relationship mismatch")
        require_use(db,company_id)
        result = measured_generation(db,company_id,lambda: judge_email(subject=subject, sender=sender, body=body))

        return {
            "company_id": company_id,
            "input": {
                "subject": subject,
                "sender": sender,
                "body": body,
            },
            "result": result,
        }

    def judge_and_save(self, company_id: str, payload: dict):
        if not self.repository:
            raise RuntimeError("repository is required")

        judgement = self.judge(company_id, payload)
        result = judgement["result"]

        saved = self.repository.create_judgement(
            company_id=company_id,
            payload={
                "customer_id": payload.get("customer_id"),
                "profit_event_id": payload.get("profit_event_id"),
                "provider": result.get("provider", "fallback"),
                "score": int(payload.get("score") or 0),
                "priority": result.get("risk_level", "中"),
                "risk": result.get("risk_level", "中"),
                "reason": result.get("reason", ""),
                "next_action": result.get("next_action", ""),
                "raw_input": judgement["input"],
                "raw_output": result,
            },
        )

        return {
            **judgement,
            "saved": True,
            "ai_judgement": saved,
        }
