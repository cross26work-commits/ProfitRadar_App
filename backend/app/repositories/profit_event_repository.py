from .base_repository import BaseRepository


class ProfitEventRepository(BaseRepository):
    def create_profit_event(self, company_id: str, payload: dict):
        self.require_company_id(company_id)

        data = {
            **payload,
            "company_id": company_id,
        }

        response = self.db.table("profit_events").insert(data).execute()
        rows = response.data or []
        return rows[0] if rows else data
