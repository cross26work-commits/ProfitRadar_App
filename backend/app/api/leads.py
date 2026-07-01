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


@router.get("/{lead_id}")
def get_lead(lead_id: int):
    return {
        "id": lead_id,
        "customer": "株式会社サンプル",
        "subject": "見積のご確認について",
        "priority": "high",
        "category": "見積",
        "status": "waiting_reply",
        "estimated_profit": 120000,
        "recoverable_profit": 100000,
        "delay_days": 3,
        "next_action": "本日中に確認フォロー",
        "body": "お世話になっております。先日いただいた見積内容について確認させてください。条件面を再度確認したうえで、進行可否をご連絡いたします。",
    }


@router.get("/{lead_id}/timeline")
def get_lead_timeline(lead_id: int):
    return {
        "items": [
            {
                "type": "mail",
                "title": "見積確認メールを受信",
                "body": "条件面の確認依頼を受信",
                "time": "3日前",
            },
            {
                "type": "ai",
                "title": "AI分析",
                "body": "高利益かつ放置リスクあり。本日中の返信を推奨。",
                "time": "今日",
            },
            {
                "type": "sms",
                "title": "SMS確認候補",
                "body": "返信がない場合は短文SMSへ切り替え",
                "time": "今日 18:00",
            },
        ]
    }
