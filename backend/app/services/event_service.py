from app.repositories.learning_repository import LearningRepository
from app.repositories.timeline_repository import TimelineRepository


class EventService:
    def __init__(
        self,
        timeline_repository: TimelineRepository,
        learning_repository: LearningRepository,
    ):
        self.timeline_repository = timeline_repository
        self.learning_repository = learning_repository

    def profit_detected(
        self,
        company_id: str,
        profit_event: dict,
    ):
        timeline_event = self.timeline_repository.create_event(
            company_id=company_id,
            payload={
                "customer_id": profit_event.get("customer_id"),
                "profit_event_id": profit_event.get("id"),
                "event_type": "profit_detected",
                "channel": "system",
                "title": "利益候補を検出",
                "description": f"{profit_event.get('title', '利益候補')} / 見込利益 ¥{int(profit_event.get('estimated_profit') or 0):,}",
                "amount": int(profit_event.get("estimated_profit") or 0),
                "metadata": {
                    "source": "revenue_engine",
                    "opportunity_score": profit_event.get("opportunity_score"),
                    "risk_level": profit_event.get("risk_level"),
                    "next_action": profit_event.get("next_action"),
                },
            },
        )

        learning_event = self.learning_repository.record_event(
            company_id=company_id,
            event_type="profit_detected",
            payload={
                "customer_id": profit_event.get("customer_id"),
                "profit_event_id": profit_event.get("id"),
                "input_data": profit_event,
                "result_data": {
                    "estimated_profit": profit_event.get("estimated_profit"),
                    "opportunity_score": profit_event.get("opportunity_score"),
                    "hot_lead": profit_event.get("hot_lead"),
                },
                "success": True,
                "actual_profit": int(profit_event.get("actual_profit") or 0),
            },
        )

        return {
            "timeline_event": timeline_event,
            "learning_event": learning_event,
        }
