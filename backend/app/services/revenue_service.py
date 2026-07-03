from app.engines.revenue_engine import analyze_email
from app.repositories.ai_judgement_repository import AIJudgementRepository
from app.repositories.profit_event_repository import ProfitEventRepository
from app.services.ai_judge_service import AIJudgeService
from app.services.event_service import EventService
from app.services.customer_resolver_service import CustomerResolverService


class RevenueService:
    def __init__(
        self,
        repository: ProfitEventRepository | None = None,
        event_service: EventService | None = None,
        customer_resolver: CustomerResolverService | None = None,
    ):
        self.repository = repository
        self.event_service = event_service
        self.customer_resolver = customer_resolver

    def analyze(self, company_id: str, payload: dict):
        if not company_id:
            raise ValueError("company_id is required")

        subject = payload.get("subject", "")
        body = payload.get("body", "") or payload.get("content", "")
        neglected_days = int(payload.get("neglected_days") or 7)

        result = analyze_email(
            subject=subject,
            body=body,
            neglected_days=neglected_days,
        )

        return {
            "company_id": company_id,
            "engine": "revenue_engine",
            "input": {
                "subject": subject,
                "body": body,
                "neglected_days": neglected_days,
            },
            "result": result,
        }

    def analyze_and_save(self, company_id: str, payload: dict):
        if not self.repository:
            raise RuntimeError("repository is required")

        analysis = self.analyze(company_id, payload)
        result = analysis["result"]

        if not result.get("is_profit_lead"):
            return {
                **analysis,
                "saved": False,
                "profit_event": None,
                "ai_judgement": None,
                "events": None,
            }

        body = payload.get("body", "") or payload.get("content", "")
        customer = None

        if self.customer_resolver:
            customer = self.customer_resolver.resolve(
                company_id=company_id,
                payload=payload,
            )

        profit_event = self.repository.create_profit_event(
            company_id=company_id,
            payload={
                "customer_id": customer.get("id") if customer else None,
                "title": payload.get("subject", "利益候補"),
                "status": "open",
                "category": result.get("category"),
                "estimated_profit": result.get("estimated_profit", 0),
                "actual_profit": 0,
                "opportunity_score": result.get("opportunity_score", 0),
                "roi_score": result.get("opportunity_score", 0),
                "hot_lead": bool(result.get("hot_lead")),
                "risk_level": result.get("risk_level", "medium"),
                "next_action": result.get("next_action"),
            },
        )

        ai_judgement = None
        if self.repository:
            judge_service = AIJudgeService(
                repository=AIJudgementRepository(db=self.repository.db)
            )
            ai_judgement = judge_service.judge_and_save(
                company_id=company_id,
                payload={
                    "subject": payload.get("subject", ""),
                    "body": payload.get("body", "") or payload.get("content", ""),
                    "sender": payload.get("sender", ""),
                    "customer_id": customer.get("id") if customer else None,
                    "profit_event_id": profit_event.get("id"),
                    "score": result.get("opportunity_score", 0),
                },
            )

        events = None
        if self.event_service:
            events = self.event_service.profit_detected(
                company_id=company_id,
                profit_event=profit_event,
            )

        return {
            **analysis,
            "saved": True,
            "profit_event": profit_event,
            "ai_judgement": ai_judgement,
            "events": events,
        }
