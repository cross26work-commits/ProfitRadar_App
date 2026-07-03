from app.engines.revenue_engine import analyze_email
from app.repositories.profit_event_repository import ProfitEventRepository
from app.services.event_service import EventService


class RevenueService:
    def __init__(
        self,
        repository: ProfitEventRepository | None = None,
        event_service: EventService | None = None,
    ):
        self.repository = repository
        self.event_service = event_service

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
                "events": None,
            }

        profit_event = self.repository.create_profit_event(
            company_id=company_id,
            payload={
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
            "events": events,
        }
