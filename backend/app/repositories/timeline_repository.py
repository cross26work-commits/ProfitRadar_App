from .base_repository import BaseRepository


class TimelineRepository(BaseRepository):
    def list_timeline(self, company_id: str, customer_id: str | None = None):
        self.require_company_id(company_id)

        query = (
            self.db.table("timeline")
            .select("*")
            .eq("company_id", company_id)
            .order("occurred_at", desc=True)
        )

        if customer_id:
            query = query.eq("customer_id", customer_id)

        response = query.execute()
        return response.data or []

    def create_event(self, company_id: str, payload: dict):
        self.require_company_id(company_id)

        data = {
            **payload,
            "company_id": company_id,
        }

        response = self.db.table("timeline").insert(data).execute()
        rows = response.data or []
        return rows[0] if rows else data
