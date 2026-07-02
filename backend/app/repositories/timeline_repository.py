from .base_repository import BaseRepository


class TimelineRepository(BaseRepository):
    def list_timeline(self, company_id: str, customer_id: str | None = None):
        self.require_company_id(company_id)
        return []

    def create_event(self, company_id: str, payload: dict):
        self.require_company_id(company_id)
        return payload
