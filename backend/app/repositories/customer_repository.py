from .base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    def list_customers(self, company_id: str):
        self.require_company_id(company_id)
        return []

    def get_customer(self, company_id: str, customer_id: str):
        self.require_company_id(company_id)
        return None
