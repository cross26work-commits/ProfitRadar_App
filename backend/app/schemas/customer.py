from pydantic import BaseModel


class CustomerItem(BaseModel):
    id: int
    name: str
    leads: int
    profit: int
    last: str
    href: str | None = None


class CustomerListResponse(BaseModel):
    items: list[CustomerItem]
    message: str = "customers loaded"
