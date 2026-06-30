from fastapi import APIRouter
from app.schemas.customer import CustomerItem, CustomerListResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=CustomerListResponse)
def list_customers():
    return CustomerListResponse(
        items=[
            CustomerItem(
                id=1,
                name="株式会社サンプル",
                leads=4,
                profit=320000,
                last="今日",
                href="/customers/1",
            )
        ]
    )
