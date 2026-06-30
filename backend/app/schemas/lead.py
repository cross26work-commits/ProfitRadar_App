from pydantic import BaseModel


class LeadItem(BaseModel):
    id: int
    customer: str
    subject: str
    priority: str
    status: str
    estimated_profit: int
    recoverable_profit: int
    delay_days: int
    href: str | None = None


class LeadListResponse(BaseModel):
    items: list[LeadItem]
    message: str = "leads loaded"
