from app.providers.ai_provider import get_ai_provider


class RevenueService:
    def analyze(self, company_id: str, payload: dict):
        if not company_id:
            raise ValueError("company_id is required")

        ai = get_ai_provider()
        judgement = ai.judge_sales_opportunity(payload)

        return {
            "company_id": company_id,
            "estimated_profit": payload.get("estimated_profit", 0),
            "judgement": judgement,
        }
