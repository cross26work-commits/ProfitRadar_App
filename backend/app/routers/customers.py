from fastapi import APIRouter, Header, HTTPException

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


def get_service() -> CustomerService:
    try:
        return CustomerService(CustomerRepository(db=get_supabase_client()))
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("")
def list_customers(x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a")):
    service = get_service()
    return service.list_customers(company_id=x_company_id)


@router.get("/{customer_id}")
def get_customer(customer_id: str, x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a")):
    service = get_service()
    customer = service.get_customer(company_id=x_company_id, customer_id=customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")

    return customer
