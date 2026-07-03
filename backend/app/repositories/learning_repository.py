from .base_repository import BaseRepository


class LearningRepository(BaseRepository):
    def record_event(self, company_id: str, event_type: str, payload: dict):
        self.require_company_id(company_id)

        data = {
            "company_id": company_id,
            "event_type": event_type,
            "input_data": payload.get("input_data", payload),
            "result_data": payload.get("result_data", {}),
            "customer_id": payload.get("customer_id"),
            "profit_event_id": payload.get("profit_event_id"),
            "success": payload.get("success"),
            "actual_profit": payload.get("actual_profit", 0),
        }

        response = self.db.table("learning_logs").insert(data).execute()
        rows = response.data or []
        return rows[0] if rows else data
