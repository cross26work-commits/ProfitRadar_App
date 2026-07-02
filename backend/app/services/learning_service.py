from app.repositories.learning_repository import LearningRepository


class LearningService:
    def __init__(self, repository: LearningRepository):
        self.repository = repository

    def record(self, company_id: str, event_type: str, payload: dict):
        return self.repository.record_event(company_id, event_type, payload)
