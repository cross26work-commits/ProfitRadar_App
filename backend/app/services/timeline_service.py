from app.repositories.timeline_repository import TimelineRepository


class TimelineService:
    def __init__(self, repository: TimelineRepository):
        self.repository = repository

    def list_timeline(self, company_id: str, customer_id: str | None = None):
        return self.repository.list_timeline(company_id, customer_id)

    def create_event(self, company_id: str, payload: dict):
        return self.repository.create_event(company_id, payload)
