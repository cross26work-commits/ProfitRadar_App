from .base_repository import BaseRepository


class LearningRepository(BaseRepository):
    def record_event(self, company_id: str, event_type: str, payload: dict):
        self.require_company_id(company_id)
        return {
            "company_id": company_id,
            "event_type": event_type,
            "payload": payload,
        }
