from app.repositories.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository

    def list_customers(self, company_id: str):
        return self.repository.list_customers(company_id)

    def get_customer(self, company_id: str, customer_id: str):
        return self.repository.get_customer(company_id, customer_id)
