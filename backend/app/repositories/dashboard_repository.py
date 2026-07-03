from .base_repository import BaseRepository


class DashboardRepository(BaseRepository):
    def list_profit_events(self, company_id: str):
        self.require_company_id(company_id)

        response = (
            self.db.table("profit_events")
            .select("*")
            .eq("company_id", company_id)
            .order("updated_at", desc=True)
            .execute()
        )

        return response.data or []

    def list_customers(self, company_id: str):
        self.require_company_id(company_id)

        response = (
            self.db.table("customers")
            .select("*")
            .eq("company_id", company_id)
            .order("updated_at", desc=True)
            .execute()
        )

        return response.data or []

    def list_recent_timeline(self, company_id: str, limit: int = 10):
        self.require_company_id(company_id)

        response = (
            self.db.table("timeline")
            .select("*")
            .eq("company_id", company_id)
            .order("occurred_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data or []
