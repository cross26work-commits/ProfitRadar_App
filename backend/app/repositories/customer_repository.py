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

    def find_by_email(self, company_id: str, email: str):
        self.require_company_id(company_id)

        if not email:
            return None

        response = (
            self.db.table("customers")
            .select("*")
            .eq("company_id", company_id)
            .eq("email", email)
            .limit(1)
            .execute()
        )

        rows = response.data or []
        return rows[0] if rows else None

    def create_customer(self, company_id: str, payload: dict):
        self.require_company_id(company_id)

        data = {
            "company_id": company_id,
            "name": payload.get("name") or payload.get("email") or "顧客未設定",
            "email": payload.get("email"),
            "status": payload.get("status") or "active",
        }

        response = self.db.table("customers").insert(data).execute()
        rows = response.data or []
        return rows[0] if rows else data

    def find_or_create_by_email(self, company_id: str, email: str, name: str | None = None):
        if not email:
            return None

        existing = self.find_by_email(company_id=company_id, email=email)
        if existing:
            return existing

        return self.create_customer(
            company_id=company_id,
            payload={
                "email": email,
                "name": name or email,
            },
        )
