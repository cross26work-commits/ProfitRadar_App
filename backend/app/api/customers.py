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


@router.get("/{customer_id}")
def get_customer(customer_id: int):
    return {
        "id": customer_id,
        "name": "株式会社サンプル",
        "contact": "佐藤様",
        "email": "sample@example.com",
        "status": "商談中",
        "next_action": "本日中に再フォロー",
    }


@router.get("/{customer_id}/leads")
def get_customer_leads(customer_id: int):
    return {
        "items": [
            {
                "id": 1,
                "customer": "株式会社サンプル",
                "subject": "見積のご確認について",
                "priority": "high",
                "status": "waiting_reply",
                "estimated_profit": 120000,
                "recoverable_profit": 100000,
                "delay_days": 3,
                "href": "/leads/1",
            }
        ]
    }


@router.get("/{customer_id}/timeline")
def get_customer_timeline(customer_id: int):
    return {
        "items": [
            {
                "type": "mail",
                "title": "フォローメール送信",
                "body": "見積確認メールを送信",
                "time": "今日 10:30",
            },
            {
                "type": "sms",
                "title": "SMS送信予定",
                "body": "返信がなければSMS確認",
                "time": "今日 18:00",
            },
        ]
    }
