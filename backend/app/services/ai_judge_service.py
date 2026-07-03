from app.engines.ai_judge import judge_email
from app.repositories.ai_judgement_repository import AIJudgementRepository


class AIJudgeService:
    def __init__(self, repository: AIJudgementRepository | None = None):
        self.repository = repository

    def judge(self, company_id: str, payload: dict):
        if not company_id:
            raise ValueError("company_id is required")

        subject = payload.get("subject", "")
        sender = payload.get("sender", "")
        body = payload.get("body", "") or payload.get("content", "")

        result = judge_email(subject=subject, sender=sender, body=body)

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
