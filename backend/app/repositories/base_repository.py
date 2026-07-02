from typing import Any


class BaseRepository:
    def __init__(self, db: Any):
        self.db = db

    @staticmethod
    def require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required")
