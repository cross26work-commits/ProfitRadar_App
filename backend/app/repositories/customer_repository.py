from .base_repository import BaseRepository


class CustomerRepository(BaseRepository):
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

    def get_customer(self, company_id: str, customer_id: str):
        self.require_company_id(company_id)

        response = (
            self.db.table("customers")
            .select("*")
            .eq("company_id", company_id)
            .eq("id", customer_id)
            .limit(1)
            .execute()
        )

        rows = response.data or []
        return rows[0] if rows else None
