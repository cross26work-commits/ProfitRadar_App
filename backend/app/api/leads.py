from fastapi import APIRouter
from app.schemas.lead import LeadItem, LeadListResponse

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads():
    return LeadListResponse(
        items=[
            LeadItem(
                id=1,
                customer="株式会社サンプル",
                subject="見積のご確認について",
                priority="high",
                status="waiting_reply",
                estimated_profit=120000,
                recoverable_profit=100000,
                delay_days=3,
                href="/leads/1",
            )
        ]
    )
